# -*- coding: utf-8 -*-
"""Tests for Flask-CuttlePool."""
import pytest
from flask import Flask

# Find the stack on which we want to store the database connection.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

import mocksql
from flask_cuttlepool import (_CAPACITY, _OVERFLOW, _TIMEOUT, CuttlePool,
                              FlaskCuttlePool, PoolConnection)


@pytest.fixture
def user():
    return 'paul_hollywood'


@pytest.fixture
def password():
    return 'bread_is_the_best'


@pytest.fixture
def host():
    return 'an_ip_address_in_england'


@pytest.fixture
def user2():
    return 'marry_berry'


@pytest.fixture
def password2():
    return 'cake_and_margaritas'


@pytest.fixture
def host2():
    return 'another_ip_address_in_england'


def create_app(u, p, h):
    app = Flask(__name__)
    app.testing = True
    app.config.update(
        CUTTLEPOOL_USER=u,
        CUTTLEPOOL_PASSWORD=p,
        CUTTLEPOOL_HOST=h
    )
    return app


@pytest.fixture
def app(user, password, host):
    """A Flask ``app`` instance."""
    return create_app(user, password, host)


@pytest.fixture
def app2(user2, password2, host2):
    """A Flask ``app`` instance."""
    return create_app(user2, password2, host2)


@pytest.fixture
def pool_no_app():
    """Pool with no app."""
    return FlaskCuttlePool(mocksql.connect)


@pytest.fixture(params=[1, 2])
def pool_one(request, app):
    """Pool initialized with one app."""
    if request.param == 1:
        # Pool initialized with app in __init__() only.
        pool = FlaskCuttlePool(mocksql.connect, app=app)
    elif request.param == 2:
        # Pool initialized with app in init_app() only.
        pool = FlaskCuttlePool(mocksql.connect)
        pool.init_app(app)
    return pool


@pytest.fixture(params=[1, 2])
def pool_two(request, app, app2):
    """Pool initialized with two apps."""
    if request.param == 1:
        # Pool initialized with one app in __init__() and one app in
        # init_app().
        pool = FlaskCuttlePool(mocksql.connect, app=app)
        pool.init_app(app2)
    elif request.param == 2:
        # Pool initialized with two apps in init_app() only.
        pool = FlaskCuttlePool(mocksql.connect)
        pool.init_app(app)
        pool.init_app(app2)
    return pool


def test_init_no_app(user, password, host):
    """Test FlaskCuttlePool instantiates properly without an app object."""
    pool = FlaskCuttlePool(mocksql.connect, user=user, password=password, host=host)
    assert isinstance(pool, FlaskCuttlePool)
    assert pool._cuttlepool_kwargs['capacity'] == _CAPACITY
    assert pool._cuttlepool_kwargs['overflow'] == _OVERFLOW
    assert pool._cuttlepool_kwargs['timeout'] == _TIMEOUT
    assert pool._cuttlepool_kwargs['user'] == user
    assert pool._cuttlepool_kwargs['password'] == password
    assert pool._cuttlepool_kwargs['host'] == host


def test_init_with_app(app, pool_one, user, password, host):
    """Test FlaskCuttlePool instantiates properly with an app object."""
    assert isinstance(pool_one, FlaskCuttlePool)
    assert pool_one._cuttlepool_kwargs['capacity'] == _CAPACITY
    assert pool_one._cuttlepool_kwargs['overflow'] == _OVERFLOW
    assert pool_one._cuttlepool_kwargs['timeout'] == _TIMEOUT
    assert app in pool_one._apps


def test_get_app_no_init(app):
    """
    Tests the ``app`` is returned when ``app`` is only passed to pool
    ``__init__()``.
    """
    pool = FlaskCuttlePool(mocksql.connect, app=app)
    # Test in app context.
    with app.app_context():
        assert pool._get_app() is app
    # Test outside app context.
    assert pool._get_app() is app


def test_get_app_multiple(pool_two, app, app2):
    """Tests the correct ``app`` is returned."""
    with app.app_context():
        assert pool_two._get_app() is app
    with app2.app_context():
        assert pool_two._get_app() is app2


def test_get_app_no_app():
    """Tests an error is raised when there is no app."""
    pool = FlaskCuttlePool(mocksql.connect)
    with pytest.raises(RuntimeError):
        pool._get_app()


def test_get_pool(pool_two, app, app2):
    """Tests the proper pool is retreived."""
    with app.app_context():
        pool = pool_two.get_pool()

    # Ensure same pool is returned again.
    with app.app_context():
        assert pool is pool_two.get_pool()

    # Ensure different pool for different app.
    with app2.app_context():
        assert pool is not pool_two.get_pool()


def test_get_pool_different_apps_and_pools(app, app2):
    """
    Tests that connection pools are stored correctly for each pool, app pair.
    """
    pool1 = FlaskCuttlePool(mocksql.connect, app=app)
    pool2 = FlaskCuttlePool(mocksql.connect, app=app2)

    with app2.app_context():
        with pytest.raises(RuntimeError):
            p = pool1.get_pool()


def test_make_pool(app, user, password, host):
    """Tests _make_pool method."""
    pool = FlaskCuttlePool(mocksql.connect)
    p = pool._make_pool(app)

    assert isinstance(p, CuttlePool)

    con_args = p.connection_arguments

    assert con_args['user'] == user
    assert con_args['password'] == password
    assert con_args['host'] == host


def test_get_connection(app, pool_one):
    """Test get_connection saves the connection on the stack."""
    with app.app_context():
        con = pool_one.get_connection()
        assert isinstance(con, PoolConnection)


def test_connection_app_ctx(app, pool_one):
    """Tests the same connection is retrieved from the stack."""
    with app.app_context():
        con1 = pool_one.connection
        assert hasattr(stack.top, 'cuttlepool_connection')
        con2 = pool_one.connection

        assert con1 is con2


def test_connection_multiple_app_ctx(app, pool_one):
    """
    Tests connection property saves a different connection to coexisting app
    contexts.
    """
    with app.app_context():
        con1 = pool_one.connection

        with app.app_context():
            con2 = pool_one.connection
            assert con1 is not con2

        assert con1 is pool_one.connection


def test_cursor(app, pool_one):
    """Tests a cursor is returned."""
    with app.app_context():
        cur = pool_one.cursor()
        assert isinstance(cur, mocksql.MockCursor)
