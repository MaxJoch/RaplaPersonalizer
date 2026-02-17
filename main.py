from pathlib import Path
import json
import re
from datetime import datetime

from flask import Flask, Response, render_template, jsonify, request
import requests
from icalendar import Calendar

app = Flask(__name__, template_folder='templates', static_folder='static')

# ============================================================================
# Configuration
# ============================================================================

# Original iCal source (Rapla link)
ICAL_URL = "https://rapla.dhbw-karlsruhe.de/rapla?page=iCal&user=li&file=TINF23B6"

# The exclusion rules now live in a JSON file for more flexibility
EXCLUSION_RULES_FILE = Path(__file__).with_name("exclusion_rules.json")

# ============================================================================
# Rapla Calendar Filtering (Time-Based Event Exclusions)
# ============================================================================

def load_exclusion_rules(file_path: Path) -> dict:
    """Load exclusion rules from JSON file.
    
    Expected format:
    {
        "always_excluded": ["event1", "event2", ...],
        "time_based_exclusions": [
            {
                "events": ["event3", "event4", ...],
                "start_date": "2025-09-22",
                "end_date": "2025-12-21",
                "description": "Optional description"
            }
        ]
    }
    """
    if not file_path.exists():
        return {"always_excluded": [], "time_based_exclusions": []}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

EXCLUSION_RULES = load_exclusion_rules(EXCLUSION_RULES_FILE)


def get_event_date(event):
    """Extract the date from an event component."""
    dtstart = event.get('dtstart')
    if dtstart:
        dt = dtstart.dt
        if isinstance(dt, datetime):
            return dt.date()
        return dt
    return None


def should_keep(event, rules=None) -> bool:
    """Check if an event should be kept based on exclusion rules.
    
    Args:
        event: The event component to check
        rules: Optional exclusion rules dict. If None, loads from file.
    
    Returns:
        True if event should be kept, False if it should be excluded.
    """
    if rules is None:
        rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    
    summary = str(event.get('summary', '')).strip().lower()
    
    # Check always excluded events
    for excluded_title in rules.get('always_excluded', []):
        if excluded_title.strip().lower() == summary:
            return False
    
    return True


# ============================================================================
# Flask Routes
# ============================================================================

@app.route("/")
def index():
    """Startseite mit Web-Oberfläche."""
    return render_template('index.html')


@app.route("/api/modules")
def get_modules():
    """API-Endpoint: Gibt alle verfügbaren Module und deren Status zurück."""
    # Aktuelle Regeln laden
    current_rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    return jsonify(current_rules)


@app.route("/api/save-preferences", methods=['POST'])
def save_preferences():
    """API-Endpoint: Speichert die Benutzereinstellungen."""
    data = request.get_json()
    excluded_modules = data.get('excluded_modules', [])
    
    # Aktuelle Regeln laden
    current_rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    
    # Always excluded mit neuen Werten aktualisieren
    current_rules['always_excluded'] = excluded_modules
    
    # Speichern
    with open(EXCLUSION_RULES_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_rules, f, ensure_ascii=False, indent=2)
    
    # Globale Regeln aktualisieren
    global EXCLUSION_RULES
    EXCLUSION_RULES = current_rules
    
    return jsonify({
        'success': True,
        'message': 'Preferenzen gespeichert'
    })


@app.route("/download-ics")
def download_ics():
    """Download: Gefilterte ICS-Datei herunterladen."""
    # Aktuelle Regeln laden
    current_rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    
    r = requests.get(ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
    cal = Calendar.from_ical(r.text)

    # Build filtered calendar based on exclusion rules
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)
    for component in cal.walk():
        if component.name == "VEVENT" and should_keep(component, current_rules):
            new_cal.add_component(component)

    return Response(
        new_cal.to_ical(),
        content_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=stundenplan.ics"}
    )


@app.route("/TINF23B6.ics")
def filtered_ics():
    """Rapla calendar with time-based event filtering."""
    # Aktuelle Regeln laden
    current_rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    
    r = requests.get(ICAL_URL, timeout=15, headers={"User-Agent":"vital/1.0"})
    cal = Calendar.from_ical(r.text)

    # Build filtered calendar based on exclusion rules
    new_cal = Calendar()
    for k, v in cal.items():
        new_cal.add(k, v)
    for component in cal.walk():
        if component.name == "VEVENT" and should_keep(component, current_rules):
            new_cal.add_component(component)

    return Response(new_cal.to_ical(), content_type="text/calendar")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)