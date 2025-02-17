from orca_client import algorithm, SingletonAlgorithms
import pytest

def test_algorithm_arg_parsing():
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

    assert "TestAlgorithm_1.0.0" in SingletonAlgorithms

def test_dependencies():

    @algorithm("TestAlgorithm", "1.0.0")
    def test_algorithm():
        return None

    assert "TestAlgorithm_1.0.0" in SingletonAlgorithms
    assert SingletonAlgorithms["TestAlgorithm_1.0.0"] == None
    
    # valid dependency
    @algorithm("TestAlgorithm2", "1.0.0")
    def test_algorithm_2():
        return None

    @algorithm("TestAlgorithm", "1.0.0", depends_on=[test_algorithm_2])
    def test_algorithm_1():
        return None


