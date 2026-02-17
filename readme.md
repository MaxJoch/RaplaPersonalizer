# 🎓 RAPLA DHBW Personalizer

Ein Python-Flask-Tool zur Filterung und Anpassung von RAPLA-Stundenplan-Kalender an der DHBW Karlsruhe. Es ermöglicht das selektive Ausblenden von Feiertagen, Klausurwochen und weiteren unerwünschten Events basierend auf konfigurierbaren Regeln.

## ✨ Features

- **Automatische Event-Filterung**: Entfernt Feiertage und andere unerwünschte Termine automatisch
- **Zeitbasierte Ausschlussregeln**: Definiere Termine, die nur in bestimmten Zeiträumen ausgeblendet werden sollen
- **JSON-Konfiguration**: Einfache, wartbare Konfiguration über `exclusion_rules.json`
- **iCal-Kompatibilität**: Arbeitet mit Standard-iCal-Formaten für volle Kalender-Kompatibilität
- **Flask-REST-API**: Stellt gefilterte Kalender über HTTP-Endpoint bereit

## 🚀 Installation

**Voraussetzungen:**
- Python 3.8+
- pip

**Schritt-für-Schritt:**

```bash
# Repository klonen
git clone https://github.com/yourusername/rapla_dhbw_personalizer.git
cd rapla_dhbw_personalizer

# Dependencies installieren
pip install -r requirements.txt

# Anwendung starten
python main.py
```

Die Anwendung läuft dann auf `http://localhost:8000`

## 📋 Konfiguration

Der gefilterte Kalender wird über `exclusion_rules.json` konfiguriert:

```json
{
  "always_excluded": [
    "Feiertag 1",
    "Feiertag 2"
  ],
  "time_based_exclusions": [
    {
      "description": "Beispiel: Auslandsaufenthalt",
      "start_date": "2026-02-16",
      "end_date": "2026-05-17",
      "events": [
        "Vorlesung 1",
        "Vorlesung 2"
      ]
    }
  ]
}
```

**Struktur:**
- `always_excluded`: Liste von Events, die immer ausgeblendet werden (z.B. Feiertage)
- `time_based_exclusions`: Events, die nur in definierten Zeiträumen ausgeblendet werden
  - `start_date` / `end_date`: Zeitraum (Format: YYYY-MM-DD)
  - `events`: Liste der auszublendenden Ereignisse in diesem Zeitraum

## 📡 API-Endpoints

**GET `/TINF23B6.ics`**
Gibt den gefilterten Stundenplan als iCal-Datei zurück. Die URL kann direkt in Calendar-Apps (iCal, Google Calendar, Outlook) abonniert werden.

```bash
curl http://localhost:8000/TINF23B6.ics > stundenplan.ics
```

## 🔧 Verwendung mit Kalender-Apps

1. Kopiere die URL: `http://yourdomain.com/TINF23B6.ics`
2. Füge sie in deine Kalender-App ein (Google Calendar, Outlook, Apple Calendar, etc.)
3. Der Stundenplan wird automatisch gefiltert und aktualisiert

## 📦 Dependencies

- **Flask**: Web-Framework für REST-API
- **icalendar**: iCal-Datei-Verarbeitung
- **requests**: HTTP-Anfragen an RAPLA
- **gunicorn**: Production-WSGI-Server

Siehe [requirements.txt](requirements.txt)

## 🛠️ Deployment

**Mit Gunicorn (Production):**

```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

**Mit Docker (optional):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

## 📝 Lizenz

MIT License - siehe LICENSE-Datei für Details

## 👤 Autor

Max Joch

## 🤝 Contributing

Contributions sind willkommen! Bitte erstelle einen Pull Request mit deinen Verbesserungen.
