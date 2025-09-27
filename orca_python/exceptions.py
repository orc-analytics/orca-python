class BaseOrcaException(Exception):
    """Base exception for the Python Orca client"""


class InvalidAlgorithmArgument(BaseOrcaException):
    """Raised when an argument to `@algorithm` is not correct"""


class InvalidAlgorithmReturnType(BaseOrcaException):
    """Raised when the return type of an algorithm is not valid"""


class InvalidWindowArgument(BaseOrcaException):
    """Raised when an argument to the Window class is not valid"""


class InvalidMetadataFieldArgument(BaseOrcaException):
    """Raised when an argument to a metadata field is not valid"""


class InvalidDependency(BaseOrcaException):
    """Raised when a dependency is invalid"""


class MissingEnvVar(BaseOrcaException):
    """Raised when an environment variable is missing"""


class BadEnvVar(BaseOrcaException):
    """Raised when an environment variable is poorly defined"""
