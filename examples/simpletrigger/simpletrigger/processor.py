import time

from orca_python import (
    Processor,
    WindowType,
    StructResult,
    MetadataField,
    ExecutionParams,
)

proc = Processor("ml")

# E.g. you have you have a fleet of busses, where every bus has a particular
# ID and runs a particular route
route_id = MetadataField(name="route_id", description="The unique ID of the route")
bus_id = MetadataField(name="bus_id", description="The unique ID of the bus")

Every30Second = WindowType(
    name="Every30Second",
    version="1.0.0",
    description="Triggers every 30 seconds",
    metadataFields=[route_id, bus_id],
)


@proc.algorithm("MyAlgo", "1.0.0", Every30Second)
def my_algorithm(params: ExecutionParams) -> StructResult:
    """A simple algorithms that does nothing interesting"""
    route_id = params.window.metadata.get("route_id", None)
    bus_id = params.window.metadata.get("bus_id", None)
    print(route_id, bus_id)

    time.sleep(5)
    return StructResult({"result": 42})


if __name__ == "__main__":
    proc.Register()
    proc.Start()
