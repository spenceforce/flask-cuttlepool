# -*- coding: utf-8 -*-
"""
Flask extension for CuttlePool. This extension is inspired by the SQLite3
example given in the `Flask Extension Development
<http://flask.pocoo.org/docs/0.12/extensiondev>`_ documentation,
`Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org>`_, and `Flask-Login
<https://flask-login.readthedocs.io>`_.

:license: BSD 3-clause, see LICENSE for details.
"""

__version__ = '0.2.0'


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


def cuttlepool_factory(ping_fn, normalize_fn):
    """
    Creates a CuttlePool class.

    :param ping_fn: A ping function to be called by the ping method.
    :param normalize_fn: A normalize_connection function to be called by the
        normalize_connection method.
    """
    class SQLPool(CuttlePool):
        def ping(self, connection):
            if ping_fn is not None:
                return ping_fn(connection)
            return super(SQLPool, self).ping(connection)

        def normalize_connection(self, connection):
            if normalize_fn is not None:
                normalize_fn(connection)
            else:
                super(SQLPool, self).normalize_connection(connection)

    return SQLPool


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
        self._apps = []
        self._cuttlepool_kwargs = kwargs
        self._cuttlepool_kwargs.update(capacity=capacity,
                                       overflow=overflow,
                                       timeout=timeout)

        self._ping = self._normalize = self._CuttlePool = None
        self._lock = RLock()    # Necessary for multithreaded apps.

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Attaches a teardown handler to the ``app`` object. All configuration
        options on ``app.config`` of the form ``CUTTLEPOOL_<KEY>`` will be
        used as connection arguments for the underlying driver. ``<KEY>`` will
        be converted to lowercase such that
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
        self._apps.append(app)
        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context.
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        if hasattr(app.extensions, 'cuttlepool'):
            raise RuntimeError('A pool has already been attached to this app.')

        app.extensions['cuttlepool'] = None

    def _get_app(self):
        """
        Looks up the current application or the default passed to
        ``__init__()``
        """
        if current_app:
            app = current_app._get_current_object()
        elif self._app is not None:
            app = self._app
        else:
            raise RuntimeError('No application found.')

        if app not in self._apps:
            raise RuntimeError('This FlaskCuttlePool instance does not have '
                               'access to the current app. Initialize the app '
                               'on the instance with init_app().')

        return app

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

        if self._CuttlePool is None:
            self._CuttlePool = cuttlepool_factory(self._ping, self._normalize)

        return self._CuttlePool(self._connect, **kwargs)

    def cursor(self):
        """
        Gets a cursor from the connection on the appplication context. It is
        the callers responsibility to close the cursor.
        """
        return self.connection.cursor()

    def get_connection(self):
        """
        Gets a ``PoolConnection`` object. The caller of this method is
        responsible for calling the ``close()`` method on the
        ``PoolConnection`` object.
        """
        return self.get_pool().get_connection()

    def get_pool(self):
        """
        Gets the pool on the current application. Creates the pool is one
        doesn't exist.
        """
        app = self._get_app()

        with self._lock:
            pool = app.extensions['cuttlepool']

            if pool is None:
                pool = self._make_pool(app)
                app.extensions['cuttlepool'] = pool

            return pool

    def ping(self, fn):
        """
        Decorator for setting ``ping()`` method on connection pool objects. The
        function should accept one parameter, a connection object and it should
        check if the connection is still open. Returning ``True`` if it is,
        otherwise ``False``.

        :param fn: A function.
        """
        self._ping = fn

    def normalize_connection(self, fn):
        """
        Decorator for setting ``normalize_connection()`` method on connection
        pool objects. The function should accept one parameter, a connection
        object and it should normalize the state of the connection to ensure
        uniformity of connections being retrieved from the pool.

        :param fn: A function.
        """
        self._normalize = fn

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

            else:
                pool = self.get_pool()
                if not pool.ping(ctx.cuttlepool_connection):
                    ctx.cuttlepool_connection.close()
                    ctx.cuttlepool_connection = self.connection

            return ctx.cuttlepool_connection
