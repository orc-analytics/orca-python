import random

import pytest

from orca_python import Processor
from orca_python.exceptions import InvalidDependency, InvalidAlgorithmArgument

proc = Processor("ml")


def test_algorithm_arg_parsing_fails():
    """Arguments to the algorithm decorator are parsed as expected."""
    proc._algorithmsSingleton._flush()

    with pytest.raises(InvalidAlgorithmArgument):

        @proc.algorithm("TestAlgorithm", "1.0.0+abcd", "WindowA", "1.0.0")
        def test_algorithm():
            return None

    with pytest.raises(InvalidAlgorithmArgument):

        @proc.algorithm("Test_Algorithm", "1.0.0", "WindowA", "1.0.0")
        def test_algorithm():
            return None


def test_algo_arg_parsing_suceeds():
    """Algorithm arg parsing succeeds."""
    proc._algorithmsSingleton._flush()

    @proc.algorithm("TestAlgorithm", "1.0.0", "WindowA", "1.0.0")
    def test_algorithm():
        return None

    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms


def test_valid_dependency():
    """Valid dependencies are successfully managed"""
    proc._algorithmsSingleton._flush()
    algo_1_result = random.random()
    algo_2_result = random.random()

    @proc.algorithm("TestAlgorithm", "1.0.0", "WindowA", "1.0.0")
    def test_algorithm():
        return algo_1_result

    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms
    assert (
        proc._algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"].exec_fn()
        == algo_1_result
    )

    @proc.algorithm("TestAlgorithm", "1.2.0", "WindowB", "1.0.0")
    def test_algorithm_2():
        return algo_2_result

    @proc.algorithm(
        "NewAlgorithm",
        "1.0.0",
        "WindowA",
        "1.0.0",
        depends_on=[test_algorithm, test_algorithm_2],
    )
    def test_algorithm_3():
        return None

    # confirm algorithm execution order.
    assert (
        proc._algorithmsSingleton._dependencyFns["NewAlgorithm_1.0.0"][0]() == algo_1_result
    )
    assert (
        proc._algorithmsSingleton._dependencyFns["NewAlgorithm_1.0.0"][1]() == algo_2_result
    )


def test_bad_dependency():
    """Dependencies are poorly managed"""
    proc._algorithmsSingleton._flush()

    # invalid dependency as not an algorithm
    def undecorated():
        return None

    with pytest.raises(InvalidDependency):

        @proc.algorithm(
            "NewAlgorithm", "1.0.0", "WindowA", "1.0.0", depends_on=[undecorated]
        )
        def new_algorithm():
            return None

@pytest.mark.live
def test_registration_works():
    """Registration of the orca processor just works"""
    proc._algorithmsSingleton._flush()
    algo_1_result = random.random()
    algo_2_result = random.random()

    @proc.algorithm("TestAlgorithm", "1.0.0", "WindowA", "1.0.0")
    def test_algorithm():
        return algo_1_result

    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms
    assert (
        proc._algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"].exec_fn()
        == algo_1_result
    )

    @proc.algorithm("TestAlgorithm", "1.2.0", "WindowB", "1.0.0")
    def test_algorithm_2():
        return algo_2_result

    @proc.algorithm(
        "NewAlgorithm",
        "1.0.0",
        "WindowA",
        "1.0.0",
        depends_on=[test_algorithm, test_algorithm_2],
    )
    def test_algorithm_3():
        return None

    proc.Register()
