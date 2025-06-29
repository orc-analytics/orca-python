class BaseOrcaException(Exception):
    """Base exception for the Python Orca client"""


class InvalidAlgorithmArgument(BaseOrcaException):
    """Raised when an argument to `@algorithm` is not correct"""


class InvalidAlgorithmReturnType(BaseOrcaException):
    """Raised when the return type of an algorithm is not valid"""


class InvalidWindowArgument(BaseOrcaException):
    """Raised when an argument to the Window class is not valid"""


class InvalidDependency(BaseOrcaException):
    """Raised when a dependency is invalid"""


class MissingDependency(BaseOrcaException):
    """Raised when a dependency is missing"""
