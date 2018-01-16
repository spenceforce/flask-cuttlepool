# -*- coding: utf-8 -*-
"""
Flask extension for CuttlePool. This is based in large part on the SQLite3
example given in the `Flask Extension Development
<http://flask.pocoo.org/docs/0.12/extensiondev>`_ documentation.

:license: BSD 3-clause, see LICENSE for details.
"""

__version__ = '0.1.0'


from cuttlepool import CuttlePool, CuttlePoolError

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class FlaskCuttlePool(CuttlePool):

    """
    An SQL connection pool for Flask applications.

    :param func connect: The ``connect`` function of the chosen sql driver.
    :param int capacity: Max number of connections in pool. Defaults to ``5``.
    :param int timeout: Time in seconds to wait for connection. Defaults to
                        ``None``.
    :param int overflow: The number of extra connections that can be made if
                         the pool is exhausted. Defaults to ``1``.
    :param Flask app: A Flask ``app`` object. Defaults to ``None``.
    :param \**kwargs: Connection arguments for the underlying database
                      connector.
    """

    def __init__(self, connect, capacity=5, overflow=1,
                 timeout=None, app=None, **kwargs):
        self._app_set = False
        super(FlaskCuttlePool, self)\
            .__init__(connect, capacity, overflow, timeout, **kwargs)

        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        """
        Configures the connection pool and attaches a teardown handler to the
        ``app`` object.

        :param Flask app: A Flask ``app`` object.
        :param \**kwargs: Connection arguments for the underlying database
                          connector. These will overwrite any key value pairs
                          with the same key that were passed to
                          ``FlaskCuttlePool`` on instantiation. This is where
                          any arguments from ``app.config`` should be passed to
                          to ``FlaskCuttlePool``.

        :Example:

        # pool will connect to rons_house.
        pool = FlaskCuttlePool(sqlite3.connect, database='rons_house')
        app = Flask(__name__)
        app.config['SQLITE3_DB'] = 'steakhouse'
        # pool will connect to steakhouse instead.
        pool.init_app(app, database=app.config['SQLITE3_DB'])
        """
        self._app_set = True
        self._connection_arguments.update(**kwargs)

        # Use the newstyle teardown_appcontext if it's available,
        # otherwise fall back to the request context.
        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self.teardown)
        else:
            app.teardown_request(self.teardown)

    def get_connection(self):
        """
        Gets a ``PoolConnection`` object. Saves the connection on the
        application context for subsequent calls.

        :raise AppUninitializedError: If trying to get a connection before
                                      calling ``init_app()``.
        """
        if not self._app_set:
            raise AppUninitializedError('init_app() with an app object before using the pool')

        ctx = stack.top

        if ctx is not None:
            if (not hasattr(ctx, 'cuttlepool_connection') or
                    ctx.cuttlepool_connection._connection is None):
                ctx.cuttlepool_connection = super(FlaskCuttlePool, self).get_connection()

            else:
                if not self.ping(ctx.cuttlepool_connection):
                    ctx.cuttlepool_connection.close()
                    del ctx.cuttlepool_connection
                    ctx.cuttlepool_connection = self.get_connection()

            return ctx.cuttlepool_connection

    def get_fresh_connection(self):
        """
        Gets a ``PoolConnection`` object directly from the pool. Does not try
        to retrieve from the application context, nor does it store the
        connection on the application context.
        :raise AppUninitializedError: If trying to get a connection before
                                      calling ``init_app()``.
        """
        if not self._app_set:
            raise AppUninitializedError('init_app() with an app object before using the pool')

        return super(FlaskCuttlePool, self).get_connection()

    def teardown(self, exception):
        """
        Calls the ``PoolConnection``'s ``close()`` method, which puts the
        connection back in the pool.
        """
        ctx = stack.top

        if hasattr(ctx, 'cuttlepool_connection'):
            ctx.cuttlepool_connection.close()


class FlaskCuttlePoolError(CuttlePoolError):

    """Base class for exceptions in this module."""


class AppUninitializedError(FlaskCuttlePoolError):

    """Exception raised when the pool is used before calling ``init_app()``."""
