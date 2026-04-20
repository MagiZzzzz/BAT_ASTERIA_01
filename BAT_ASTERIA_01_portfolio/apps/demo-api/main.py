from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent.parent
DATA = BASE / "data" / "seed.json"
WEB = BASE / "apps" / "demo-web"
DOCS = BASE / "apps" / "public-docs"

app = FastAPI(title="BAT_ASTERIA_01 Demo API", version="1.0.0")

with DATA.open("r", encoding="utf-8") as f:
    seed = json.load(f)

state = {
    "site": seed["site"],
    "zones": {z["id"]: {**z, "temperature": 21.5 + random.random(), "co2": 650 + random.randint(0, 150), "occupied": z["id"] != "B1_TECH"} for z in seed["zones"]},
    "equipment": {e["id"]: {**e, "status": "ok", "value": random.randint(0, 100)} for e in seed["equipment"]},
    "alarms": [
        {"id": "ALM-CVC-AHU01-FANFAULT", "severity": "critical", "label": "Défaut ventilateur CTA 01", "active": False},
        {"id": "ALM-QAI-CO2-HIGH", "severity": "warning", "label": "CO2 élevé salle réunion", "active": False},
    ],
    "scenarios": {
        "ahu-failure": {"name": "Panne CTA", "running": False},
        "high-co2": {"name": "CO2 élevé", "running": False},
        "schedule-switchover": {"name": "Bascule horaire", "running": False},
    },
}

clients: set[WebSocket] = set()

def now():
    return datetime.now(timezone.utc).isoformat()

def snapshot() -> dict[str, Any]:
    power_kw = 128.4 + random.uniform(-4, 6)
    return {
        "site": state["site"],
        "timestamp": now(),
        "kpi": {
            "open_alarms": sum(1 for a in state["alarms"] if a["active"]),
            "power_kw": round(power_kw, 1),
            "co2_max_ppm": max(z["co2"] for z in state["zones"].values()),
            "occupied_zones": sum(1 for z in state["zones"].values() if z["occupied"]),
            "ahu_running": 2 if not state["scenarios"]["ahu-failure"]["running"] else 1,
        },
        "zones": list(state["zones"].values()),
        "equipment": list(state["equipment"].values()),
        "alarms": state["alarms"],
        "scenarios": state["scenarios"],
    }

async def broadcast(message: dict[str, Any]) -> None:
    dead = []
    for ws in clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)

@app.get("/", response_class=HTMLResponse)
def public_docs_home():
    return FileResponse(DOCS / "index.html")

@app.get("/demo", response_class=HTMLResponse)
def demo_home():
    return FileResponse(WEB / "index.html")

@app.get("/demo/styles.css")
def demo_css():
    return FileResponse(WEB / "styles.css")

@app.get("/demo/app.js")
def demo_js():
    return FileResponse(WEB / "app.js")

@app.get("/api/v1/overview")
def overview():
    return JSONResponse(snapshot())

@app.get("/api/v1/zones")
def zones():
    return JSONResponse(list(state["zones"].values()))

@app.get("/api/v1/equipment")
def equipment():
    return JSONResponse(list(state["equipment"].values()))

@app.get("/api/v1/alarms")
def alarms():
    return JSONResponse(state["alarms"])

@app.get("/api/v1/scenarios")
def scenarios():
    return JSONResponse(state["scenarios"])

@app.post("/api/v1/scenarios/{scenario_id}/trigger")
async def trigger_scenario(scenario_id: str):
    if scenario_id not in state["scenarios"]:
        return JSONResponse({"error": "unknown scenario"}, status_code=404)

    state["scenarios"][scenario_id]["running"] = True

    if scenario_id == "ahu-failure":
        state["alarms"][0]["active"] = True
        state["equipment"]["AHU_01"]["status"] = "fault"
    elif scenario_id == "high-co2":
        state["alarms"][1]["active"] = True
        state["zones"]["R1_MEETING"]["co2"] = 1290
    elif scenario_id == "schedule-switchover":
        for z in state["zones"].values():
            z["occupied"] = False

    await broadcast({"type": "scenario", "scenario": scenario_id, "state": "running", "snapshot": snapshot()})
    return JSONResponse({"ok": True, "scenario": scenario_id, "snapshot": snapshot()})

@app.post("/api/v1/scenarios/{scenario_id}/reset")
async def reset_scenario(scenario_id: str):
    if scenario_id not in state["scenarios"]:
        return JSONResponse({"error": "unknown scenario"}, status_code=404)
    state["scenarios"][scenario_id]["running"] = False

    state["alarms"][0]["active"] = False
    state["alarms"][1]["active"] = False
    state["equipment"]["AHU_01"]["status"] = "ok"
    state["zones"]["R1_MEETING"]["co2"] = 710
    for z in state["zones"].values():
        z["occupied"] = z["id"] != "B1_TECH"

    await broadcast({"type": "scenario", "scenario": scenario_id, "state": "reset", "snapshot": snapshot()})
    return JSONResponse({"ok": True, "scenario": scenario_id, "snapshot": snapshot()})

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.send_json({"type": "tick", "snapshot": snapshot()})
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)
    except Exception:
        clients.discard(ws)

@app.on_event("startup")
async def startup():
    # Nothing heavy here. The app is intentionally simple and demo-friendly.
    pass
