import time

from orca_python import Processor, WindowType, StructResult, ExecutionParams

proc = Processor("ml")

Every30Second = WindowType(
    name="Every30Second", version="1.0.0", description="Triggers every 30 seconds"
)


@proc.algorithm("MyAlgo", "1.0.0", Every30Second)
def my_algorithm(params: ExecutionParams) -> StructResult:
    time.sleep(5)
    return StructResult({"result": 42})


if __name__ == "__main__":
    proc.Register()
    proc.Start()
