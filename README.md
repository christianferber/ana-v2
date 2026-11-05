# ANA 2.00

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
Copy-Item ana.example.ini ana.ini
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
python build_windows.py
```

Ergebnis: `release/ANA-2.00-Windows-x64.zip`. Die Anwendung wird als Ordnerpaket
mit EXE und Laufzeitdateien erzeugt. Lokale INI-Dateien, Beispieldaten und Testausgaben
werden nicht in das Paket übernommen.

## Lokale Verifikation

Die Prüfprogramme erwarten Ausgangsversion und Beispieldaten in den lokal
festgelegten Nachbarverzeichnissen. `ana.ini` muss auf den freigegebenen
Beispieldatenordner zeigen. Referenzen und Ausgaben liegen ausschließlich unter `.lokal/`.

```powershell
python referenz_pruefen.py pruefen
python berechnungen_pruefen.py
python rueckverguetung_pruefen.py pruefen
python buchungsvorlagen_pruefen.py pruefen
python dateihilfen_pruefen.py
python dokumente_pruefen.py
```

Vor einem Oberflächentest eine laufende ANA-Instanz beenden. Oberflächentests
verwenden eine separate lokale Datenkopie und eine lokale Chrome-Installation.
Sie geben keine Inhalte der Beispieldaten aus.

```powershell
python oberflaeche_pruefen.py
python oberflaeche_pruefen.py --rueckverguetung
```

Bei der Rückvergütung verwendet der Praxistest einen vorhandenen Datensatz;
der Berechnungsvergleich prüft alle vorhandenen Referenzfälle.
Weitere Änderungen und Prüfgrenzen stehen in `RELEASE_NOTES.md`.
