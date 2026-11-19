"""
Mock data and campus geo-spatial definitions for CampusShield
Centered on a realistic collegiate campus layout with precise coordinates.
"""
from typing import Dict, List
from app.models import (
    CampusLocation, SafePoint, Responder, ResponderType, ResponderStatus,
    Coordinates, IncidentType
)

# Campus center benchmark
CAMPUS_CENTER = {"lat": 28.5458, "lng": 77.1920}

CAMPUS_LOCATIONS: Dict[str, CampusLocation] = {
    "loc_library": CampusLocation(
        id="loc_library",
        name="Central University Library",
        category="library",
        building_code="LIB-01",
        coords=Coordinates(lat=28.5463, lng=77.1924),
        floors=4,
        primary_safe_point_id="safe_library_lawn"
    ),
    "loc_science": CampusLocation(
        id="loc_science",
        name="Science & Chemistry Block B",
        category="academic",
        building_code="SCI-B",
        coords=Coordinates(lat=28.5471, lng=77.1908),
        floors=5,
        primary_safe_point_id="safe_north_lawn"
    ),
    "loc_engineering": CampusLocation(
        id="loc_engineering",
        name="Computer Science & Engineering Complex",
        category="academic",
        building_code="ENG-A",
        coords=Coordinates(lat=28.5452, lng=77.1905),
        floors=4,
        primary_safe_point_id="safe_sports_ground"
    ),
    "loc_health_center": CampusLocation(
        id="loc_health_center",
        name="Campus Health Center & Clinic",
        category="medical",
        building_code="MED-01",
        coords=Coordinates(lat=28.5445, lng=77.1935),
        floors=2,
        primary_safe_point_id="safe_health_lawn"
    ),
    "loc_admin": CampusLocation(
        id="loc_admin",
        name="Main Administrative Headquarters",
        category="admin",
        building_code="ADM-01",
        coords=Coordinates(lat=28.5460, lng=77.1942),
        floors=3,
        primary_safe_point_id="safe_admin_circle"
    ),
    "loc_hostel_north": CampusLocation(
        id="loc_hostel_north",
        name="Aryabhatta Boys Hostel (North)",
        category="hostel",
        building_code="HST-N",
        coords=Coordinates(lat=28.5482, lng=77.1930),
        floors=6,
        primary_safe_point_id="safe_north_lawn"
    ),
    "loc_hostel_south": CampusLocation(
        id="loc_hostel_south",
        name="Gargi Girls Hostel (South)",
        category="hostel",
        building_code="HST-S",
        coords=Coordinates(lat=28.5435, lng=77.1915),
        floors=6,
        primary_safe_point_id="safe_sports_ground"
    ),
    "loc_cafeteria": CampusLocation(
        id="loc_cafeteria",
        name="Student Activity & Food Court",
        category="student_center",
        building_code="SAC-01",
        coords=Coordinates(lat=28.5455, lng=77.1918),
        floors=2,
        primary_safe_point_id="safe_central_plaza"
    ),
    "loc_sports": CampusLocation(
        id="loc_sports",
        name="University Sports Arena & Track",
        category="sports",
        building_code="SPT-01",
        coords=Coordinates(lat=28.5440, lng=77.1895),
        floors=2,
        primary_safe_point_id="safe_sports_ground"
    ),
    "loc_main_gate": CampusLocation(
        id="loc_main_gate",
        name="Main Security Gate & Visitor Booth",
        category="security",
        building_code="SEC-GATE",
        coords=Coordinates(lat=28.5440, lng=77.1950),
        floors=1,
        primary_safe_point_id="safe_admin_circle"
    )
}

SAFE_POINTS: Dict[str, SafePoint] = {
    "safe_sports_ground": SafePoint(
        id="safe_sports_ground",
        name="Grand Athletic Ground - Evacuation Assembly 1",
        category="assembly_point",
        coords=Coordinates(lat=28.5438, lng=77.1898),
        capacity=1500,
        instructions="Primary disaster assembly zone. Clear from buildings, open sky with emergency medical triage tents."
    ),
    "safe_north_lawn": SafePoint(
        id="safe_north_lawn",
        name="North Residential Lawn - Assembly 2",
        category="assembly_point",
        coords=Coordinates(lat=28.5478, lng=77.1925),
        capacity=600,
        instructions="Safe assembly zone for North Hostels and Science Block. Equipped with emergency water and lighting."
    ),
    "safe_library_lawn": SafePoint(
        id="safe_library_lawn",
        name="Library Plaza Assembly & AED Post",
        category="aed_station",
        coords=Coordinates(lat=28.5461, lng=77.1920),
        capacity=300,
        instructions="Automatic External Defibrillator (AED) mounted at South Pillar. First aid kit and stretcher stationed here."
    ),
    "safe_central_plaza": SafePoint(
        id="safe_central_plaza",
        name="Central Fountain Plaza Safe Area",
        category="assembly_point",
        coords=Coordinates(lat=28.5456, lng=77.1925),
        capacity=400,
        instructions="Open gathering space midway between Admin and Library with public address speaker."
    ),
    "safe_admin_circle": SafePoint(
        id="safe_admin_circle",
        name="Admin Parking Emergency Muster Point",
        category="assembly_point",
        coords=Coordinates(lat=28.5458, lng=77.1945),
        capacity=500,
        instructions="Immediate vehicle egress zone for external municipal fire tenders and city ambulances."
    )
}

DEFAULT_RESPONDERS: List[Responder] = [
    Responder(
        id="resp_med_01",
        name="Dr. Ananya Roy & EMT Paramedics",
        role="Campus Medical Officer (Ambulance Unit)",
        responder_type=ResponderType.MEDICAL,
        phone="+91 98111 22334",
        unit_code="AMBULANCE-01",
        coords=Coordinates(lat=28.5446, lng=77.1934),  # Stationed at Health Center
        status=ResponderStatus.AVAILABLE,
        avatar_url="https://images.unsplash.com/photo-1594824813583-e18e865f123c?w=150"
    ),
    Responder(
        id="resp_sec_alpha",
        name="Officer Vikram Singh",
        role="Senior Campus Security Patrol (Quick Response)",
        responder_type=ResponderType.SECURITY,
        phone="+91 98222 33445",
        unit_code="SECURITY-ALPHA (Mobile)",
        coords=Coordinates(lat=28.5442, lng=77.1948),  # Patrol near Main Gate
        status=ResponderStatus.AVAILABLE,
        avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"
    ),
    Responder(
        id="resp_sec_beta",
        name="Officer Rajesh Kumar",
        role="Academic Quad Foot Patrol",
        responder_type=ResponderType.SECURITY,
        phone="+91 98333 44556",
        unit_code="SECURITY-BETA (Foot)",
        coords=Coordinates(lat=28.5460, lng=77.1915),  # In Quad between Science & Library
        status=ResponderStatus.AVAILABLE,
        avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"
    ),
    Responder(
        id="resp_fire_01",
        name="Safety Marshall Suresh Patil",
        role="Fire Emergency & Evacuation Lead",
        responder_type=ResponderType.FIRE,
        phone="+91 98444 55667",
        unit_code="FIRE-HAZMAT-01",
        coords=Coordinates(lat=28.5450, lng=77.1938),  # Near Admin / Utility depot
        status=ResponderStatus.AVAILABLE,
        avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"
    )
]

STANDARD_INSTRUCTIONS: Dict[str, Dict[str, List[str]]] = {
    IncidentType.MEDICAL: {
        "immediate": [
            "Keep the patient calm and lying down. Do not move them if spinal injury is suspected.",
            "Check responsiveness: gently shake shoulders and ask loudly, 'Are you okay?'",
            "Check breathing: if not breathing normally, begin Hands-Only CPR (100-120 compressions/min to the beat of 'Stayin' Alive').",
            "Locate the nearest AED (Stationed at Library Plaza South Pillar or Health Center).",
            "If vomiting or unconscious but breathing, turn them into Recovery Position on their side."
        ],
        "dos": [
            "Keep airway clear and loosen tight neck clothing.",
            "Ask a bystander to wave and guide the ambulance crew at the building entrance.",
            "Note the exact time symptoms started."
        ],
        "donts": [
            "DO NOT administer food, water, or medicine to an unconscious person.",
            "DO NOT crowd the victim - maintain fresh air circulation."
        ]
    },
    IncidentType.FIRE: {
        "immediate": [
            "Pull the nearest manual fire alarm pull station immediately.",
            "Evacuate via stairs immediately — NEVER USE ELEVATORS.",
            "Feel door handles before opening: if warm or hot, DO NOT OPEN; seek alternate exit.",
            "Stay low to the floor where air is cleaner if smoke is present.",
            "Proceed directly to the designated Assembly Point (Grand Athletic Ground or North Lawn)."
        ],
        "dos": [
            "Close doors behind you to compartmentalize smoke and flames.",
            "Alert others in your floor corridor as you evacuate safely."
        ],
        "donts": [
            "DO NOT stop to collect personal belongings or laptops.",
            "DO NOT re-enter the building until official 'All Clear' is signaled by Security."
        ]
    },
    IncidentType.SECURITY: {
        "immediate": [
            "If in danger, run to a safe area or lock yourself in a secure room.",
            "Lock and barricade doors, turn off lights, and silence mobile phones.",
            "Stay out of sight from windows and doors.",
            "Campus Security and local police have been alerted to your exact GPS coordinates."
        ],
        "dos": [
            "Keep hands visible and follow responder directions when units arrive.",
            "Share suspect descriptions (height, clothing, direction of flight) if safe to do so."
        ],
        "donts": [
            "DO NOT confront an aggressive or armed individual.",
            "DO NOT spread unverified rumors on social media."
        ]
    },
    IncidentType.ACCIDENT: {
        "immediate": [
            "Ensure the surrounding scene is safe from traffic, electrical wires, or falling debris.",
            "Apply direct, firm pressure with a clean cloth if there is active bleeding.",
            "Immobilize injured limbs — do not attempt to straighten broken bones.",
            "Keep the victim warm with a jacket to prevent medical shock."
        ],
        "dos": [
            "Talk reassuringly to the victim to keep them awake and conscious.",
            "Keep the pathway clear for the stretcher team."
        ],
        "donts": [
            "DO NOT remove deeply embedded objects; stabilize them in place.",
            "DO NOT let the injured person walk or stand up abruptly."
        ]
    },
    IncidentType.HAZARD: {
        "immediate": [
            "Evacuate upwind and uphill from the hazardous leak, chemical vapor, or exposed wire.",
            "Do not switch lights on/off or ignite lighters if flammable gas is suspected.",
            "Alert lab marshalls and facilities maintenance team.",
            "Await Hazmat safety unit arrival."
        ],
        "dos": [
            "Flush chemical contact with eyes or skin at nearest eyewash/shower for 15 minutes.",
            "Warn arriving students away from the contaminated area."
        ],
        "donts": [
            "DO NOT attempt to clean up unknown chemical spills yourself."
        ]
    },
    IncidentType.GENERAL: {
        "immediate": [
            "Stay in a well-lit public area and await coordinator acknowledgment.",
            "Provide clear room and floor specifics to responders via the app."
        ],
        "dos": [
            "Keep your phone line open for responder callback."
        ],
        "donts": [
            "DO NOT panic; campus coordinators are tracking your beacon."
        ]
    }
}
