import pytest

from orca_client import algorithm
from orca_client.main import _algorithmsSingleton
from orca_client.exceptions import InvalidDependency


def test_algorithm_arg_parsing():
    """Arguments to the algorithm decorator are parsed as expected."""
    _algorithmsSingleton.flush()
    with pytest.raises(ValueError):

        @algorithm("TestAlgorithm", "1.0.0+abcd")
        def test_algorithm():
            return None

    with pytest.raises(ValueError):

        @algorithm("Test_Algorithm", "1.0.0")
        def test_algorithm():
            return None

    @algorithm("TestAlgorithm", "1.0.0")
    def test_algorithm():
        return None

    assert _algorithmsSingleton.has_algorithm("TestAlgorithm_1.0.0")


def test_dependencies():
    """Dependencies are properly managed"""
    _algorithmsSingleton.flush()
    random_number = 1234

    @algorithm("TestAlgorithm", "1.0.0")
    def test_algorithm():
        return random_number

    assert _algorithmsSingleton.has_algorithm("TestAlgorithm_1.0.0")
    assert _algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"]() == random_number

    # valid dependency
    @algorithm("TestAlgorithm2", "1.0.0")
    def test_algorithm_2():
        return None

    @algorithm("TestAlgorithm", "1.1.0", depends_on=[test_algorithm_2])
    def test_algorithm_1():
        return None

    # invalid dependency
    def undecorated():
        return None

    with pytest.raises(InvalidDependency):
        @algorithm("NewAlgorithm", "1.0.0", depends_on=[undecorated])
        def new_algorithm():
            return None
