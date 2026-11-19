"""
Triage Rules Engine, Geospatial Proximity Allocator, and Escalation Engine
"""
import math
import datetime
from typing import List, Optional, Tuple, Dict
from app.models import (
    Incident, IncidentCreate, IncidentType, IncidentPriority, IncidentStatus,
    Responder, ResponderType, ResponderStatus, Coordinates, SafePoint, AuditLog
)
from app.data import CAMPUS_LOCATIONS, SAFE_POINTS, STANDARD_INSTRUCTIONS


def calculate_distance_meters(c1: Coordinates, c2: Coordinates) -> float:
    """Haversine distance in meters between two lat/lng coordinates"""
    R = 6371000  # Radius of earth in meters
    phi1 = math.radians(c1.lat)
    phi2 = math.radians(c2.lat)
    delta_phi = math.radians(c2.lat - c1.lat)
    delta_lambda = math.radians(c2.lng - c1.lng)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def determine_priority(incident_type: IncidentType, description: str = "") -> IncidentPriority:
    """Triage rules engine: maps incident type & description to priority level"""
    desc_lower = description.lower()
    
    if incident_type == IncidentType.FIRE:
        return IncidentPriority.CRITICAL
    elif incident_type == IncidentType.MEDICAL:
        critical_words = ["collapse", "unconscious", "heart", "cardiac", "breathing", "cpr", "bleeding", "seizure", "choking"]
        if any(w in desc_lower for w in critical_words) or not description:
            return IncidentPriority.CRITICAL
        return IncidentPriority.HIGH
    elif incident_type == IncidentType.SECURITY:
        if any(w in desc_lower for w in ["weapon", "knife", "intruder", "attack", "violence", "threat"]):
            return IncidentPriority.CRITICAL
        return IncidentPriority.HIGH
    elif incident_type == IncidentType.HAZARD:
        return IncidentPriority.HIGH
    elif incident_type == IncidentType.ACCIDENT:
        return IncidentPriority.MEDIUM
    return IncidentPriority.LOW


def find_nearest_safe_point(incident_coords: Coordinates) -> Tuple[SafePoint, float]:
    """Finds closest safe point or AED to the incident coordinates"""
    best_sp = None
    min_dist = float("inf")
    for sp in SAFE_POINTS.values():
        dist = calculate_distance_meters(incident_coords, sp.coords)
        if dist < min_dist:
            min_dist = dist
            best_sp = sp
    return best_sp, min_dist


def select_best_responder(
    incident_type: IncidentType,
    incident_coords: Coordinates,
    responders: List[Responder]
) -> Tuple[Optional[Responder], float, int]:
    """
    Ranks responders by:
    1. Specialty match (e.g. Medical for Medical, Fire for Fire, Security for Security)
    2. Availability status (AVAILABLE > EN_ROUTE > BUSY)
    3. Proximity (closest Euclidean/Haversine distance)
    Returns: (best_responder, distance_meters, eta_seconds)
    """
    # Filter available responders first
    preferred_type = {
        IncidentType.MEDICAL: ResponderType.MEDICAL,
        IncidentType.FIRE: ResponderType.FIRE,
        IncidentType.SECURITY: ResponderType.SECURITY,
        IncidentType.ACCIDENT: ResponderType.MEDICAL,
        IncidentType.HAZARD: ResponderType.FIRE,
        IncidentType.GENERAL: ResponderType.SECURITY
    }.get(incident_type, ResponderType.SECURITY)

    # Candidate scoring: (is_preferred_type, is_available, -distance)
    scored_candidates = []
    for r in responders:
        dist = calculate_distance_meters(incident_coords, r.coords)
        type_match = (r.responder_type == preferred_type)
        is_avail = (r.status == ResponderStatus.AVAILABLE)
        
        # Campus speed: 25 km/h for vehicles (approx 7 m/s) with 30s mobilization buffer
        eta_sec = int((dist / 7.0) + 30)
        
        # Priority score tuple for sorting (higher is better)
        score = (
            2 if (type_match and is_avail) else (1 if is_avail else 0),
            -dist
        )
        scored_candidates.append((score, r, dist, eta_sec))

    if not scored_candidates:
        return None, 0.0, 0

    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    best = scored_candidates[0]
    return best[1], best[2], best[3]


def create_incident_record(
    incident_in: IncidentCreate,
    all_responders: List[Responder],
    incident_seq_num: int
) -> Incident:
    """Creates a fully triaged incident with auto-routing, safe points, and safety guide"""
    # 1. Location and Coords
    coords = incident_in.coords
    location_name = incident_in.location_name
    if not coords:
        # Match from known campus locations
        matched_loc = None
        for loc in CAMPUS_LOCATIONS.values():
            if loc.name.lower() in location_name.lower() or location_name.lower() in loc.name.lower():
                matched_loc = loc
                break
        if matched_loc:
            coords = matched_loc.coords
            location_name = matched_loc.name
        else:
            # Fallback to campus center
            coords = Coordinates(lat=28.5463, lng=77.1924)

    # 2. Triage priority
    priority = incident_in.priority or determine_priority(incident_in.incident_type, incident_in.description or "")

    # 3. Find Nearest Safe Point
    nearest_sp, sp_dist = find_nearest_safe_point(coords)

    # 4. Instructions
    instr_data = STANDARD_INSTRUCTIONS.get(incident_in.incident_type, STANDARD_INSTRUCTIONS[IncidentType.GENERAL])
    safety_instructions = instr_data.get("immediate", [])
    first_aid_guidelines = instr_data.get("dos", []) + [f"AVOID: {x}" for x in instr_data.get("donts", [])]

    # 5. Best responder selection
    best_resp, resp_dist, eta_sec = select_best_responder(incident_in.incident_type, coords, all_responders)

    inc_id = f"INC-{datetime.datetime.now().strftime('%m%d')}-{incident_seq_num:03d}"
    code = f"CS-{incident_seq_num:03d}"

    initial_logs = [
        AuditLog(
            event="LOCATE",
            details=f"GPS fix locked at [{coords.lat:.4f}, {coords.lng:.4f}] - {location_name}",
            actor="Mobile Client GPS"
        ),
        AuditLog(
            event="REPORT",
            details=f"Incident '{incident_in.incident_type.value.upper()}' reported by {incident_in.reporter_name}",
            actor=incident_in.reporter_name
        ),
        AuditLog(
            event="TRIAGE",
            details=f"Rules Engine assigned priority '{priority.value.upper()}' based on incident category",
            actor="CampusShield Rules Engine"
        )
    ]

    assigned_id = None
    if best_resp:
        assigned_id = best_resp.id
        initial_logs.append(
            AuditLog(
                event="ASSIGN",
                details=f"Auto-routed to closest unit {best_resp.unit_code} ({best_resp.name}) - Distance: {resp_dist:.0f}m, Est ETA: {eta_sec // 60}m {eta_sec % 60}s",
                actor="Proximity Dispatcher"
            )
        )

    incident = Incident(
        id=inc_id,
        code=code,
        incident_type=incident_in.incident_type,
        priority=priority,
        status=IncidentStatus.REPORTED,
        location_name=location_name,
        coords=coords,
        floor_room=incident_in.floor_room or "Ground Level",
        description=incident_in.description or f"Emergency reported at {location_name}",
        reporter_name=incident_in.reporter_name or "Campus Student",
        reporter_phone=incident_in.reporter_phone or "+91 98765 43210",
        assigned_responder_id=assigned_id,
        assigned_responder=best_resp,
        safety_instructions=safety_instructions,
        first_aid_guidelines=first_aid_guidelines,
        nearest_safe_point=nearest_sp,
        logs=initial_logs
    )
    return incident
