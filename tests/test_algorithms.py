import random

import pytest

from orca_python import algorithm
from orca_python.main import _algorithmsSingleton
from orca_python.exceptions import InvalidDependency, InvalidAlgorithmArgument


def test_algorithm_arg_parsing_fails():
    """Arguments to the algorithm decorator are parsed as expected."""
    _algorithmsSingleton._flush()

    with pytest.raises(InvalidAlgorithmArgument):

        @algorithm("TestAlgorithm", "1.0.0+abcd", "WindowA", "1.0.0")
        def test_algorithm():
            return None

    with pytest.raises(InvalidAlgorithmArgument):

        @algorithm("Test_Algorithm", "1.0.0", "WindowA", "1.0.0")
        def test_algorithm():
            return None


def test_algo_arg_parsing_suceeds():
    """Algorithm arg parsing succeeds."""
    _algorithmsSingleton._flush()

    @algorithm("TestAlgorithm", "1.0.0", "WindowA", "1.0.0")
    def test_algorithm():
        return None

    assert _algorithmsSingleton._has_algorithm("TestAlgorithm_1.0.0")


def test_valid_dependency():
    """Valid dependencies are successfully managed"""
    _algorithmsSingleton._flush()
    algo_1_result = random.random()
    algo_2_result = random.random()

    @algorithm("TestAlgorithm", "1.0.0", "WindowA", "1.0.0")
    def test_algorithm():
        return algo_1_result

    assert _algorithmsSingleton._has_algorithm("TestAlgorithm_1.0.0")
    assert _algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"]() == algo_1_result

    @algorithm("TestAlgorithm", "1.2.0", "WindowB", "1.0.0")
    def test_algorithm_2():
        return algo_2_result

    @algorithm(
        "NewAlgorithm",
        "1.0.0",
        "WindowA",
        depends_on=[test_algorithm, test_algorithm_2],
    )
    def test_algorithm_3():
        return None

    # confirm algorithm execution order.
    assert (
        _algorithmsSingleton._dependencies["NewAlgorithm_1.0.0"][0]() == algo_1_result
    )
    assert (
        _algorithmsSingleton._dependencies["NewAlgorithm_1.0.0"][1]() == algo_2_result
    )


def test_bad_dependency():
    """Dependencies are poorly managed"""
    _algorithmsSingleton._flush()

    # invalid dependency as not an algorithm
    def undecorated():
        return None

    with pytest.raises(InvalidDependency):

        @algorithm(
            "NewAlgorithm", "1.0.0", "WindowA", "1.0.0", depends_on=[undecorated]
        )
        def new_algorithm():
            return None
