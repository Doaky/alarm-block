from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List

from backend.alarm import Alarm
from backend.alarm_manager import AlarmManager
from backend.alarm_scheduler import AlarmScheduler
from backend.settings_manager import SettingsManager
from backend.pi_handler import PiHandler, play_alarm, stop_alarm

app = FastAPI()

settings_manager = SettingsManager()
alarm_manager = AlarmManager(settings_manager)
pi_handler = PiHandler()

# Serve React frontend
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="frontend")

### ---- ALARM MANAGEMENT ---- ###
@app.get("/alarms")
def get_alarms():
    """Returns all stored alarms."""
    return alarm_manager.get_alarms()

@app.put("/set-alarm")
def set_alarm(alarm_data: dict):
    """Creates or updates an alarm using an Alarm object."""
    try:
        alarm_obj = Alarm(
            id=alarm_data.id,
            hour=alarm_data.hour,
            minute=alarm_data.minute,
            days=alarm_data.days,
            is_primary_schedule=alarm_data.is_primary_schedule,
            active=alarm_data.active,
        )
        
        alarm_manager.set_alarm(alarm_obj)
        return {"message": "Alarm set successfully"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {e.args[0]}")

@app.delete("/alarms")
def remove_alarms(alarm_ids: List[str]):
    """Deletes alarms by their IDs."""
    removed_all = alarm_manager.remove_alarms(alarm_ids)
    if not removed_all:
        return {"message": "Some alarms were not found", "success": False}
    return {"message": "Alarms removed successfully", "success": True}


### ---- ALARM TRIGGERING ---- ###
@app.post("/stop-alarm")
def stop():
    """Stops the currently playing alarm."""
    stop_alarm()
    return {"message": "Alarm stopped"}

@app.post("/play-alarm")
def play():
    """Plays an alarm."""
    play_alarm()
    return {"message": "Alarm playing"}


### ---- SCHEDULE & GLOBAL STATUS MANAGEMENT ---- ###
@app.get("/get_schedule")
def get_schedule():
    """Returns is primary schedule."""
    return {"is_primary_schedule": settings_manager.get_is_primary_schedule()}

@app.post("/set_schedule")
def set_schedule(is_primary: bool):
    """Updates primary schedule status."""
    try:
        settings_manager.set_is_primary_schedule(is_primary)
        return {"message": f"Schedule set to primary: {is_primary}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_global_status")
def get_global_status():
    """Returns is global."""
    return {"is_global_on": settings_manager.get_is_global_on()}

@app.post("/set_global_status")
def set_global_status(is_global_on: bool):
    """Enables or disables all alarms."""
    settings_manager.set_is_global_on(is_global_on)
    return {"message": f"Global status set to {is_global_on}"}


### ---- SERVER STARTUP ---- ###
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
