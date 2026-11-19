"""
CampusShield - Campus Emergency Response Coordinator
FastAPI Backend with Real-Time WebSockets, Triage Engine & Scenario Simulator
"""
import asyncio
import json
import datetime
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    Incident, IncidentCreate, IncidentStatus, IncidentPriority,
    Responder, ResponderStatus, ResponderType, SafePoint,
    CampusLocation, Coordinates, AuditLog, BroadcastAlert
)
from app.data import (
    CAMPUS_CENTER, CAMPUS_LOCATIONS, SAFE_POINTS,
    DEFAULT_RESPONDERS, STANDARD_INSTRUCTIONS
)
from app.engine import (
    create_incident_record, calculate_distance_meters, select_best_responder
)
from app.simulator import SIMULATION_PRESETS


# In-Memory State Store
class SystemState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.incidents: Dict[str, Incident] = {}
        self.responders: Dict[str, Responder] = {
            r.id: r.model_copy(deep=True) for r in DEFAULT_RESPONDERS
        }
        self.locations: Dict[str, CampusLocation] = dict(CAMPUS_LOCATIONS)
        self.safepoints: Dict[str, SafePoint] = dict(SAFE_POINTS)
        self.broadcasts: List[BroadcastAlert] = []
        self.seq_num: int = 100
        self.active_simulation_tasks: Dict[str, asyncio.Task] = {}


state = SystemState()


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, event_type: str, data: dict):
        if not self.active_connections:
            return
        payload = json.dumps({"event": event_type, "data": data, "timestamp": datetime.datetime.now().isoformat()})
        dead_conns = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_conns.append(connection)
        for dead in dead_conns:
            self.active_connections.discard(dead)


manager = ConnectionManager()


# Background Task for Escalation Monitoring & Responder Trajectory Simulation
async def escalation_and_movement_worker():
    while True:
        try:
            await asyncio.sleep(1.0)
            now_iso = datetime.datetime.now().isoformat()
            state_changed = False

            # 1. Escalation check on active incidents
            for inc_id, inc in list(state.incidents.items()):
                if inc.status == IncidentStatus.REPORTED:
                    inc.seconds_elapsed += 1
                    # Escalation Level 1: at 15 seconds
                    if inc.seconds_elapsed >= 15 and inc.escalation_level < 1:
                        inc.escalated = True
                        inc.escalation_level = 1
                        inc.logs.append(AuditLog(
                            timestamp=now_iso,
                            event="ESCALATION_L1",
                            details="No acknowledgment after 15s. Level 1 reminder buzzer sent to primary responder.",
                            actor="CampusShield Auto-Escalation Engine"
                        ))
                        state_changed = True
                        await manager.broadcast("incident_escalated", {"incident": inc.model_dump(), "level": 1})

                    # Escalation Level 2: at 30 seconds
                    elif inc.seconds_elapsed >= 30 and inc.escalation_level < 2:
                        inc.escalation_level = 2
                        inc.logs.append(AuditLog(
                            timestamp=now_iso,
                            event="ESCALATION_L2",
                            details="CRITICAL SLA BREACH (30s unacknowledged). Re-routing to secondary responder and alerting Chief Security Officer.",
                            actor="CampusShield Auto-Escalation Engine"
                        ))
                        # Assign secondary backup responder if available
                        backup_resp, _, _ = select_best_responder(
                            inc.incident_type, inc.coords,
                            [r for r in state.responders.values() if r.id != inc.assigned_responder_id]
                        )
                        if backup_resp:
                            inc.assigned_responder_id = backup_resp.id
                            inc.assigned_responder = backup_resp
                        state_changed = True
                        await manager.broadcast("incident_escalated", {"incident": inc.model_dump(), "level": 2})

                # 2. Smooth movement of Dispatched Responders toward Incident
                elif inc.status == IncidentStatus.DISPATCHED and inc.assigned_responder_id:
                    resp = state.responders.get(inc.assigned_responder_id)
                    if resp and resp.status == ResponderStatus.EN_ROUTE:
                        target = inc.coords
                        # Step responder 8% closer per second
                        d_lat = target.lat - resp.coords.lat
                        d_lng = target.lng - resp.coords.lng
                        dist = calculate_distance_meters(resp.coords, target)
                        if dist > 15:
                            resp.coords.lat += d_lat * 0.08
                            resp.coords.lng += d_lng * 0.08
                            # Recalculate ETA
                            resp.eta_seconds = max(5, int((dist / 7.0)))
                            inc.assigned_responder = resp
                            await manager.broadcast("responder_moved", {"responder": resp.model_dump(), "incident_id": inc.id})

            if state_changed:
                await manager.broadcast("metrics_updated", get_system_metrics())

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in background worker: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: spawn escalation worker
    worker_task = asyncio.create_task(escalation_and_movement_worker())
    yield
    # Shutdown: cancel task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CampusShield - Campus Emergency Response Coordinator",
    description="Aarambhathon Hackathon Project - Real-time emergency reporting, routing, and live tracking.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper: Compute System Metrics
def get_system_metrics() -> dict:
    incidents = list(state.incidents.values())
    total = len(incidents)
    active = sum(1 for i in incidents if i.status not in [IncidentStatus.RESOLVED, IncidentStatus.CANCELLED])
    resolved = sum(1 for i in incidents if i.status == IncidentStatus.RESOLVED)
    escalated_count = sum(1 for i in incidents if i.escalated)

    # Time to acknowledge
    tta_list = [i.time_to_ack_sec for i in incidents if i.time_to_ack_sec is not None]
    avg_tta = round(sum(tta_list) / len(tta_list), 1) if tta_list else 0.0

    # Time to dispatch
    ttd_list = [i.time_to_dispatch_sec for i in incidents if i.time_to_dispatch_sec is not None]
    avg_ttd = round(sum(ttd_list) / len(ttd_list), 1) if ttd_list else 0.0

    # Time to resolve
    ttr_list = [i.time_to_resolve_sec for i in incidents if i.time_to_resolve_sec is not None]
    avg_ttr = round(sum(ttr_list) / len(ttr_list), 1) if ttr_list else 0.0

    avail_responders = sum(1 for r in state.responders.values() if r.status == ResponderStatus.AVAILABLE)

    return {
        "total_incidents": total,
        "active_incidents": active,
        "resolved_incidents": resolved,
        "escalated_incidents": escalated_count,
        "avg_time_to_acknowledge_sec": avg_tta,
        "avg_time_to_dispatch_sec": avg_ttd,
        "avg_time_to_resolve_sec": avg_ttr,
        "available_responders": avail_responders,
        "total_responders": len(state.responders),
        "target_sla_sec": 30
    }


# WebSocket Route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial full state on connect
        await websocket.send_text(json.dumps({
            "event": "init_state",
            "data": {
                "incidents": [i.model_dump() for i in state.incidents.values()],
                "responders": [r.model_dump() for r in state.responders.values()],
                "locations": [loc.model_dump() for loc in state.locations.values()],
                "safepoints": [sp.model_dump() for sp in state.safepoints.values()],
                "broadcasts": [b.model_dump() for b in state.broadcasts],
                "metrics": get_system_metrics()
            }
        }))
        while True:
            # Keep connection alive & handle incoming pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# REST API Routes
@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "service": "CampusShield Coordinator",
        "timestamp": datetime.datetime.now().isoformat(),
        "metrics": get_system_metrics()
    }


@app.get("/api/campus/locations")
async def get_locations():
    return list(state.locations.values())


@app.get("/api/campus/safepoints")
async def get_safepoints():
    return list(state.safepoints.values())


@app.get("/api/responders")
async def get_responders():
    return list(state.responders.values())


@app.put("/api/responders/{resp_id}/status")
async def update_responder_status(resp_id: str, payload: dict):
    if resp_id not in state.responders:
        raise HTTPException(status_code=404, detail="Responder not found")
    resp = state.responders[resp_id]
    if "status" in payload:
        resp.status = ResponderStatus(payload["status"])
    if "lat" in payload and "lng" in payload:
        resp.coords = Coordinates(lat=payload["lat"], lng=payload["lng"])
    await manager.broadcast("responder_updated", resp.model_dump())
    return resp


@app.get("/api/incidents")
async def get_incidents():
    return list(state.incidents.values())


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    return state.incidents[incident_id]


@app.post("/api/incidents")
async def report_incident(incident_in: IncidentCreate):
    """Student 1-tap / 2-tap SOS Report Endpoint"""
    state.seq_num += 1
    new_inc = create_incident_record(
        incident_in=incident_in,
        all_responders=list(state.responders.values()),
        incident_seq_num=state.seq_num
    )
    
    # Update responder state if assigned
    if new_inc.assigned_responder_id and new_inc.assigned_responder_id in state.responders:
        assigned_resp = state.responders[new_inc.assigned_responder_id]
        assigned_resp.status = ResponderStatus.ASSIGNED
        assigned_resp.current_incident_id = new_inc.id

    state.incidents[new_inc.id] = new_inc

    # Broadcast real-time alert to all connected dashboards, responders, reporters
    await manager.broadcast("incident_created", new_inc.model_dump())
    await manager.broadcast("metrics_updated", get_system_metrics())
    return new_inc


@app.post("/api/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str):
    """Responder or Dispatcher acknowledges incident"""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]
    if inc.status != IncidentStatus.REPORTED:
        return inc

    now = datetime.datetime.now()
    inc.status = IncidentStatus.ACKNOWLEDGED
    inc.acknowledged_at = now.isoformat()
    created_dt = datetime.datetime.fromisoformat(inc.created_at)
    inc.time_to_ack_sec = max(1.0, round((now - created_dt).total_seconds(), 1))

    resp_name = inc.assigned_responder.name if inc.assigned_responder else "Dispatch Supervisor"
    inc.logs.append(AuditLog(
        timestamp=now.isoformat(),
        event="ACKNOWLEDGE",
        details=f"Incident acknowledged by {resp_name}. Response team notified. TTA: {inc.time_to_ack_sec}s.",
        actor=resp_name
    ))

    await manager.broadcast("incident_updated", inc.model_dump())
    await manager.broadcast("metrics_updated", get_system_metrics())
    return inc


@app.post("/api/incidents/{incident_id}/dispatch")
async def dispatch_incident(incident_id: str):
    """Responder marks dispatched and en route to incident location"""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]
    
    now = datetime.datetime.now()
    inc.status = IncidentStatus.DISPATCHED
    inc.dispatched_at = now.isoformat()
    created_dt = datetime.datetime.fromisoformat(inc.created_at)
    inc.time_to_dispatch_sec = max(1.0, round((now - created_dt).total_seconds(), 1))

    if inc.assigned_responder_id and inc.assigned_responder_id in state.responders:
        resp = state.responders[inc.assigned_responder_id]
        resp.status = ResponderStatus.EN_ROUTE
        resp.eta_seconds = 180  # Initial 3-minute ETA

    resp_name = inc.assigned_responder.name if inc.assigned_responder else "Emergency Unit"
    inc.logs.append(AuditLog(
        timestamp=now.isoformat(),
        event="DISPATCH",
        details=f"{resp_name} deployed vehicle/unit. Heading to {inc.location_name}.",
        actor=resp_name
    ))

    await manager.broadcast("incident_updated", inc.model_dump())
    await manager.broadcast("metrics_updated", get_system_metrics())
    return inc


@app.post("/api/incidents/{incident_id}/on-site")
async def arrive_on_site(incident_id: str):
    """Responder arrived on scene"""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]
    
    now = datetime.datetime.now()
    inc.status = IncidentStatus.ON_SITE
    inc.on_site_at = now.isoformat()

    if inc.assigned_responder_id and inc.assigned_responder_id in state.responders:
        resp = state.responders[inc.assigned_responder_id]
        resp.status = ResponderStatus.ON_SCENE
        resp.coords = Coordinates(lat=inc.coords.lat, lng=inc.coords.lng)
        resp.eta_seconds = 0

    resp_name = inc.assigned_responder.name if inc.assigned_responder else "Emergency Unit"
    inc.logs.append(AuditLog(
        timestamp=now.isoformat(),
        event="ON_SITE",
        details=f"{resp_name} arrived on site at {inc.location_name} ({inc.floor_room}). First aid & scene stabilization underway.",
        actor=resp_name
    ))

    await manager.broadcast("incident_updated", inc.model_dump())
    await manager.broadcast("metrics_updated", get_system_metrics())
    return inc


@app.post("/api/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    """Incident resolved and closed"""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]
    
    now = datetime.datetime.now()
    inc.status = IncidentStatus.RESOLVED
    inc.resolved_at = now.isoformat()
    created_dt = datetime.datetime.fromisoformat(inc.created_at)
    inc.time_to_resolve_sec = round((now - created_dt).total_seconds(), 1)

    # Free up responder
    if inc.assigned_responder_id and inc.assigned_responder_id in state.responders:
        resp = state.responders[inc.assigned_responder_id]
        resp.status = ResponderStatus.AVAILABLE
        resp.current_incident_id = None
        resp.eta_seconds = None

    inc.logs.append(AuditLog(
        timestamp=now.isoformat(),
        event="CLOSE",
        details=f"Incident safely resolved. Total duration: {inc.time_to_resolve_sec}s. All clear issued.",
        actor="Incident Coordinator"
    ))

    await manager.broadcast("incident_updated", inc.model_dump())
    await manager.broadcast("metrics_updated", get_system_metrics())
    return inc


# Broadcast Alert Endpoint
@app.post("/api/broadcast")
async def create_broadcast(payload: dict):
    alert = BroadcastAlert(
        id=f"ALERT-{len(state.broadcasts)+1:02d}",
        title=payload.get("title", "Campus Emergency Broadcast"),
        message=payload.get("message", "Please remain calm and follow safety coordinator guidelines."),
        severity=payload.get("severity", "warning")
    )
    state.broadcasts.append(alert)
    await manager.broadcast("campus_broadcast", alert.model_dump())
    return alert


# Simulator Endpoints
@app.get("/api/simulator/presets")
async def get_presets():
    return list(SIMULATION_PRESETS.values())


@app.post("/api/simulator/run/{preset_id}")
async def run_simulation_preset(preset_id: str):
    """Launches the selected simulation preset"""
    if preset_id not in SIMULATION_PRESETS:
        raise HTTPException(status_code=404, detail="Preset not found")
    preset = SIMULATION_PRESETS[preset_id]

    inc_in = IncidentCreate(
        incident_type=preset["type"],
        location_name=preset["location_name"],
        floor_room=preset["floor_room"],
        description=preset["description"],
        coords=Coordinates(lat=preset["coords"]["lat"], lng=preset["coords"]["lng"]),
        reporter_name=preset["reporter_name"],
        reporter_phone=preset["reporter_phone"],
        priority=preset["priority"]
    )
    return await report_incident(inc_in)


@app.post("/api/simulator/step/{incident_id}")
async def step_incident_stage(incident_id: str):
    """Advances incident to the next logical phase in the lifecycle"""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]
    
    if inc.status == IncidentStatus.REPORTED:
        return await acknowledge_incident(incident_id)
    elif inc.status == IncidentStatus.ACKNOWLEDGED:
        return await dispatch_incident(incident_id)
    elif inc.status == IncidentStatus.DISPATCHED:
        return await arrive_on_site(incident_id)
    elif inc.status == IncidentStatus.ON_SITE:
        return await resolve_incident(incident_id)
    return inc


@app.post("/api/simulator/reset")
async def reset_simulator():
    """Resets the entire simulator to fresh state"""
    state.reset()
    await manager.broadcast("system_reset", {"message": "System state refreshed"})
    return {"status": "reset_successful", "metrics": get_system_metrics()}


@app.get("/api/metrics")
async def get_metrics_endpoint():
    return get_system_metrics()


# Mount Static Files & HTML entry points
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


@app.get("/reporter")
async def serve_reporter():
    return FileResponse("static/reporter.html")


@app.get("/responder")
async def serve_responder():
    return FileResponse("static/responder.html")


@app.get("/presentation")
async def serve_presentation():
    return FileResponse("presentation/slides.html")


# ─── Live Location Sharing via WebSocket ─────────────────────────────────────
# Responder -> Reporter location push
# When a responder accepts/dispatches, they POST their coords every 3s
# The backend fan-out broadcasts to all connected clients as "responder_location_update"

@app.post("/api/incidents/{incident_id}/location")
async def update_responder_live_location(incident_id: str, payload: dict):
    """Responder continuously pushes their GPS coordinates while en-route.
    Payload: { lat: float, lng: float, responder_id: str }
    Broadcast to all WebSocket clients so the reporter can see live movement."""
    if incident_id not in state.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc = state.incidents[incident_id]

    lat = payload.get("lat")
    lng = payload.get("lng")
    resp_id = payload.get("responder_id", inc.assigned_responder_id)

    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="lat and lng required")

    # Update responder coords in state
    if resp_id and resp_id in state.responders:
        resp = state.responders[resp_id]
        resp.coords = Coordinates(lat=lat, lng=lng)
        inc.assigned_responder = resp
        # Recalculate distance/ETA
        dist = calculate_distance_meters(resp.coords, inc.coords)
        resp.eta_seconds = max(0, int(dist / 7.0))

    await manager.broadcast("responder_location_update", {
        "incident_id": incident_id,
        "responder_id": resp_id,
        "lat": lat,
        "lng": lng,
        "eta_seconds": state.responders[resp_id].eta_seconds if resp_id and resp_id in state.responders else None
    })
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
