# Technisches Änderungsprotokoll

<!-- Änderung: Technische Details aus den Endbenutzer-Release-Notes hierher verschoben. -->

Dieses Protokoll dokumentiert interne Umbauten, technische Fehlerkorrekturen,
Testanpassungen und die Bereitstellung je Version. Die folgenden bisherigen
Einträge wurden vollständig aus den Release Notes übernommen; Prüfaussagen
beschreiben den jeweiligen damaligen Stand. Aktuelle Prüfungen stehen im
[Prüfbericht](TESTBERICHT.md).

Für Endbenutzer bestimmte Features, Verbesserungen und Fehlerkorrekturen stehen
in den [Release Notes](../RELEASE_NOTES.md).

## Pflege der Änderungsdokumentation

- `RELEASE_NOTES.md`: Änderungen beschreiben, die Anwender bei Bedienung oder
  Ergebnissen bemerken; wie bei Version 1.x mit `Feature:`, `Verbesserung:` oder
  `Bugfix:` kennzeichnen. Interne Umbauten nicht als neue Funktionen darstellen.
- `docs/AENDERUNGSPROTOKOLL.md`: Module, Implementierung, Tests, Versionierung und
  Bereitstellung mit der zugehörigen Version dokumentieren.
- `docs/TESTBERICHT.md`: Durchgeführte Prüfungen und deren Grenzen festhalten.

## Version 2.033 – 06.11.2026

<!-- Änderung 2.033: Technische Auslagerung getrennt von Anwenderhinweisen festhalten. -->
- Zähleroberfläche nach `anwendung/zaehler_ui.py` ausgelagert: Import,
  Sortierung, Prüfung, Korrekturdialoge, Tabellenbearbeitung und Speichern.
- `ZaehlerOberflaeche` verwaltet Tabellen- und Dialogzustand. Gemeinsame
  Datenbanken und Hilfen bleiben auf der Anwendung; Adapter erhalten Aufrufe
  und refresh-Zugriffe. Programmlogik und Dialogtexte bleiben unverändert.
- Strukturvergleich umfasst alle verschobenen Methoden und Adapter.
  Gebundene Methoden werden mit lokalen Beispieldaten gegen das Original
  geprüft, einschließlich Import, Überschreiben, Formatabweisung,
  Fehlwertdialogen und byteidentischer CSV-Speicherung.
- Quellfreigabe gemäß Freigabeprozess; keine Windows-EXE erstellt.
- Vollständiger Praxislauf: Zählerregister, Abrechnung, CSV-Referenz und
  73 Word-/PDF-Paare bestanden. Word-Paketinhalte, PDF-Seitenzahlen und
  Texte gegenüber dem vorherigen Praxislauf identisch; Originalbestand
  unverändert. Testprozesse vollständig beendet; keine visuelle Layoutprüfung.

## Überarbeitung der Dokumentation – 06.11.2026

- Einträge für Version 2.x in den Release Notes auf Anwenderinformationen gekürzt.
- Bisherige technische Einträge unverändert in dieses Protokoll übernommen.
- Einträge für Version 1.x unverändert beibehalten und Dokumentationsverweise ergänzt.
- Reine Dokumentationsänderung ohne neue Programmversion oder Windows-EXE.

Version 2.032 – 06.11.2026
-------------------------

- Oberflächentests schließen App, Fenster und Browser einschließlich aller Unterprozesse.
- Windows-Prozessgruppe räumt nach Erfolg, Fehler und Abbruch auf.
- Eine Betriebssystem-Sperre verhindert parallele Oberflächentests.
- Vor dem Start werden vorhandene ANA-Instanzen beendet und der Zustand kontrolliert.
- Verhalten mit echten verwaisten Testprozessen und konkurrierendem Teststart geprüft.
- Keine Änderung der Fachlogik; keine neue EXE.

Version 2.031 – 06.11.2026
-------------------------

- Abschlagsoberfläche in `anwendung/abschlag_ui.py` ausgelagert.
- Tabelle und Speichern-Schaltfläche gehören zur Ansicht; gemeinsam genutzte Daten bleiben in der Anwendung.
- Bestehende Einstiegspunkte und aktualisierbare Tabellen- und Statusanzeigen erhalten.
- Spaltendefinitionen, Bearbeiten, Upload und CSV-Speicherung gegen Original geprüft.
- Versionsschritt um 0.001 gemäß aktueller Projektvorgabe.
- Sieben Freigabeprüfungen sowie Abschlagstabelle und vollständiger Abrechnungslauf bestanden.
- 73 Word-Dateien und 73 lesbare PDFs neu erzeugt; CSV-Referenz identisch, Originaldaten unverändert.
- Quellfreigabe ohne neue EXE.

Version 2.03 – 06.11.2026
------------------------

- Abrechnungsoberfläche in `anwendung/abrechnung_ui.py` ausgelagert.
- Eigener Tabellen- und Bedienzustand einschließlich Speicherdialogen,
  Mindestabnahme-Nachfragen und Plausibilitätsprüfung.
- Gemeinsame Datenbanken und Einstellungen bleiben in der Anwendung verfügbar.
- Berechnungen, Rundungen, Speichern, CSV-Download und Word-/PDF-Ablauf beibehalten.
- Referenzprüfung führt echte Instanzmethoden aus; Strukturprüfung umfasst auch
  verschachtelte Dialogfunktionen und den asynchronen Speicherablauf.

Version 2.02 – 06.11.2026
------------------------

- Rückvergütungsoberfläche und Dialoge in `anwendung/rueckverguetung_ui.py` ausgelagert.
- Eigener Bereichszustand für Tabellen und Bedienelemente statt globaler Variablen.
- Gemeinsame Pfade und Einstellungen werden weiterhin aus der Anwendung gelesen.
- Berechnungen, Speichern, CSV-Download und Word-/PDF-Ablauf bleiben erhalten.
- Referenzprüfung auf echte Instanzmethoden umgestellt; Strukturvergleich erweitert.

Version 2.01 – 06.11.2026
------------------------

- Rückvergütung: Eine eigene Word-Sitzung für den vollständigen PDF-Stapel verwenden.
- Dokument, Word und COM auch bei Konvertierungsfehlern zuverlässig freigeben.
- Berechnungen, CSV-Ausgabe, Word-Felder, Dateinamen und Dateiauswahl bleiben erhalten.
- Dokumenttests für gemeinsame Word-Sitzung und Fehlerbehandlung ergänzt.

Version 2.00 – 05.11.2026
------------------------

- Aktualisierte Freigabe 2.00: Die neue Verzeichnisstruktur ersetzt die bisherige Bereitstellung derselben Version.
- Projektstruktur: Anwendungsmodule, Tests, Skripte, Ressourcen, Beispielkonfiguration und Dokumentation in eigene Verzeichnisse eingeordnet.
- Der Start mit `python ana.py` bleibt erhalten; Test- und Buildaufrufe verwenden Python-Pakete.
- Ressourcenpfade für Python und Windows-Paket angepasst; Berechnungen und Datenformate unverändert.
- Architektur: CSV-Dateizugriffe, INI-Zugriffe und Pfadbildung in eigene Module ausgelagert.
- Architektur: Abrechnungs- und Rückvergütungsberechnung von der Oberfläche getrennt.
- Architektur: Word-/PDF-Verarbeitung, Feldformatierung und CSV-Buchungsvorlagen ausgelagert.
- Bestehende Formeln, Rundungen und Datenformate durch lokale Referenzvergleiche abgesichert.
- Bugfix: Rückvergütungs-Nettoexport wandelt CSV-Text vor der Multiplikation in Decimal um.
- Bugfix: Rückvergütungs-Bruttoexport verwendet bei Zwischenablesung „Rückvergütung gesamt“.
- Bereitstellung: Python-Start und Windows-Build mit neutraler Startkonfiguration dokumentiert.
- Datenschutz: Beispieldaten, lokale Konfiguration und Referenzausgaben werden nicht veröffentlicht.
- Prüfung: Lokale Berechnungs-, CSV-, Struktur- und Dokumenttests; erfolgreiche Oberflächen-Praxistests
  einschließlich Speichern und echter Word-/PDF-Erstellung mit ausgewählten Beispieldatensätzen.
- Prüfgrenze: Der vollständige Rückvergütungs-Dokumentlauf überschritt das Testzeitlimit;
  der Praxistest mit einem vorhandenen Datensatz war erfolgreich. Keine visuelle Dokumentprüfung im KI-Kontext.

