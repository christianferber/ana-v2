# ANA 2.049

<!-- Änderung 2.049: Aktuelle Quellversion mit modernisierter Oberfläche kennzeichnen. -->

Automatische Nahwärme-Abrechnung für Windows.

<!-- Änderung für v2: Installation, Python-Start, Windows-Build und lokale Prüfungen dokumentieren. -->

## Windows-Paket starten

Das Windows-ZIP vollständig in einen beschreibbaren Ordner entpacken und `ANA.exe`
im Unterordner `ANA` starten. `_internal` muss neben der EXE erhalten bleiben.
Das Paket enthält keine Mitglieds-, Konto-, Zähler- oder Abrechnungsdaten.
Über das Zahnradsymbol den Arbeitsordner einstellen und die Anwendung danach neu starten.
Für Word-/PDF-Ausgaben wird eine lokale Microsoft-Word-Installation benötigt.
Das native Fenster verwendet Microsoft Edge WebView2; bei fehlender Laufzeit muss diese installiert werden.
Vor dem Einsatz mit produktiven Daten eine separate Datensicherung erstellen.

## Mit Python starten

Geprüfte Umgebung: Windows, Python 3.13.5. Befehle im Projektordner ausführen:

```powershell
python -m pip install -r requirements.txt
Copy-Item konfiguration/ana.example.ini ana.ini
python ana_start.py
```

Eine bereits vorhandene `ana.ini` beibehalten. Alternativ ist im Projektordner
weiterhin `python ana.py` möglich. Die Beispielkonfiguration verwendet zunächst
den Programmordner als Arbeitsordner. In einer leeren Datenumgebung vor dem
ersten Start `Datenbank`, `Sicherungen`, `Logs`, `Downloads`, `Abrechnungen`,
`Rückvergütungen` und `Vorlagen` als Ordner anlegen.

## Windows-EXE erstellen

```powershell
python -m pip install -r requirements-build.txt
python -m scripts.build_windows
```

Ergebnis: `release/ANA-2.00-Windows-x64.zip`. Die Anwendung wird als Ordnerpaket
mit EXE und Laufzeitdateien erzeugt. Lokale INI-Dateien, Beispieldaten und Testausgaben
werden nicht in das Paket übernommen.

## Lokale Verifikation

Die Prüfprogramme erwarten Ausgangsversion und Beispieldaten in den lokal
festgelegten Nachbarverzeichnissen. `ana.ini` muss auf den freigegebenen
Beispieldatenordner zeigen. Referenzen und Ausgaben liegen ausschließlich unter `.lokal/`.

```powershell
python -m scripts.freigabe_pruefen
```

Vor einem Oberflächentest eine laufende ANA-Instanz beenden. Oberflächentests
verwenden eine separate lokale Datenkopie und eine lokale Chrome-Installation.
Sie geben keine Inhalte der Beispieldaten aus.

```powershell
python -m tests.oberflaeche_pruefen
python -m tests.oberflaeche_pruefen --rueckverguetung
```

Bei der Rückvergütung verwendet der Praxistest einen vorhandenen Datensatz;
der Berechnungsvergleich prüft alle vorhandenen Referenzfälle.
<!-- Änderung: Anwenderinformationen, technische Details und Prüfungen getrennt verlinken. -->
Features und Fehlerkorrekturen für Anwender stehen in den
[Release Notes](RELEASE_NOTES.md), technische Einzelheiten im
[Änderungsprotokoll](docs/AENDERUNGSPROTOKOLL.md) und Prüfungen einschließlich
ihrer Grenzen im [Prüfbericht](docs/TESTBERICHT.md).

## Verzeichnisstruktur

<!-- Änderung für v2: Quellcode, Tests, Werkzeuge und Ressourcen getrennt erläutern. -->

```text
ana-v2/
├── ana.py                 # Start mit python ana.py
├── ana_start.py           # Start für die Windows-Paketierung
├── anwendung/             # Oberfläche, Berechnungen und Fachmodule
├── tests/                 # Lokale Referenz- und Praxistests
├── scripts/               # Windows-Build und gebündelte Freigabeprüfung
├── ressourcen/            # Logos und Icons
├── konfiguration/         # Neutrale Beispielkonfiguration
├── docs/                  # Strukturübersicht und aktueller Prüfbericht
├── .lokal/                # Lokale Referenzen, Protokolle und Testausgaben
├── build/                 # Temporäre Builddateien
├── dist/                  # Erzeugte Windows-Anwendung
└── release/               # Freigabearchive und Prüfsummen
```

Die aktive `ana.ini` bleibt lokal im Projektordner. `.lokal/`, aktive Einstellungen
und Buildausgaben sind von Git ausgeschlossen. Details stehen in
[`docs/STRUKTUR.md`](docs/STRUKTUR.md); der aktuelle Prüfbericht in
[`docs/TESTBERICHT.md`](docs/TESTBERICHT.md).

Ein Build in einem separaten Zielordner ersetzt keine vorhandenen Freigabepakete:

```powershell
python -m scripts.build_windows --ausgabe .lokal/struktur-build
```
