# 🎓 RAPLA DHBW Personalizer

Ein kleines Flask-Tool, das deinen RAPLA-Stundenplan personalisiert. Du kannst im Web-UI Module ausblenden und dir den gefilterten Kalender als `.ics` herunterladen oder per URL abonnieren.

## ✨ Features

- Weboberflaeche zum Ein- und Ausblenden von Modulen
- iCal-Export und Abonnement-URL
- Einfache Konfiguration ueber `exclusion_rules.json`
- Optional: Persistente Speicherung ueber Vercel KV

## 🚀 Lokaler Start

```bash
git clone https://github.com/yourusername/rapla_dhbw_personalizer.git
cd rapla_dhbw_personalizer
pip install -r requirements.txt
python main.py
```

Die App laeuft unter `http://localhost:8000`.

## ✅ Bedienung

- **Angehakt** = Modul wird **nicht** im Kalender angezeigt
- **Nicht angehakt** = Modul bleibt im Kalender

Nach dem Speichern wird der Kalender sofort gefiltert.

## 📡 Kalender-Links

- Download: `http://localhost:8000/download-ics`
- Abonnement: `http://localhost:8000/TINF23B6.ics`

Das Abonnement aktualisiert sich automatisch, sobald du Module speicherst (je nach Kalender-App meist alle paar Stunden).

## 📋 Modul-Liste

Die Liste der Module wird aus `exclusion_rules.json` gelesen:

```json
{
  "always_excluded": [],
  "time_based_exclusions": [
    {
      "description": "Nur fuer die Modul-Liste",
      "start_date": "2025-01-01",
      "end_date": "2099-12-31",
      "events": [
        "Recht",
        "Grundlagen KI (aus KI und BV)"
      ]
    }
  ]
}
```

Die App nutzt aktuell nur `always_excluded` fuer die Filterung. `time_based_exclusions` dient hier nur als Quelle fuer die Modul-Liste.

## ☁️ Vercel Deployment (mit KV)

Auf Vercel ist das Dateisystem read-only. Deshalb muss die Auswahl in Vercel KV gespeichert werden.

**Schritte:**
1. Vercel Dashboard -> Storage -> KV anlegen und verbinden
2. Diese Env-Variablen werden gesetzt:
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`
3. Redeploy oder Pushen

Ohne diese Variablen schreibt die App lokal weiter in `exclusion_rules.json`.

## 📦 Dependencies

- Flask
- icalendar
- requests
- gunicorn

Siehe [requirements.txt](requirements.txt)

## 📝 Lizenz

MIT License

## 👤 Autor

Max Joch