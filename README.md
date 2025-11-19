## Kompendium-CLI

Dieses kleine Werkzeug erlaubt es, das `XML_Kompendium_2023.xml` direkt zu durchsuchen, jeden einzelnen IT-Grundschutz-Punkt mit einem Umsetzungsstatus zu versehen und sofort umsetzbare Praxis-Ideen abzurufen.

### Installation

Python 3.10+ genÃ¼gt, es werden keine zusÃ¤tzlichen Pakete benÃ¶tigt.

```powershell
python app.py --help
```

### Wichtige Befehle

- `python app.py modules` - listet alle Bausteine inkl. Anzahl erledigter Anforderungen.
- `python app.py requirements APP.1.1` - zeigt die Anforderungen des genannten Bausteins. Optional mit `--status done`.
- `python app.py show APP.1.1.A3` - Details, Beschreibungstext aus dem XML sowie automatisch generierte Praxis-Impulse.
- `python app.py set-status APP.1.1.A3 done --note "Technische Umsetzung per GPO"` - setzt Status und Kommentar.
- `python app.py statuses` - zeigt alle gepflegten Statuswerte (optional mit `--status in_progress`).

StandardmÃ¤ÃŸig wird `XML_Kompendium_2023.xml` im aktuellen Ordner genutzt und die Datei `status.json` fÃ¼r Fortschrittswerte angelegt. Beide Pfade kÃ¶nnen per `--xml` bzw. `--status-file` Ã¼berschrieben werden.

### Grafische OberflÃ¤che

FÃ¼r eine komfortable Bearbeitung steht zusÃ¤tzlich eine Tkinter-OberflÃ¤che bereit:

```powershell
python gui.py
```

Die OberflÃ¤che zeigt links alle Bausteine und rechts deren Anforderungen. Beim Anklicken einer Anforderung erscheinen Beschreibung, Praxis-Impulse sowie ein Dropdown zum Setzen des Status (inklusive Kommentar). Alle Ã„nderungen werden sofort im gleichen `status.json` gespeichert und kÃ¶nnen anschlieÃŸend auch Ã¼ber die CLI weiterbearbeitet werden. Mit `--xml` und `--status-file` kÃ¶nnen ebenfalls andere Dateien gesetzt werden.

### Praxis-ErlÃ¤uterungen

FÃ¼r jede Anforderung werden automatisch mehrere Hinweise erzeugt:

1. Einordnung nach Anforderungslevel (Basis, Standard, Hoch) mit konkreter Erwartung an Prozesse/Nachweise.
2. Einbindung der adressierten Rollen (falls im XML angegeben).
3. SchlÃ¼sselwort-basierte Tipps (Planung, Konfiguration, Monitoring, Notfall, Dokumentation usw.).
4. Bis zu zwei SÃ¤tze aus dem Originaltext als direkt umsetzbare Handlungsempfehlung.

Damit erhalten Sie fÃ¼r jeden Punkt sofort VorschlÃ¤ge, wie die Umsetzung in Projekten, Betrieb oder Dokumentation gestaltet werden kann. Eigene Notizen kÃ¶nnen Ã¼ber `set-status` ergÃ¤nzt werden.

### Statuswerte

Es stehen vier Statuswerte bereit:

- `open` - noch nicht gestartet
- `in_progress` - Bearbeitung lÃ¤uft
- `done` - umgesetzt und nachweisbar kontrolliert
- `not_applicable` - nachvollziehbar nicht anwendbar

Die Angaben werden im JSON-Format gespeichert und kÃ¶nnen z.â€¯B. fÃ¼r Audits versioniert werden.

