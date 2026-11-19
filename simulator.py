"""
Interactive Incident Simulator Engine for CampusShield Demos
Pre-configured with scenarios matching Aarambhathon presentation slides.
"""
from typing import Dict, List, Optional
from app.models import IncidentType, IncidentPriority, Coordinates, IncidentCreate

SIMULATION_PRESETS: Dict[str, Dict] = {
    "library_collapse": {
        "id": "library_collapse",
        "title": "Use Case: Student Collapses in Library at 9 PM (Aarambhathon Slide 6)",
        "type": IncidentType.MEDICAL,
        "priority": IncidentPriority.CRITICAL,
        "location_name": "Central University Library",
        "floor_room": "2nd Floor Silent Reading Room - Desk 42",
        "description": "Student suddenly collapsed while studying, unconscious and shallow breathing. Bystanders gathering.",
        "coords": {"lat": 28.5463, "lng": 77.1924},
        "reporter_name": "Rohan Verma (Student ID: 2024CS104)",
        "reporter_phone": "+91 98765 00101",
        "expected_responder": "resp_med_01",
        "narrative_steps": [
            "9:00 PM - Student loses consciousness at desk 42 in Central Library.",
            "9:00:15 PM - Bystander Rohan opens CampusShield and taps Medical SOS.",
            "9:00:18 PM - CampusShield auto-detects Library 2nd Floor GPS, triages as CRITICAL, alerts Ambulance-01 and Security-Beta.",
            "9:00:30 PM - Dr. Ananya acknowledges alert. Rohan sees 'Help is on the way' and CPR guidelines.",
            "9:01:10 PM - Ambulance departs Medical Center, live map updates with real-time ETA.",
            "9:03:00 PM - Foot Patrol Unit Beta arrives on site to secure corridor; Ambulance arrives 30s later.",
            "9:05:00 PM - Oxygen administered, vitals stabilized, student transported to Health Center. Incident Resolved."
        ]
    },
    "chemistry_lab_fire": {
        "id": "chemistry_lab_fire",
        "title": "Scenario 2: Chemistry Lab Flash Fire & Chemical Spill",
        "type": IncidentType.FIRE,
        "priority": IncidentPriority.CRITICAL,
        "location_name": "Science & Chemistry Block B",
        "floor_room": "Room 304 - Organic Synthesis Lab",
        "description": "Solvent flash fire near fume hood. Heavy white smoke in corridor. Lab evacuated.",
        "coords": {"lat": 28.5471, "lng": 77.1908},
        "reporter_name": "Prof. S. Mehra (Chemistry Faculty)",
        "reporter_phone": "+91 98123 45678",
        "expected_responder": "resp_fire_01",
        "narrative_steps": [
            "Flash fire ignited by ether spill in Room 304.",
            "Prof. Mehra activates CampusShield Fire Alarm.",
            "Immediate alert dispatched to Fire Safety Marshall Suresh and campus sirens.",
            "Automated evacuation guidance routes students to North Lawn Assembly Point.",
            "Fire Marshall deploys CO2 extinguisher; room ventilation shut off.",
            "All students accounted for at assembly point; incident safely closed."
        ]
    },
    "hostel_intruder_escalation": {
        "id": "hostel_intruder_escalation",
        "title": "Scenario 3: Hostel Night Intruder (Demo of Auto-Escalation Engine)",
        "type": IncidentType.SECURITY,
        "priority": IncidentPriority.HIGH,
        "location_name": "Aryabhatta Boys Hostel (North)",
        "floor_room": "Rear Boundary Wall - Gate 4",
        "description": "Unidentified person attempting to climb perimeter fence in dark alleyway.",
        "coords": {"lat": 28.5482, "lng": 77.1930},
        "reporter_name": "Amit Sharma (Hostel Warden)",
        "reporter_phone": "+91 99988 77665",
        "expected_responder": "resp_sec_alpha",
        "narrative_steps": [
            "Warden spots intruder and fires Security SOS.",
            "Primary unit assigned. Simulated delay tests escalation timer.",
            "Timer expires: Escalation Level 1 triggers buzzer reminder.",
            "Timer expires again: Escalation Level 2 auto-reroutes to backup Patrol Alpha and alerts Chief Security Officer.",
            "Security Patrol Alpha intercepts intruder at rear gate. Threat neutralized."
        ]
    },
    "sports_heatstroke": {
        "id": "sports_heatstroke",
        "title": "Scenario 4: Track Athlete Severe Heat Exhaustion",
        "type": IncidentType.ACCIDENT,
        "priority": IncidentPriority.MEDIUM,
        "location_name": "University Sports Arena & Track",
        "floor_room": "400m Track - East Bleachers",
        "description": "Athlete collapsed during 5K run. Severe dehydration and cramps, needs fluids & ice pack.",
        "coords": {"lat": 28.5440, "lng": 77.1895},
        "reporter_name": "Coach Balwinder Singh",
        "reporter_phone": "+91 98777 66554",
        "expected_responder": "resp_med_01",
        "narrative_steps": [
            "Coach reports heat exhaustion on sports track.",
            "Campus Health Center EMT dispatched with hydration electrolyte kit.",
            "In-app guidelines instruct coach on cooling techniques.",
            "Athlete recovers, incident closed."
        ]
    }
}
