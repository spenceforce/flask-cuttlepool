# -*- coding: utf-8 -*-
"""
A mock database driver module.
"""


class MockConnection(object):
    """
    A mock Connection object.

    :param \**kwargs: Accepts anything.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

        # Used to determine if the connection is "open" or not.
        self.open = True

    def close(self):
        """
        "Closes" the connection.
        """
        self.open = False

    def commit(self):
        """
        "Commits" the transaction.
        """
        return MockCommit()

    def cursor(self, cursorclass=None, **kwargs):
        """
        Returns a mock Cursor object.

        :param \**kwargs: Accepts anything.
        """
        if cursorclass is None:
            cursorclass = MockCursor
        return cursorclass(self)


class MockCursor(object):
    """
    A mock Cursor object.

    :param MockConnection connection: A MockConnection object.
    """

    def __init__(self, connection):
        self.connection = connection

    def close(self):
        """
        "Closes" the cursor.
        """
        self.connection = None

    def execute(self, query, *args):
        """
        "Executes" a query.
        """
        pass


class MockCommit(object):
    """
    A mock Commit object. Strictly used for testing methods involving commits.
    """
    def __eq__(self, other):
        return type(self) == type(other)


def connect(**kwargs):
    """
    Returns a mock Connection object.

    :param \**kwargs: Accepts anything, which is passed to the Connection
                      object.
    """
    return MockConnection(**kwargs)
