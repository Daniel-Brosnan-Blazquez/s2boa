"""
Errors definition for the ingestions module

Written by DEIMOS Space S.L. (dibb)

module eboa
"""
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class CentresConfigCannotBeRead(Error):
    """Exception raised when the centres configuration file cannot be read.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

class CentresConfigDoesNotPassSchema(Error):
    """Exception raised when the centres configuration does not pass the schema.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

