from orca_python import Processor
import time
proc = Processor("ml")

@proc.algorithm("MyAlgo", "1.0.0", "Every30Second", "1.0.0")
def my_algorithm() -> dict:
    time.sleep(5)
    return {"result": 42}

if __name__=="__main__":
    proc.Register()
    proc.Start()
