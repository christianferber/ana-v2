# Projektstruktur

<!-- Änderung für v2: Zuständigkeiten und Aufrufe nach der Verzeichnisumstellung dokumentieren. -->

`ana.py` bleibt der einfache Einstiegspunkt. Die Oberfläche liegt in
`anwendung/oberflaeche.py`. `ana_start.py` unterstützt zusätzlich die
Windows-Paketierung und den Start unabhängig vom aktuellen Verzeichnis.

| Verzeichnis | Inhalt |
| --- | --- |
| `anwendung/` | Oberfläche, Berechnungen, CSV-Zugriffe, Einstellungen, Dokumentverarbeitung und Buchungsvorlagen |
| `tests/` | Berechnungs- und Referenzvergleiche, Strukturprüfung, CSV- und Dokumenttests sowie Oberflächentests |
| `scripts/` | Windows-Build und gebündelte lokale Prüfungen |
| `ressourcen/` | Logos und Icons; keine Arbeitsdaten |
| `konfiguration/` | Neutrale `ana.example.ini` ohne persönliche Pfade |
| `docs/` | Diese Übersicht und der aktuelle Prüfbericht |
| `.lokal/` | Nur lokale Referenzen, Protokolle und isolierte Testausgaben; nicht in Git |
| `build/`, `dist/`, `release/` | Erzeugte Builddateien, Windows-Anwendung und Freigabearchive; nicht in Git |

Die aktive `ana.ini` bleibt im Projektordner und wird nicht veröffentlicht.
<!-- Änderung 2.033: Zuständigkeit der Zähleransicht dokumentieren. -->
`anwendung/zaehler_ui.py` enthält Zählerimport, Sortierung, Datenprüfung,
Korrekturdialoge, Tabellenbearbeitung und Speichern. Bedienzustand liegt auf
der Ansicht; gemeinsame Daten bleiben auf der Anwendung. Adapter erhalten
bestehende Aufrufe und die aktualisierbare Tabellen- und Statusanzeige.

<!-- Änderung 2.03: Zuständigkeit der Abrechnungsansicht dokumentieren. -->
`anwendung/abrechnung_ui.py` enthält die Jahresabrechnung mit Speicherdialogen,
Mindestabnahme-Nachfragen, Plausibilitätsprüfung und Dokumentaufrufen. Der
Tabellen- und Bedienzustand gehört zur Ansicht; gemeinsame Datenbanken und
Einstellungen werden über die übergebene Anwendung verwendet. Das Hauptmodul
erzeugt die Ansicht und bindet die Jahresauswahl beim Registerwechsel an.

<!-- Änderung 2.02: Zuständigkeit der ausgelagerten Rückvergütungsansicht dokumentieren. -->
`anwendung/rueckverguetung_ui.py` enthält die Rückvergütungsoberfläche mit ihren
Dialogen und dem eigenen Tabellen- und Bedienzustand. Das Hauptmodul erzeugt
die Ansicht und ruft beim Registerwechsel die Jahresauswahl auf. Gemeinsame
Pfade, Einstellungen und Hilfsfunktionen werden über die übergebene Anwendung
verwendet; die Berechnungen bleiben im Berechnungsmodul.

Arbeitsdaten und Secrets bleiben außerhalb des Quellcodes. Die Namen der
Datenbankdateien sowie die Struktur des Arbeitsordners wurden nicht geändert.

Alle Befehle im Projektordner ausführen:

```powershell
python ana.py
python -m scripts.freigabe_pruefen
python -m tests.buchungsvorlagen_pruefen pruefen
python -m scripts.build_windows
```

Vor einem Oberflächentest eine laufende ANA-Instanz beenden. Die Referenztests
geben keine Inhalte der Beispieldaten aus. Die Verzeichnisumstellung ist ein
Bestandteil der aktualisierten Freigabe 2.00. Auf ausdrücklichen Benutzerwunsch
ersetzen der Versionstag und die Freigabepakete die bisherige Bereitstellung von 2.00.

## Prüfung der Umstellung am 05.11.2026

<!-- Änderung für v2: Tatsächlich durchgeführte Strukturprüfungen dokumentieren. -->

- Alle vorhandenen Referenz-, Berechnungs-, CSV-, Struktur- und Dokumenttests bestanden.
- Die Oberfläche startet aus dem neuen Anwendungspaket; beide Logos und das Favicon wurden über HTTP geladen.
- Ein separater Windows-Build unter `.lokal/struktur-build/` wurde erstellt und die EXE aus dessen ZIP gestartet.
- Natives Fenster, lokale Oberfläche und Versionsanzeige der EXE wurden bestätigt.
- Starttests verwendeten leere lokale Umgebungen und wurden anschließend beendet.
- Die Umstellung wurde zunächst getrennt von den veröffentlichten Archiven geprüft.
  Für die aktualisierte Freigabe 2.00 werden Quellarchiv, Windows-Paket, Prüfbericht und Prüfsummen ersetzt.

<!-- Änderung: Zuständigkeit der ausgelagerten Abschlagsansicht dokumentieren. -->
`anwendung/abschlag_ui.py` enthält Tabellenaufbau, Bearbeitung, Upload und Speichern
für Abschläge. Tabelle und Speichern-Schaltfläche liegen auf der Ansicht.
Gemeinsame Abschlagsdaten bleiben in der Anwendung. Kleine Adapter erhalten
bestehende Aufrufe einschließlich der aktualisierbaren Status- und Tabellenanzeige.

<!-- Änderung 2.032: Lebensdauer der Testprozesse dokumentieren. -->
`tests/testprozesse.py` sperrt parallele Oberflächentests und beendet vor dem Start
vorhandene ANA-Prozesse. Eine Windows-Prozessgruppe umfasst Test-App, natives
Fenster, Testbrowser und Unterprozesse. Sie wird nach Erfolg, Fehler und Abbruch
vollständig beendet; auch beim Ende des Testtreibers schließt Windows den Job.
`tests/testprozesse_pruefen.py` prüft echte verwaiste Kinder und konkurrierende Starts.

<!-- Änderung: Getrennte Dokumentation für Anwender und technische Wartung erläutern. -->
`RELEASE_NOTES.md` beschreibt Features, Verbesserungen und Fehlerkorrekturen für
Anwender. `docs/AENDERUNGSPROTOKOLL.md` enthält die technischen Details pro Version;
`docs/TESTBERICHT.md` dokumentiert die Prüfungen und ihre Grenzen.

<!-- Änderung 2.034: Zuständigkeit der Abnehmeransicht dokumentieren. -->
`anwendung/abnehmer_ui.py` enthält Tabellenaufbau, CSV-Upload, Bearbeitung und
Speichern der Abnehmerdaten. Tabelle und Speichern-Schaltfläche gehören zur
Ansicht; gemeinsame Abnehmer- und Abschlagsdaten bleiben auf der Anwendung.
Die bisherigen Aufrufe und refresh-Zugriffe bleiben über Adapter erhalten.

<!-- Änderung 2.035: Zuständigkeit der Mitgliederansicht dokumentieren. -->
`anwendung/mitglieder_ui.py` enthält Mitgliederverwaltung, Wartungsdialoge,
Anschlusswechsel, Tabellenfilter, Upload, Speichern sowie CSV-/Word-Export und
Serienbriefdialog. Gemeinsame Daten bleiben auf der Anwendung; Tabellen-,
Schaltflächen- und Dialogzustand liegt auf der Ansicht. Die bisherigen
Einstiegspunkte bleiben im Hauptmodul erhalten.

<!-- Änderung 2.036: Zuständigkeit der Kontodatenansicht dokumentieren. -->
`anwendung/kontodaten_ui.py` enthält Tabelle, Import, Laden, Bearbeiten und
Speichern der Kontodaten sowie den Registeraufbau für Buchungsvorlagen.
Die Ansicht besitzt Tabelle und Speichern-Schaltfläche; Kontodaten und
Exportauswahl bleiben gemeinsam auf der Anwendung verfügbar. Die bisherigen
CSV-Exportfunktionen und deren Speicherdialoge bleiben im Hauptmodul.

<!-- Änderung 2.037: Zuständigkeit der Werkzeugeansicht dokumentieren. -->
`anwendung/werkzeuge_ui.py` enthält die Werkzeugeansicht mit Ordnerauswahl,
ID-Ermittlung und PDF-Zusammenfügen. Beschriftungen und Hinweisfeld gehören
zur Ansicht, die bisherigen Ordnerpfade bleiben auf der Anwendung. Die
Einstiegspunkte im Hauptmodul bleiben über Adapter erhalten.

<!-- Änderung 2.038: Zuständigkeit der Einstellungsansicht dokumentieren. -->
`anwendung/einstellungen_ui.py` enthält Einstellungsdialoge, Arbeitsordnerauswahl,
Standard-Rücksetzung und Speichern. Eingabefelder und Dialogzustand gehören zur
Ansicht; Konfigurationswerte, Einlesen und Pfadbildung bleiben auf der Anwendung.
Die bisherigen Einstiegspunkte bleiben über Adapter erhalten.

<!-- Änderung 2.039: Zuständigkeit der Changelog-Ansicht dokumentieren. -->
`anwendung/changelog_ui.py` enthält Registeraufbau und gefilterte Markdown-Anzeige
für das Changelog. Anzeige- und Filterzustand liegt auf der Ansicht. Protokollpfad
und Schreibfunktionen bleiben auf der Anwendung; Adapter erhalten bestehende Aufrufe.

<!-- Änderung 2.040: Zuständigkeit des deaktivierten Statistikbereichs dokumentieren. -->
`anwendung/statistik_ui.py` enthält Auswahlfelder, CSV-Laden und Diagrammaufrufe
für den weiterhin deaktivierten Statistikbereich. Anzeigezustand gehört zur
Ansicht; Daten und Abrechnungspfad bleiben auf der Anwendung. Die bisherigen
Einstiegspunkte bleiben über Adapter erhalten; das Register wird nicht aktiviert.
