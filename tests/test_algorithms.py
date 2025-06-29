import random

import pytest
import service_pb2 as pb
from google.protobuf import timestamp_pb2

from orca_python import (
    Processor,
    NoneResult,
    WindowType,
    ValueResult,
    ExecutionParams,
)
from orca_python.exceptions import InvalidDependency, InvalidAlgorithmArgument

proc = Processor("ml")


def test_algorithm_arg_parsing_fails():
    """Arguments to the algorithm decorator are parsed as expected."""
    proc._algorithmsSingleton._flush()

    with pytest.raises(InvalidAlgorithmArgument):

        @proc.algorithm("TestAlgorithm", "1.0.0+abcd", "WindowA", "1.0.0")
        def test_algorithm(params: ExecutionParams) -> NoneResult:
            return NoneResult()

    with pytest.raises(InvalidAlgorithmArgument):

        @proc.algorithm("Test_Algorithm", "1.0.0", "WindowA", "1.0.0")
        def test_algorithm(params: ExecutionParams) -> NoneResult:
            return NoneResult()


def test_algo_arg_parsing_suceeds():
    """Algorithm arg parsing succeeds."""
    proc._algorithmsSingleton._flush()
    WindowA = WindowType(name="TestAlgorithm", version="1.0.0", description="Test")

    @proc.algorithm("TestAlgorithm", "1.0.0", WindowA)
    def test_algorithm(params: ExecutionParams) -> NoneResult:
        return NoneResult()

    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms


def test_valid_dependency():
    """Valid dependencies are successfully managed"""
    proc._algorithmsSingleton._flush()
    algo_1_result = random.random()
    algo_2_result = random.random()

    WindowA = WindowType(name="WindowA", version="1.0.0", description="Test")

    @proc.algorithm("TestAlgorithm", "1.0.0", WindowA)
    def test_algorithm(params: ExecutionParams) -> ValueResult:
        return ValueResult(algo_1_result)

    _time_from = timestamp_pb2.Timestamp(seconds=0)
    _time_to = timestamp_pb2.Timestamp(seconds=1)
    window_pb = pb.Window(
        time_from=_time_from,
        time_to=_time_to,
        window_type_name=WindowA.name,
        window_type_version=WindowA.version,
        origin="test",
    )
    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms
    assert (
        proc._algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"]
        .exec_fn(params=ExecutionParams(window=window_pb))
        .value
        == algo_1_result
    )

    WindowA = WindowType(name="WindowA", version="1.0.0", description="Test")
    WindowB = WindowType(name="WindowB", version="1.0.0", description="Test")

    @proc.algorithm("TestAlgorithm", "1.2.0", WindowB)
    def test_algorithm_2(params: ExecutionParams) -> ValueResult:
        return ValueResult(algo_2_result)

    @proc.algorithm(
        "NewAlgorithm",
        "1.0.0",
        WindowA,
        depends_on=[test_algorithm, test_algorithm_2],
    )
    def test_algorithm_3(params: ExecutionParams) -> NoneResult:
        return NoneResult()

    # confirm algorithm execution order.
    assert (
        proc._algorithmsSingleton._dependencyFns["NewAlgorithm_1.0.0"][0](
            params=ExecutionParams(window=window_pb)
        ).value
        == algo_1_result
    )
    assert (
        proc._algorithmsSingleton._dependencyFns["NewAlgorithm_1.0.0"][1](
            params=ExecutionParams(window=window_pb)
        ).value
        == algo_2_result
    )


def test_bad_dependency():
    """Dependencies are poorly managed"""
    proc._algorithmsSingleton._flush()
    WindowA = WindowType(name="WindowA", version="1.0.0", description="Test")

    # invalid dependency as not an algorithm
    def undecorated():
        return None

    with pytest.raises(InvalidDependency):

        @proc.algorithm("NewAlgorithm", "1.0.0", WindowA, depends_on=[undecorated])
        def new_algorithm(params: ExecutionParams) -> NoneResult:
            return None


@pytest.mark.live
def test_registration_works():
    """Registration of the orca processor just works"""
    proc._algorithmsSingleton._flush()
    algo_1_result = random.random()
    algo_2_result = random.random()

    WindowA = WindowType("WindowA", "1.0.0", "Test")
    WindowB = WindowType("WindowB", "1.0.0", "Test")

    @proc.algorithm("TestAlgorithm", "1.0.0", WindowA)
    def test_algorithm(params: ExecutionParams) -> ValueResult:
        return ValueResult(algo_1_result)

    assert "TestAlgorithm_1.0.0" in proc._algorithmsSingleton._algorithms
    assert (
        proc._algorithmsSingleton._algorithms["TestAlgorithm_1.0.0"].exec_fn()
        == algo_1_result
    )

    @proc.algorithm("TestAlgorithm", "1.2.0", WindowB)
    def test_algorithm_2(params: ExecutionParams) -> ValueResult:
        return ValueResult(algo_2_result)

    @proc.algorithm(
        "NewAlgorithm",
        "1.0.0",
        WindowA,
        depends_on=[test_algorithm, test_algorithm_2],
    )
    def test_algorithm_3(params: ExecutionParams) -> NoneResult:
        return NoneResult()

    proc.Register()
