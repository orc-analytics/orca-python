import time
from typing import Dict

from orca_python import Processor

proc = Processor("ml")


@proc.algorithm("MyAlgo", "1.0.0", "Every30Second", "1.0.0")
def my_algorithm() -> Dict[str, int]:
    time.sleep(5)
    return {"result": 42}


if __name__ == "__main__":
    proc.Register()
    proc.Start()
