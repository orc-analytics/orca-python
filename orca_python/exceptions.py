class BaseOrcaException(Exception):
    """Base exception for the Python Orca client"""


class InvalidAlgorithmArgument(BaseOrcaException):
    """Raised when an argument to `@algorithm` is not correct"""


class InvalidDependency(BaseOrcaException):
    """Raised when a dependency is invalid"""


class MissingDependency(BaseOrcaException):
    """Raised when a dependency is missing"""
