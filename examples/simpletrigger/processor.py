import time

from orca_python import (
    Processor,
    WindowType,
    StructResult,
    MetadataField,
    ExecutionParams,
)

proc = Processor("ml")

trip_id = MetadataField(name="trip_id", description="The unique ID of the trip")
bus_id = MetadataField(name="bus_id", description="The unique ID of the bus")

Every30Second = WindowType(
    name="Every30Second",
    version="1.0.0",
    description="Triggers every 30 seconds",
    metadataFields=[trip_id, bus_id],
)


@proc.algorithm("MyAlgo", "1.0.0", Every30Second)
def my_algorithm(params: ExecutionParams) -> StructResult:
    trip_id = params.window.metadata.get("trip_id", None)
    bus_id = params.window.metadata.get("bus_id", None)
    print(trip_id, bus_id)

    time.sleep(5)
    return StructResult({"result": 42})


if __name__ == "__main__":
    proc.Register()
    proc.Start()
