import schedule
import time
from orca_python import EmitWindow, Window

def emitWindow():
    now = int(time.time())
    window = Window(time_from=now - 30, time_to=now, name="Every30Second", version="1.0.0", origin="Example")
    EmitWindow(window)

schedule.every(30).seconds.do(emitWindow)

if __name__=="__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
