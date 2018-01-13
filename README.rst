################
Flask-CuttlePool
################

Flask-CuttlePool provides a convenient interface for using `CuttlePool
<https://github.com/smitchell556/cuttlepool>`_ with Flask.

How-to Guide
============

If you haven't read the `How-to Guide
<https://github.com/smitchell556/cuttlepool#how-to-guide>`_ for CuttlePool, you
really should before going any further. ``FlaskCuttlePool``

``FlaskCuttlePool`` should be subclassed in the same way. The only difference in
use is how the pool is initialized and how connections are returned to the
pool. ``FlaskCuttlePool`` accepts retains all the same ``__init__()``
parameters as ``CuttlePool``. Assume we have the following pool class (and an
app object of course) ::

  import sqlite3

  from flask import Flask
  from flask_cuttlepool import FlaskCuttlePool
  
  class SQLitePool(FlaskCuttlePool):
       def normalize_connection(self, connection):
           connection.row_factory = None
       def ping(self, connection):
           try:
               rv = connection.execute('SELECT 1').fetchall()
               return (1,) in rv
           except sqlite3.Error:
               return False

  app = Flask(__name__)


There are two ways to set up a pool object. On pool initialization ::

  pool = SQLitePool(sqlite3.connect, app=app, database='ricks_lab')

or using ``init_app()`` explicitly ::

  pool = SQLitePool(sqlite3.connect, database='ricks_lab')
  pool.init_app(app)

``init_app()`` also accepts connection arguments for the underlying SQL driver.
So if the database name was stored in ``app.config`` and ``app`` wasn't
instantiated until after ``SQLitePool``, set up would look like this ::

  pool = SQLitePool(sqlite3.connect)
  ...  # additional set up code
  app = Flask(__name__)
  app.from_pyfile('config.cfg')
  pool.init_app(app, database=app.config['DATABASE'])

Now the pool can be used as normal. Any calls to ``get_connection()`` will
store the connection in the application context and the connection will be
returned to the pool when the application context is torn down. If a connection
is stored on the application context, calls to ``get_connection()`` will return
that connection. There is no need to call ``close()`` on the
``PoolConnection()`` object, although it's ok if the connection is explicitly
closed.

If for some reason, you do not want to store the connection on the application
context or you need multiple connections at the same time,
``get_fresh_connection()`` will get a connection from the pool and won't store
it on the application context. Any connection retrieved from
``get_fresh_connection()`` should be explicitly closed.

FAQ
===

These questions are related to Flask-CuttlePool only, check the `FAQ
<https://github.com/smitchell556/cuttlepool#faq>`_ for CuttlePool if you don't
find your answers here.

How do I install it?
--------------------

``pip install git+https://github.com/smitchell556/flask-cuttlepool.git``

Contributing
------------

It's highly recommended to develop in a virtualenv.

Fork the repository.

Clone the repository::

  git clone https://github.com/<your_username>/flask-cuttlepool.git

Install the package in editable mode::

  cd flask-cuttlepool
  pip install -e .[dev]

Now you're set. See the next section for running tests.

Running the tests
-----------------

Tests can be run with the command ``pytest``.

Where can I get help?
---------------------

If you haven't read the How-to guide above, please do that first. Otherwise,
check the `issue tracker
<https://github.com/smitchell556/flask-cuttlepool/issues>`_. Your issue may be
addressed there and if it isn't please file an issue :)
