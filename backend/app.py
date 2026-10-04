import os
import json
import time
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import jwt
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from database import SessionLocal, User as DBUser, Audit as DBAudit, Maintenance as DBMaintenance, init_db

PROM = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
ALERT = os.getenv("ALERTMANAGER_URL", "http://localhost:9093").rstrip("/")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALG = "HS256"
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LOG_PATHS = {"/var/log/syslog", "/var/log/auth.log", "/var/log/kern.log"}

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("dc-monitor")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(
    title="Data Center Monitoring & Observability API",
    version="2.0.0",
    description="Secure operational API for Linux infrastructure monitoring."
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

class AcknowledgeRequest(BaseModel):
    note: str = Field(default="", max_length=500)

class DiagnosticRequest(BaseModel):
    server: str = Field(min_length=1, max_length=255)
    command: str = Field(min_length=1, max_length=40)

class MaintenanceRequest(BaseModel):
    server: str
    start: datetime
    end: datetime
    reason: str = Field(min_length=1, max_length=300)

# In-memory application metadata keeps the demo self-contained. Prometheus remains
# the source of truth for time-series metrics. Replace with PostgreSQL persistence
# for multi-instance production deployments.
USERS = {
    "admin": {"password_hash": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin")), "role": "ADMIN"},
    "operator": {"password_hash": pwd_context.hash(os.getenv("OPERATOR_PASSWORD", "operator")), "role": "OPERATOR"},
    "viewer": {"password_hash": pwd_context.hash(os.getenv("VIEWER_PASSWORD", "viewer")), "role": "VIEWER"},
}
AUDIT_LOG: list[dict[str, Any]] = []
MAINTENANCE: list[dict[str, Any]] = []

@app.on_event("startup")
def startup():
    try:
        init_db()
        db=SessionLocal()
        for username, cfg in USERS.items():
            if not db.query(DBUser).filter_by(username=username).first():
                db.add(DBUser(username=username,password_hash=cfg["password_hash"],role=cfg["role"]))
        db.commit(); db.close()
        logger.info("Metadata database initialized")
    except Exception as e:
        logger.warning("Metadata database unavailable; continuing without persistence: %s", e)

def token_for(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": username, "role": role, "iat": now, "exp": now + timedelta(hours=8)}, JWT_SECRET, algorithm=JWT_ALG)

def current_user(authorization: Optional[str] = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALG])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")

def require_role(*roles: str):
    def checker(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker

def audit(user: dict[str, str], action: str, details: str = ""):
    item={"timestamp": datetime.now(timezone.utc).isoformat(),"user":user["username"],"role":user["role"],"action":action,"details":details}
    AUDIT_LOG.insert(0,item); del AUDIT_LOG[200:]
    try:
        db=SessionLocal(); db.add(DBAudit(username=user["username"],role=user["role"],action=action,details=details)); db.commit(); db.close()
    except Exception as e: logger.warning("Audit persistence failed: %s",e)

async def prom_query(query: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=6) as client:
        r = await client.get(f"{PROM}/api/v1/query", params={"query": query})
        r.raise_for_status()
        return r.json().get("data", {}).get("result", [])

async def prom_range(query: str, start: float, end: float, step: int = 60) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(f"{PROM}/api/v1/query_range", params={"query": query, "start": start, "end": end, "step": step})
        r.raise_for_status()
        return r.json().get("data", {}).get("result", [])

def scalar(rows, default=0.0):
    try: return float(rows[0]["value"][1]) if rows else default
    except (KeyError, IndexError, ValueError, TypeError): return default

async def server_rows():
    rows = await prom_query('up{job="linux-servers"}')
    output = []
    for row in rows:
        metric = row.get("metric", {})
        instance = metric.get("instance", "unknown")
        label = instance.replace("\\", "\\\\").replace('"', '\\"')
        queries = {
            "cpu": f'100 - (avg by(instance) (rate(node_cpu_seconds_total{{job="linux-servers",instance="{label}",mode="idle"}}[5m])) * 100)',
            "memory": f'100 * (1 - node_memory_MemAvailable_bytes{{job="linux-servers",instance="{label}"}} / node_memory_MemTotal_bytes{{job="linux-servers",instance="{label}"}})',
            "disk": f'100 * (1 - min(node_filesystem_avail_bytes{{job="linux-servers",instance="{label}",fstype!~"tmpfs|overlay"}} / node_filesystem_size_bytes{{job="linux-servers",instance="{label}",fstype!~"tmpfs|overlay"}}))',
            "load": f'node_load5{{job="linux-servers",instance="{label}"}}',
            "rx": f'sum(rate(node_network_receive_bytes_total{{job="linux-servers",instance="{label}",device!="lo"}}[5m])) * 8',
            "tx": f'sum(rate(node_network_transmit_bytes_total{{job="linux-servers",instance="{label}",device!="lo"}}[5m])) * 8',
            "temp": f'max(node_hwmon_temp_celsius{{job="linux-servers",instance="{label}"}})',
            "uptime": f'min(time() - node_boot_time_seconds{{job="linux-servers",instance="{label}"}})',
        }
        vals = {}
        for k, q in queries.items():
            try: vals[k] = scalar(await prom_query(q), 0)
            except Exception: vals[k] = 0
        up = row.get("value", ["", "0"])[1] == "1"
        health = 100 if up else 0
        if up:
            penalties = [max(0, vals["cpu"]-60)*0.5, max(0, vals["memory"]-65)*0.5, max(0, vals["disk"]-70)*0.35]
            if vals["temp"] > 70: penalties.append(min(20, (vals["temp"]-70)*0.8))
            health = max(0, round(100 - sum(penalties)))
        output.append({
            "id": instance, "instance": instance, "hostname": instance.split(":")[0],
            "ip": instance.split(":")[0], "status": "UP" if up else "DOWN",
            "environment": metric.get("environment", "unknown"),
            "role": metric.get("role", "linux-server"),
            "cpu": round(vals["cpu"], 1), "memory": round(vals["memory"], 1),
            "disk": round(vals["disk"], 1), "network_rx_bps": round(vals["rx"], 0),
            "network_tx_bps": round(vals["tx"], 0), "temperature": round(vals["temp"], 1) if vals["temp"] else None,
            "load": round(vals["load"], 2), "uptime_seconds": round(vals["uptime"], 0),
            "health_score": health, "last_heartbeat": datetime.now(timezone.utc).isoformat()
        })
    return output

@app.get("/health")
async def health():
    prom_ok = False
    try:
        await prom_query("up")
        prom_ok = True
    except Exception: pass
    return {"status": "ok", "service": "data-center-monitoring-api", "prometheus": prom_ok, "demo_mode": DEMO_MODE}

@app.post("/api/auth/login")
async def login(body: LoginRequest):
    user = USERS.get(body.username)
    role = user["role"] if user else None
    password_hash = user["password_hash"] if user else None
    try:
        db=SessionLocal(); row=db.query(DBUser).filter_by(username=body.username).first(); db.close()
        if row: role=row.role; password_hash=row.password_hash
    except Exception: pass
    if not password_hash or not pwd_context.verify(body.password, password_hash):
        raise HTTPException(401, "Invalid username or password")
    record = {"username": body.username, "role": role}
    audit(record, "USER_LOGIN")
    return {"access_token": token_for(body.username, user["role"]), "token_type": "bearer", "role": user["role"], "username": body.username}

@app.get("/api/auth/me")
async def me(user=Depends(current_user)): return user

@app.get("/api/overview")
async def overview(user=Depends(current_user)):
    try:
        servers = await server_rows()
    except Exception as e:
        logger.warning("Prometheus unavailable: %s", e)
        servers = []
    up = sum(s["status"] == "UP" for s in servers)
    down = len(servers) - up
    avg = lambda key: round(sum(s[key] for s in servers if s["status"] == "UP") / max(up,1), 1)
    alerts = await get_alerts_internal()
    return {"servers_total": len(servers), "servers_up": up, "servers_down": down,
            "critical_servers": sum(s["health_score"] < 60 for s in servers),
            "warning_servers": sum(60 <= s["health_score"] < 80 for s in servers),
            "avg_cpu": avg("cpu"), "avg_memory": avg("memory"), "avg_disk": avg("disk"),
            "network_bps": round(sum(s["network_rx_bps"] + s["network_tx_bps"] for s in servers)), 
            "active_alerts": sum(a.get("status", {}).get("state") == "active" for a in alerts),
            "resolved_alerts": sum(a.get("status", {}).get("state") == "resolved" for a in alerts),
            "monitoring_uptime": "Live" if servers else "Waiting for targets"}

@app.get("/api/servers")
async def servers(user=Depends(current_user)):
    try: return await server_rows()
    except Exception as e:
        logger.exception("server query failed")
        raise HTTPException(503, f"Prometheus unavailable: {e}")

@app.get("/api/servers/{server_id:path}/metrics")
async def server_metrics(server_id: str, minutes: int = Query(60, ge=5, le=1440), user=Depends(current_user)):
    end = time.time(); start = end - minutes*60
    safe = server_id.replace("\\", "\\\\").replace('"', '\\"')
    qs = {
      "cpu": f'100 - (avg by(instance) (rate(node_cpu_seconds_total{{job="linux-servers",instance="{safe}",mode="idle"}}[5m])) * 100)',
      "memory": f'100 * (1 - node_memory_MemAvailable_bytes{{job="linux-servers",instance="{safe}"}} / node_memory_MemTotal_bytes{{job="linux-servers",instance="{safe}"}})',
      "network_rx": f'sum(rate(node_network_receive_bytes_total{{job="linux-servers",instance="{safe}",device!="lo"}}[5m])) * 8',
      "network_tx": f'sum(rate(node_network_transmit_bytes_total{{job="linux-servers",instance="{safe}",device!="lo"}}[5m])) * 8',
      "load": f'node_load5{{job="linux-servers",instance="{safe}"}}'
    }
    out={}
    for key,q in qs.items():
        try: out[key]=await prom_range(q,start,end,60)
        except Exception: out[key]=[]
    return {"server": server_id, "minutes": minutes, "metrics": out}

async def get_alerts_internal():
    try:
        async with httpx.AsyncClient(timeout=6) as client:
            r=await client.get(f"{ALERT}/api/v2/alerts"); r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Alertmanager unavailable: %s", e); return []

@app.get("/api/alerts")
async def alerts(user=Depends(current_user)): return await get_alerts_internal()

@app.get("/api/alerts/active")
async def active_alerts(user=Depends(current_user)): return [a for a in await get_alerts_internal() if a.get("status",{}).get("state")=="active"]

@app.get("/api/alerts/history")
async def alert_history(user=Depends(current_user)): return await get_alerts_internal()

@app.post("/api/alerts/{fingerprint}/acknowledge")
async def acknowledge(fingerprint: str, body: AcknowledgeRequest, user=Depends(require_role("ADMIN","OPERATOR"))):
    audit(user, "ALERT_ACKNOWLEDGED", f"{fingerprint}: {body.note}")
    return {"status":"acknowledged","fingerprint":fingerprint,"note":body.note}

@app.get("/api/network")
async def network(user=Depends(current_user)):
    try:
        servers=await server_rows()
        return {"servers":[{"instance":s["instance"],"rx_bps":s["network_rx_bps"],"tx_bps":s["network_tx_bps"]} for s in servers]}
    except Exception: return {"servers":[]}

@app.get("/api/disk")
async def disk(user=Depends(current_user)):
    try:
        servers=await server_rows()
        return {"servers":[{"instance":s["instance"],"disk_percent":s["disk"]} for s in servers]}
    except Exception: return {"servers":[]}

@app.get("/api/system")
async def system(user=Depends(current_user)):
    try:
        servers=await server_rows()
        return {"servers":[{"instance":s["instance"],"load":s["load"],"temperature":s["temperature"],"uptime_seconds":s["uptime_seconds"]} for s in servers]}
    except Exception: return {"servers":[]}

@app.get("/api/anomaly")
async def anomaly(user=Depends(current_user)):
    try:
        servers=await server_rows()
        findings=[]
        for s in servers:
            score=0
            reasons=[]
            if s["cpu"] >= 90: score += 2; reasons.append("CPU above 90%")
            if s["memory"] >= 90: score += 2; reasons.append("Memory above 90%")
            if s["network_rx_bps"] > 100_000_000: score += 1; reasons.append("High inbound traffic")
            if s["disk"] >= 90: score += 1; reasons.append("Disk above 90%")
            findings.append({"instance":s["instance"],"anomaly":score>=2,"score":score,"reasons":reasons})
        return {"method":"Rule-assisted z-score-ready baseline","experimental":True,"findings":findings}
    except Exception: return {"method":"experimental","experimental":True,"findings":[]}

@app.get("/api/logs")
async def logs(path: str="/var/log/syslog", limit: int=Query(50, ge=1, le=200), user=Depends(require_role("ADMIN","OPERATOR"))):
    if path not in LOG_PATHS: raise HTTPException(400, "Log path is not allowlisted")
    p=Path(path)
    if not p.exists(): return {"path":path,"available":False,"entries":[]}
    try:
        lines=p.read_text(errors="replace").splitlines()[-limit:]
        patterns=("ERROR","FAILED","CRITICAL","WARNING","ssh","kernel","disk")
        entries=[{"line":x,"severity":"critical" if "CRITICAL" in x.upper() else "warning" if any(p in x for p in patterns) else "info"} for x in lines]
        return {"path":path,"available":True,"entries":entries}
    except Exception as e: raise HTTPException(500, f"Unable to read log: {e}")

ALLOWED_DIAGNOSTICS={
    "cpu":"uname -a && nproc && uptime",
    "memory":"free -h",
    "disk":"df -h",
    "uptime":"uptime",
    "network":"ip -brief address",
    "load":"cat /proc/loadavg",
    "os":"cat /etc/os-release",
}
@app.post("/api/diagnostics")
async def diagnostics(body: DiagnosticRequest, user=Depends(require_role("ADMIN","OPERATOR"))):
    if body.command not in ALLOWED_DIAGNOSTICS: raise HTTPException(400, "Diagnostic command is not allowed")
    # Safe-by-design placeholder: execute only through a future SSH connector.
    audit(user, "DIAGNOSTIC_REQUESTED", f"{body.server}:{body.command}")
    return {"server":body.server,"command":body.command,"allowed":True,"execution":"remote SSH connector required","command_preview":ALLOWED_DIAGNOSTICS[body.command]}

@app.get("/api/audit")
async def audit_log(user=Depends(require_role("ADMIN","OPERATOR"))):
    try:
        db=SessionLocal(); rows=db.query(DBAudit).order_by(DBAudit.id.desc()).limit(200).all(); db.close()
        return [{"timestamp":r.timestamp.replace(tzinfo=timezone.utc).isoformat(),"user":r.username,"role":r.role,"action":r.action,"details":r.details} for r in rows]
    except Exception: return AUDIT_LOG

@app.post("/api/maintenance")
async def maintenance(body: MaintenanceRequest, user=Depends(require_role("ADMIN","OPERATOR"))):
    if body.end <= body.start: raise HTTPException(400,"End must be after start")
    item={"id":len(MAINTENANCE)+1,**body.model_dump(),"created_by":user["username"]}
    item["start"]=item["start"].isoformat(); item["end"]=item["end"].isoformat()
    MAINTENANCE.append(item); audit(user,"MAINTENANCE_CREATED",body.server)
    return item

@app.get("/api/maintenance")
async def maintenance_list(user=Depends(current_user)): return MAINTENANCE
