################
Flask-CuttlePool
################

Flask-CuttlePool provides a convenient interface for using `Cuttle Pool
<https://github.com/smitchell556/cuttlepool>`_ with Flask.

How-to Guide
============

If you haven't read the `How-to Guide
<https://github.com/smitchell556/cuttlepool#how-to-guide>`_ for CuttlePool, you
really should before going any further.

``FlaskCuttlePool`` objects accept the same arguments as ``CuttlePool``
objects, as well as a Flask ``app`` object. Assume we have the following
imports and ``app`` object. ::

  import sqlite3

  from flask import Flask
  from flask_cuttlepool import FlaskCuttlePool
  

  app = Flask(__name__)


There are two ways to set up a pool object. On pool initialization ::

  pool = FlaskCuttlePool(sqlite3.connect, app=app, database='ricks_lab')

or using ``init_app()`` explicitly ::

  pool = FlaskCuttlePool(sqlite3.connect)
  pool.init_app(app)

Any configuration keys that start with ``CUTTLEPOOL_`` will be converted to a
key value pair. If the key already exists in the initial arguments passed to
the ``__init__()`` method, those will be superceded by the value on
``app.config``. For example ::

  pool = FlaskCuttlePool(sqlite3.connect, database='ricks_lab')
  app.config['CUTTLEPOOL_DATABASE'] = 'citadel_of_ricks'
  pool.init_app(app)

will result in the connection pool associated with that ``app`` object
connecting to ``'citadel_of_ricks'`` instead of ``'ricks_lab'``. Every key
value pair on ``app.config`` of the form ``app.config['CUTTLEPOOL_KEY'] =
value`` is passed to the pool constructor as ``key=value`` where ``key`` is
lowercase.

Now the pool can be used as normal. Any calls to ``get_connection()`` will
return a connection in the same manner a ``CuttlePool`` object would.

To make things more convenient, the ``connection`` getter will store a
connection on the application context and reuse that connection whenever the
``connection`` getter is called again. When the application context is torn
down, the connection will be returned to the pool. Therefore, there is no need
to call ``close()`` on a connection retrieved from the ``connection`` getter,
but it's ok if ``close()`` is called. Connections retrieved with
``get_connection()`` should be explicitly closed.

The convenience method ``cursor()`` will return a ``Cursor`` instance for the
connection stored on the application context.

FAQ
===

These questions are related to Flask-CuttlePool only, check the `FAQ
<https://github.com/smitchell556/cuttlepool#faq>`_ for CuttlePool if you don't
find your answers here.

How do I install it?
--------------------

``pip install flask-cuttlepool``

What is an application contexts?
--------------------------------

This is a Flask extension, so it is meant to be used in the context of a Flask
application. See `here <http://http://flask.pocoo.org/docs/appcontext/>`_ to
learn about Flask's application context.

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
