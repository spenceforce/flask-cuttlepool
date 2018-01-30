# -*- coding: utf-8 -*-
"""
Flask extension for CuttlePool. This extension is inspired by the SQLite3
example given in the `Flask Extension Development
<http://flask.pocoo.org/docs/0.12/extensiondev>`_ documentation and
`Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org>`_.

:license: BSD 3-clause, see LICENSE for details.
"""

__version__ = '0.2.0-dev'


from threading import RLock

from cuttlepool import CuttlePool, CuttlePoolError, PoolConnection
from flask import current_app

try:
    from cuttlepool import _CAPACITY, _OVERFLOW, _TIMEOUT
except ImportError:
    # Compatibility for cuttlepool-0.5.1
    from cuttlepool import (CAPACITY as _CAPACITY, OVERFLOW as _OVERFLOW,
                            TIMEOUT as _TIMEOUT)

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class FlaskCuttlePool(object):
    """
    An SQL connection pool for Flask applications.

    :param func connect: The ``connect`` function of the chosen sql driver.
    :param int capacity: Max number of connections in pool. Uses ``CuttlePool``
        default as default value.
    :param int timeout: Time in seconds to wait for connection. Uses
        ``CuttlePool`` default as default value.
    :param int overflow: The number of extra connections that can be made if
        the pool is exhausted. Uses ``CuttlePool`` default as default value.
    :param Flask app: A Flask ``app`` object. Defaults to ``None``.
    :param \**kwargs: Connection arguments for the underlying database
        connector.
    """

    def __init__(self, connect, capacity=_CAPACITY, overflow=_OVERFLOW,
                 timeout=_TIMEOUT, app=None, **kwargs):
        self._connect = connect
        self._app = app
        self._cuttlepool_kwargs = kwargs
        self._cuttlepool_kwargs.update(capacity=capacity,
                                       overflow=overflow,
                                       timeout=timeout)

        self._lock = RLock()    # Necessary for multithreaded apps.

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Attaches a connection pool and a teardown handler to the ``app``
        object. All configuration options on ``app.config`` of the form
        ``CUTTLEPOOL_<KEY>`` will be used as connection arguments for the
        underlying driver. ``<KEY>`` will be converted to lowercase such that
        ``app.config['CUTTLEPOOL_<KEY>'] = <value>`` will be passed to the
        connection driver as ``<key>=<value>``.

        :param Flask app: A Flask ``app`` object.

        :Example:

        # pool will connect to rons_house.
        pool = FlaskCuttlePool(sqlite3.connect, database='rons_house')
        app = Flask(__name__)
        app.config['CUTTLEPOOL_DATABASE'] = 'steakhouse'
        # pool will connect to steakhouse instead.
        pool.init_app(app)
        """
        self._attach_pool(app)
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context.
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def _attach_pool(self, app):
        """Attaches a pool to the ``app`` object."""
        with self._lock:
            if not hasattr(app, 'extensions'):
                app.extensions = {}

            if 'cuttlepool' not in app.extensions:
                # Attach self and CuttlePool instance to app object. self is
                # attached to ensure that a FlaskCuttlePool instance is not
                # retrieving CuttlePool instances from apps it shouldn't have
                # access to.
                app.extensions['cuttlepool'] = (self, self._make_pool(app))
            else:
                raise RuntimeError('A pool has already been attached to this app.')


    def _get_app(self):
        """
        Looks up the current application or the default passed to
        ``__init__()``
        """
        if current_app:
            return current_app._get_current_object()

        if self._app is not None:
            return self._app

        raise RuntimeError('No application found.')

    def _make_pool(self, app):
        """
        Make a CuttlePool instance.

        :param app: A Flask app.
        """
        prefix = 'CUTTLEPOOL_'
        kwargs = self._cuttlepool_kwargs.copy()

        kwargs.update(
            **{k[len(prefix):].lower(): v
               for k, v in app.config.items()
               if k.startswith(prefix)})

        return CuttlePool(self._connect, **kwargs)


    def cursor(self):
        """Gets a cursor from the connection on the appplication context."""
        return self.connection.cursor()

    def get_connection(self):
        """
        Gets a ``PoolConnection`` object. The caller of this method is
        responsible for calling the ``close()`` method on the
        ``PoolConnection`` object.
        """
        pool = self.get_pool()
        return pool.get_connection()

    def get_pool(self):
        """Gets the pool on the current application."""
        app = self._get_app()

        with self._lock:
            flask_cp, pool = app.extensions['cuttlepool']

            if flask_cp is not self:
                raise ValueError(('Attempting to retrieve connection pool '
                                  'from a different FlaskCuttlePool '
                                  'instance.'))

            return pool

    def teardown(self, exception):
        """
        Calls the ``PoolConnection``'s ``close()`` method, which puts the
        connection back in the pool.
        """
        ctx = stack.top

        if hasattr(ctx, 'cuttlepool_connection'):
            ctx.cuttlepool_connection.close()

    @property
    def connection(self):
        """
        Gets a ``PoolConnection`` object. Saves the connection on the
        application context for subsequent gets.

        If there is no application context, returns ``None``.
        """
        ctx = stack.top

        if ctx is not None:
            if (not hasattr(ctx, 'cuttlepool_connection') or
                    ctx.cuttlepool_connection._connection is None):
                ctx.cuttlepool_connection = self.get_connection()

            elif not self.get_pool().ping(ctx.cuttlepool_connection):
                ctx.cuttlepool_connection.close()
                ctx.cuttlepool_connection = self.connection

            return ctx.cuttlepool_connection
