## IT-Grundschutz Kompendium Toolset

Dieses Repository enthaelt eine Python-CLI und eine Tkinter-GUI, mit denen du die offiziellen IT-Grundschutz-Anforderungen aus der DocBook/XML-Version des Kompendiums durchsuchen, bewerten und kommentieren kannst. Zu jeder Anforderung kannst du Status und Notiz erfassen; die Anwendung erzeugt zugleich automatisch Praxis-Impulse, die bei der Umsetzung helfen.

> **Wichtig:** Lade die benoetigte XML-Datei selbst herunter (Platzhalter-URL: `https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium/XML_Kompendium_2023.xml`) und speichere sie z. B. als `XML_Kompendium_2023.xml` im Projekt. Alternativ kannst du den Pfad ueber `--xml` setzen.

### Voraussetzungen und Start

Python 3.10 oder neuer reicht aus, Zusatzpakete sind nicht erforderlich.

```powershell
python app.py --help
```

### CLI-Befehle

- `python app.py modules` - listet alle Bausteine mit erledigten/offenen Anforderungen.
- `python app.py requirements APP.1.1` - zeigt Anforderungen eines Bausteins, optional mit `--status done`.
- `python app.py show APP.1.1.A3` - Detailansicht inklusive Praxis-Impulse.
- `python app.py set-status APP.1.1.A3 done --note "..."` - Status und Kommentar pflegen.
- `python app.py statuses` - zeigt alle gepflegten Statuswerte (Filter per `--status` moeglich).

Standardmaessig nutzt die CLI `XML_Kompendium_2023.xml` im Projektordner und schreibt Fortschritte in `status.json`. Beide Pfade lassen sich mit `--xml` bzw. `--status-file` anpassen.

### Grafische Oberflaeche

```powershell
python gui.py
```

Die GUI zeigt links die Bausteine (mit Fortschritt), rechts die Anforderungen. Ein Dropdown erlaubt das Filtern nach Status. Beim Anklicken einer Anforderung siehst du Beschreibung, Praxis-Impulse sowie Felder zum Setzen von Status und Kommentar. Saemtliche Aenderungen landen ebenfalls in `status.json`, sodass CLI und GUI jederzeit denselben Datenstand nutzen.

### Praxis-Impulse

Zu jeder Anforderung erzeugt das Toolset mehrere Hinweise:

1. Einordnung anhand des Anforderungslevels (Basis, Standard, Hoch) mit erwarteten Massnahmen.
2. Erinnerung an die beteiligten Rollen laut Kompendium.
3. Keyword-basierte Tipps (z. B. Planung, Konfiguration, Monitoring, Notfall, Dokumentation).
4. Bis zu zwei Saetze aus dem Originaltext als direkt umsetzbare Handlungsempfehlung.

So erhaeltst du sofort Ideen, wie du jeden Punkt organisatorisch, technisch oder dokumentarisch angehen kannst. Eigene Notizen kannst du jederzeit ergaenzen.

### Statuswerte

- `open` - noch nicht gestartet
- `in_progress` - in Bearbeitung
- `done` - umgesetzt und geprueft
- `not_applicable` - nachvollziehbar nicht relevant

Alle Angaben werden in `status.json` gespeichert (JSON-Format) und koennen daher versioniert oder fuer Audits exportiert werden.
