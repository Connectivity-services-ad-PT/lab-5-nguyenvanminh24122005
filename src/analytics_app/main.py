import os
from typing import Optional
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics-integrated-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.1.0-analytics")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

app = FastAPI(
    title="Smart Campus — Analytics Service",
    version=SERVICE_VERSION,
    description="Analytics service cho Lab 05 Docker Compose.",
)


def build_problem(*, status_code, title, detail, instance=None):
    p = {"type": "about:blank", "title": title, "status": status_code, "detail": detail}
    if instance:
        p["instance"] = instance
    return p


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail,
                            media_type="application/problem+json")
    return JSONResponse(
        status_code=exc.status_code,
        content=build_problem(status_code=exc.status_code, title="HTTP Error",
                               detail=str(exc.detail), instance=str(request.url.path)),
        media_type="application/problem+json",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=build_problem(status_code=422, title="Validation error",
                               detail="Request validation failed",
                               instance=str(request.url.path)),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(
            status_code=401,
            detail=build_problem(status_code=401, title="Unauthorized",
                                  detail="Missing or invalid bearer token"),
        )


# ── Dữ liệu mẫu ──────────────────────────────────────────────────────────────

telemetry_items = [
    {
        "eventId": "d6703cc8-9e79-415d-ac03-a4dc7f6ab43c",
        "eventType": "telemetry.ingested",
        "timestamp": "2019-08-24T14:15:22Z",
        "source": "iot",
        "data": {
            "deviceId": "SENSOR-001",
            "sensorType": "temperature",
            "value": 38.5,
            "unit": "celsius",
            "timestamp": "2019-08-24T14:15:22Z",
            "zoneId": "ZONE-A"
        }
    }
]

camera_motion_items = [
    {
        "eventId": "c6703cc8-9e79-415d-ac03-a4dc7f6ab43c",
        "correlationId": "48fb4cd3-2ef6-4479-bea1-7c92721b988c",
        "eventType": "camera.motion.detected",
        "timestamp": "2019-08-24T14:15:22Z",
        "source": "camera",
        "data": {
            "cameraId": "CAM-001",
            "zoneId": "ZONE-A",
            "confidence": 0.91
        }
    }
]

policy_decision_items = [
    {
        "eventId": "p6703cc8-9e79-415d-ac03-a4dc7f6ab43c",
        "eventType": "policy.decision.created",
        "timestamp": "2019-08-24T14:15:22Z",
        "source": "core-business",
        "data": {
            "policyId": "POLICY-001",
            "decision": "allow",
            "zoneId": "ZONE-A"
        }
    }
]

access_log_items = [
    {
        "eventId": "a6703cc8-9e79-415d-ac03-a4dc7f6ab43c",
        "correlationId": "48fb4cd3-2ef6-4479-bea1-7c92721b988c",
        "eventType": "access.log.created",
        "timestamp": "2019-08-24T14:15:22Z",
        "source": "access-gate",
        "data": {
            "gateId": "GATE-001",
            "zoneId": "ZONE-A",
            "direction": "in",
            "personHash": "person-001"
        }
    }
]

alerts_items = [
    {
        "id": "a001",
        "sourceService": "core-business",
        "alertType": "UNAUTHORIZED_ACCESS",
        "severity": "HIGH",
        "message": "Phát hiện truy cập trái phép tại cổng chính",
        "status": "OPEN",
        "createdAt": "2026-06-14T08:00:00Z"
    }
]


class AlertPayload(BaseModel):
    sourceService: str
    alertType: str
    severity: str
    message: str
    relatedEventId: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION
    }

@app.head("/health")
def health_head():
    return None

@app.get("/telemetry", dependencies=[Depends(verify_bearer_token)])
def get_telemetry():
    return {"items": telemetry_items, "total": len(telemetry_items), "nextCursor": None}

@app.get("/camera/motion", dependencies=[Depends(verify_bearer_token)])
def get_camera_motion():
    return {"items": camera_motion_items, "total": len(camera_motion_items), "nextCursor": None}

@app.get("/policy-decisions", dependencies=[Depends(verify_bearer_token)])
def get_policy_decisions():
    return {"items": policy_decision_items, "total": len(policy_decision_items), "nextCursor": None}

@app.get("/access/logs", dependencies=[Depends(verify_bearer_token)])
def get_access_logs():
    return {"items": access_log_items, "total": len(access_log_items), "nextCursor": None}

@app.get("/alerts", dependencies=[Depends(verify_bearer_token)])
def get_alerts():
    return {"items": alerts_items, "total": len(alerts_items), "nextCursor": None}

@app.post("/alerts", status_code=201, dependencies=[Depends(verify_bearer_token)])
def create_alert(payload: AlertPayload):
    new_alert = {
        "id": "alert-new-001",
        "sourceService": payload.sourceService,
        "alertType": payload.alertType,
        "severity": payload.severity,
        "message": payload.message,
        "status": "OPEN",
        "createdAt": "2026-06-14T08:00:00Z"
    }
    alerts_items.append(new_alert)
    return new_alert

@app.get("/events", dependencies=[Depends(verify_bearer_token)])
def get_events():
    all_events = telemetry_items + camera_motion_items + policy_decision_items + access_log_items
    return {"items": all_events, "total": len(all_events), "nextCursor": None}