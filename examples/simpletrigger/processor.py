import time
from typing import Dict

from orca_python import Processor, WindowType

proc = Processor("ml")

Every30Second = WindowType(
    name="Every30Second", version="1.0.0", description="Triggers every 30 seconds"
)


@proc.algorithm("MyAlgo", "1.0.0", Every30Second)
def my_algorithm() -> Dict[str, int]:
    time.sleep(5)
    return {"result": 42}


if __name__ == "__main__":
    proc.Register()
    proc.Start()
