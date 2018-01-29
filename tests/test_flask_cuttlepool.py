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
from flask_cuttlepool import (_CAPACITY, _OVERFLOW, _TIMEOUT, FlaskCuttlePool,
                              PoolConnection, AppUninitializedError)


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
def app(user, password, host):
    """A Flask ``app`` instance."""
    app = Flask(__name__)
    app.testing = True
    app.config.update(
        CUTTLEPOOL_USER=user,
        CUTTLEPOOL_PASSWORD=password,
        CUTTLEPOOL_HOST=host
    )
    return app


@pytest.fixture
def pool_no_app():
    return FlaskCuttlePool(mocksql.connect)


@pytest.fixture
def pool(app):
    pool = FlaskCuttlePool(mocksql.connect, app=app)
    return pool


def test_init_no_app(user, password, host):
    """Test FlaskCuttlePool instantiates properly without an app object."""
    pool = FlaskCuttlePool(mocksql.connect, user=user, password=password, host=host)
    assert isinstance(pool, FlaskCuttlePool)
    assert pool._capacity == _CAPACITY
    assert pool._overflow == _OVERFLOW
    assert pool._timeout == _TIMEOUT

    con_args = pool._connection_arguments

    assert con_args['user'] == user
    assert con_args['password'] == password
    assert con_args['host'] == host


def test_init_with_app(app, user, password, host):
    """Test FlaskCuttlePool instantiates properly with an app object."""
    pool = FlaskCuttlePool(mocksql.connect, app=app, user=user, password=password, host=host)
    assert isinstance(pool, FlaskCuttlePool)
    assert pool._capacity == _CAPACITY
    assert pool._overflow == _OVERFLOW
    assert pool._timeout == _TIMEOUT

    con_args = pool._connection_arguments

    assert con_args['user'] == user
    assert con_args['password'] == password
    assert con_args['host'] == host


def test_init_app(app, pool_no_app, user, password, host):
    """Test init_app method."""
    pool_no_app.init_app(app)
    pool = pool_no_app          # since the pool has been initialized, this name fits better.

    con_args = pool._connection_arguments

    assert con_args['user'] == user
    assert con_args['password'] == password
    assert con_args['host'] == host


def test_get_connection(app, pool):
    """Test get_connection saves the connection on the stack."""
    with app.app_context():
        assert not hasattr(stack.top, 'cuttlepool_connection')
        con = pool.get_connection()
        assert isinstance(con, PoolConnection)

    assert pool._pool.qsize() == 1


def test_get_connection_app_ctx(app, pool):
    """Tests the connection is saved on the application context."""
    with app.app_context():
        con1 = pool.get_connection()
        assert hasattr(stack.top, 'cuttlepool_connection')
        con2 = pool.get_connection()

        assert con1 is con2


def test_get_connection_multiple_app_ctx(app, pool):
    """
    Tests get_connection saves a different connection to coexisting app
    contexts.
    """
    with app.app_context():
        con1 = pool.get_connection()

        with app.app_context():
            con2 = pool.get_connection()
            assert con1 is not con2

        assert con1 is pool.get_connection()


def test_get_connection_error(pool_no_app):
    """Test get_connection throws an error when called before init_app."""
    with pytest.raises(AppUninitializedError):
        pool_no_app.get_connection()


def test_get_connection_after_explicit_close(app, pool):
    """Test get_connection after an explicit close of the connection."""
    with app.app_context():
        con = pool.get_connection()
        con.close()
        con = pool.get_connection()
        assert isinstance(con, PoolConnection)


def test_get_fresh_connection(app, pool):
    """
    Tests a different connection than what exists on the application context
    stack is returned.
    """
    with app.app_context():
        con1 = pool.get_connection()
        con2 = pool.get_fresh_connection()
        assert isinstance(con2, PoolConnection)
        assert con1 is not con2


def test_get_fresh_connection_error(pool_no_app):
    """Test get_fresh_connection throws an error when called before init_app."""
    with pytest.raises(AppUninitializedError):
        pool_no_app.get_fresh_connection()
