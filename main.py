from pathlib import Path
import json
import os
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

# Vercel KV (Upstash) REST API configuration
KV_REST_API_URL = os.getenv("KV_REST_API_URL")
KV_REST_API_TOKEN = os.getenv("KV_REST_API_TOKEN")
KV_KEY = "exclusion_rules"
KV_ENABLED = bool(KV_REST_API_URL and KV_REST_API_TOKEN)

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

def load_rules() -> dict:
    """Load rules from file and overlay KV-stored exclusions if available."""
    rules = load_exclusion_rules(EXCLUSION_RULES_FILE)

    if KV_ENABLED:
        try:
            response = requests.get(
                f"{KV_REST_API_URL}/get/{KV_KEY}",
                headers={"Authorization": f"Bearer {KV_REST_API_TOKEN}"},
                timeout=5,
            )
            response.raise_for_status()
            result = response.json().get("result")
            if result:
                excluded = json.loads(result)
                if isinstance(excluded, list):
                    rules["always_excluded"] = excluded
        except Exception:
            # Fall back to file-based rules if KV is unavailable
            pass

    return rules


def save_exclusions(excluded_modules: list) -> None:
    """Save exclusions to KV when configured; otherwise write to file."""
    if KV_ENABLED:
        payload = json.dumps(excluded_modules, ensure_ascii=False)
        response = requests.post(
            f"{KV_REST_API_URL}/set/{KV_KEY}",
            headers={
                "Authorization": f"Bearer {KV_REST_API_TOKEN}",
                "Content-Type": "text/plain; charset=utf-8",
            },
            data=payload.encode("utf-8"),
            timeout=8,
        )
        if not response.ok:
            raise RuntimeError(f"KV set failed: {response.status_code} {response.text}")
        return

    current_rules = load_exclusion_rules(EXCLUSION_RULES_FILE)
    current_rules["always_excluded"] = excluded_modules
    with open(EXCLUSION_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(current_rules, f, ensure_ascii=False, indent=2)


def save_rules(rules: dict) -> None:
    """Save complete rules (including time_based_exclusions) to file."""
    with open(EXCLUSION_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def fetch_modules_from_rapla() -> list:
    """Fetch all modules from RAPLA and extract unique event summaries.
    
    Returns:
        List of unique module names found in the calendar.
    """
    try:
        r = requests.get(ICAL_URL, timeout=15, headers={"User-Agent": "vital/1.0"})
        r.raise_for_status()
        cal = Calendar.from_ical(r.text)
        
        modules = set()
        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary', '')).strip()
                if summary:
                    modules.add(summary)
        
        return sorted(list(modules))
    except Exception as e:
        raise RuntimeError(f"Module-Fetch von RAPLA fehlgeschlagen: {e}")


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
        rules = load_rules()
    
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
    current_rules = load_rules()
    return jsonify(current_rules)


@app.route("/api/save-preferences", methods=['POST'])
def save_preferences():
    """API-Endpoint: Speichert die Benutzereinstellungen."""
    data = request.get_json()
    excluded_modules = data.get('excluded_modules', [])
    
    try:
        save_exclusions(excluded_modules)
    except Exception as exc:
        return jsonify({
            'success': False,
            'message': f'Speichern fehlgeschlagen: {exc}'
        }), 500
    
    return jsonify({
        'success': True,
        'message': 'Preferenzen gespeichert'
    })


@app.route("/api/refresh-modules", methods=['POST'])
def refresh_modules():
    """API-Endpoint: Aktualisiert die Modulliste von RAPLA."""
    try:
        # Hole alle verfügbaren Module von RAPLA
        new_modules = fetch_modules_from_rapla()
        
        # Lade aktuelle Regeln (behält always_excluded bei)
        current_rules = load_rules()
        
        # Initialisiere time_based_exclusions falls leer
        if not current_rules.get('time_based_exclusions'):
            current_rules['time_based_exclusions'] = [
                {
                    "description": "Dies ist nur für die Modul-Liste. Die Zeit-Filterung ist deaktiviert.",
                    "start_date": "2025-01-01",
                    "end_date": "2099-12-31",
                    "events": []
                }
            ]
        
        # Merge mit bestehenden Modulen (keine Duplikate)
        existing_modules = set(current_rules['time_based_exclusions'][0].get('events', []))
        all_modules = sorted(list(existing_modules.union(set(new_modules))))
        
        current_rules['time_based_exclusions'][0]['events'] = all_modules
        
        # Speichere aktualisierte Regeln
        save_rules(current_rules)
        
        return jsonify({
            'success': True,
            'message': f'Module aktualisiert: {len(all_modules)} Module gefunden',
            'module_count': len(all_modules)
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'message': f'Modul-Refresh fehlgeschlagen: {exc}'
        }), 500


@app.route("/download-ics")
def download_ics():
    """Download: Gefilterte ICS-Datei herunterladen."""
    # Aktuelle Regeln laden
    current_rules = load_rules()
    
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
    current_rules = load_rules()
    
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