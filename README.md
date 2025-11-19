## IT-Grundschutz Kompendium Toolset

Dieses Repository enthaelt eine Python-CLI und eine Tkinter-GUI, mit denen du das IT-Grundschutz-Kompendium (DocBook/XML) durchsuchen, Anforderungen bewerten und dazu passende KI-Hilfen abrufen kannst. Status- und Notizdaten werden lokal gespeichert.

> **Hinweis:** Lade die XML-Datei selbst von der BSI-Webseite herunter (z. B. `https://www.bsi.bund.de/.../XML_Kompendium_2023.xml?...`) und speichere sie als `XML_Kompendium_2023.xml` im Projekt. Alternativ gibst du den Pfad ueber `--xml` an.

### Voraussetzungen

Python 3.10+ reicht aus, zusaetzliche Pakete sind nicht erforderlich.

```powershell
python app.py --help
```

### CLI-Befehle

- `python app.py modules` – uebersicht aller Bausteine samt Fortschritt.
- `python app.py requirements APP.1.1` – Anforderungen eines Bausteins (optional `--status done`).
- `python app.py set-status APP.1.1.A3 done --note "..."` – Status/Notiz pflegen.
- `python app.py statuses` – alle gepflegten Statuswerte.
- `python app.py set-api-key --key sk-...` – OpenAI API-Key lokal speichern (alternativ ohne `--key`, dann wird nachgefragt).
- `python app.py ai-help APP.1.1.A3` – KI-Hilfe generieren; Ergebnis landet im lokalen Hilfe-Store und wird bei `show` angezeigt.

Standardpfade: `XML_Kompendium_2023.xml`, `status.json`, `openai_key.txt`, `ai_help_store.json`. Per `--xml`, `--status-file`, `--api-key-file`, `--ai-help-file` kannst du andere Dateien verwenden.

### GUI (inkl. KI-Hilfe)

```powershell
python gui.py
```

Features:
- Linke Liste: Bausteine mit Zahl erledigter Anforderungen.
- Rechte obere Liste: Anforderungen, filterbar nach Status.
- Detailansicht: Beschreibung, Statuspflege, KI-Hilfe-Bereich.
- Menue `Einstellungen > OpenAI API-Key hinterlegen` zum sicheren Speichern des API-Keys (nur lokal).
- Schaltflaeche „Hilfe laden“: ruft via OpenAI (Modell `gpt-4o-mini`) einen Umsetzungsvorschlag fuer die ausgewaehlte Anforderung ab und speichert ihn fuer spaetere Nutzung.

### KI-Hilfe & Speicherung

- API-Key liegt unverschluesselt in `openai_key.txt` (nicht einchecken!).
- Generierte Hilfen landen in `ai_help_store.json`, getrennt je Anforderungscode.
- In der CLI (`show ...`) sowie der GUI wird immer der zuletzt gespeicherte Text angezeigt; per Button/Command kannst du neue Antworten anfordern.

### Statuswerte

- `open` – noch nicht gestartet
- `in_progress` – in Bearbeitung
- `done` – umgesetzt und geprueft
- `not_applicable` – begruendet nicht relevant

Alle Angaben werden lokal als JSON gespeichert und koennen versioniert oder fuer Audits exportiert werden.



