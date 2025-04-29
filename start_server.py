
from orca_python import Processor
import random 

proc = Processor("ml_v2")

@proc.algorithm("AlgoA", "1.0.0", "WindowA", "1.0.0")
def test_algorithm():
    return random.random()

@proc.algorithm("AlgoB", "1.1.0", "WindowA", "1.0.0")
def test_algorithm_2():
    return random.random()

@proc.algorithm(
    "AlgoC",
    "1.0.0",
    "WindowA",
    "1.0.0",
    depends_on=[test_algorithm, test_algorithm_2],
)
def test_algorithm_3():
    return None



if __name__ == "__main__":
    proc.Register()
    proc.Start()
