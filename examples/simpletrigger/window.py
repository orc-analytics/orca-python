import time
import datetime as dt

import schedule
from processor import bus_id, trip_id

from orca_python import Window, EmitWindow


def emitWindow() -> None:
    now = dt.datetime.now()
    window = Window(
        time_from=now - dt.timedelta(seconds=30),
        time_to=now,
        name="Every30Second",
        version="1.0.0",
        origin="Example",
        metadata={bus_id.name: 1, trip_id.name: 2},
    )
    EmitWindow(window)


schedule.every(30).seconds.do(emitWindow)

if __name__ == "__main__":
    emitWindow()
    while True:
        schedule.run_pending()
        time.sleep(1)
