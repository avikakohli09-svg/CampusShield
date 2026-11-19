"""
Data models for CampusShield Emergency Response Coordinator
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime


class IncidentType(str, Enum):
    MEDICAL = "medical"
    FIRE = "fire"
    SECURITY = "security"
    ACCIDENT = "accident"
    HAZARD = "hazard"
    GENERAL = "general"


class IncidentPriority(str, Enum):
    CRITICAL = "critical"  # Immediate life threat (cardiac, heavy bleeding, active shooter, large fire)
    HIGH = "high"          # Severe risk (unconscious, bone fracture, chemical hazard)
    MEDIUM = "medium"      # Moderate urgency (minor injury, localized smoke, property theft)
    LOW = "low"            # Low risk (suspicious loitering, water leak)


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    DISPATCHED = "dispatched"
    ON_SITE = "on_site"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ResponderType(str, Enum):
    MEDICAL = "medical"
    SECURITY = "security"
    FIRE = "fire"
    RAPID_ACTION = "rapid_action"


class ResponderStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    OFF_DUTY = "off_duty"


class Coordinates(BaseModel):
    lat: float
    lng: float


class CampusLocation(BaseModel):
    id: str
    name: str
    category: str  # academic, hostel, library, admin, sports, medical
    building_code: str
    coords: Coordinates
    floors: int = 3
    primary_safe_point_id: Optional[str] = None


class SafePoint(BaseModel):
    id: str
    name: str
    category: str  # assembly_point, aed_station, first_aid, fire_extinguisher
    coords: Coordinates
    capacity: Optional[int] = 200
    instructions: str


class Responder(BaseModel):
    id: str
    name: str
    role: str
    responder_type: ResponderType
    phone: str
    unit_code: str
    coords: Coordinates
    status: ResponderStatus = ResponderStatus.AVAILABLE
    current_incident_id: Optional[str] = None
    eta_seconds: Optional[int] = None
    avatar_url: Optional[str] = None


class AuditLog(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    event: str
    details: str
    actor: str


class IncidentCreate(BaseModel):
    incident_type: IncidentType
    location_name: str
    coords: Optional[Coordinates] = None
    floor_room: Optional[str] = ""
    description: Optional[str] = ""
    reporter_name: Optional[str] = "Anonymous Student"
    reporter_phone: Optional[str] = "+91 98765 43210"
    priority: Optional[IncidentPriority] = None


class Incident(BaseModel):
    id: str
    code: str
    incident_type: IncidentType
    priority: IncidentPriority
    status: IncidentStatus = IncidentStatus.REPORTED
    location_name: str
    coords: Coordinates
    floor_room: str = ""
    description: str = ""
    reporter_name: str = "Anonymous Student"
    reporter_phone: str = "+91 98765 43210"
    
    assigned_responder_id: Optional[str] = None
    assigned_responder: Optional[Responder] = None
    
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    acknowledged_at: Optional[str] = None
    dispatched_at: Optional[str] = None
    on_site_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    escalated: bool = False
    escalation_level: int = 0  # 0=normal, 1=reminder sent, 2=supervisor escalation, 3=campus-wide alarm
    seconds_elapsed: int = 0
    time_to_ack_sec: Optional[float] = None
    time_to_dispatch_sec: Optional[float] = None
    time_to_resolve_sec: Optional[float] = None
    
    safety_instructions: List[str] = []
    first_aid_guidelines: List[str] = []
    nearest_safe_point: Optional[SafePoint] = None
    
    logs: List[AuditLog] = []


class BroadcastAlert(BaseModel):
    id: str
    title: str
    message: str
    severity: str  # critical, warning, info
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    active: bool = True
