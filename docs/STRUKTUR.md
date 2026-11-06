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
