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

## Word-Fehlerbereinigung nach Version 2.047 – 10.11.2026

<!-- Änderung: Ressourcenfreigabe beim Abrechnungs-PDF-Export dokumentieren. -->

- Abrechnung verwendet `DispatchEx` für eine eigene Word-Instanz. Verschachtelte
  `finally`-Blöcke versuchen Dokumentabschluss und Word-Ende und geben COM frei.
  Leere Dateilisten starten Word nicht mehr. Dateifilter, Reihenfolge, PDF-Format,
  Dateinamen und Fortschrittswerte bleiben für vorhandene Dokumente unverändert.
- 20 Fehlersimulationen für beide PDF-Funktionen in die Freigabeprüfung aufgenommen.
  Der Strukturvergleich prüft den unveränderten Adapter; Dokumentaufrufvergleiche
  berücksichtigen ausschließlich neue Freigabe und leere Stapel.
- Version 2.047 und Versionsanzeige bleiben gemäß Benutzerwunsch unverändert.
  Keine neue EXE, kein neuer Versionstag oder Versionsrelease.
- UI-Fehlermeldungen, Parallelexportsperre, Mitgliederlisten und das Überdecken
  ursprünglicher Fehler durch fehlschlagendes Close/Quit sind nicht geändert.

## Bereinigung nach Version 2.047 – 09.11.2026

<!-- Änderung: Autorisierte Absicherung der Dateizugriffe bei unveränderter Fachlogik dokumentieren. -->

- CSV-Datei- und Datenbankspeicherung schreiben eine temporäre Datei im Zielordner,
  leeren den Schreibpuffer, führen `fsync` aus und ersetzen das Ziel mit `os.replace`.
  Aufbereitung, Standardkodierung und Zeilenenden bleiben erhalten. Temporäre Dateien
  werden bei Fehlern entfernt; die Ausnahme wird weitergegeben.
- Sicherungen werden zunächst in einem temporären Ordner vollständig kopiert und
  anschließend umbenannt. Erst danach werden alte Sicherungen bereinigt. Kollisionen
  bei gleicher Sekunde/Aktion erhalten einen nummerierten eigenen Ordner.
- Neue Regressionstests prüfen Teil-Schreibfehler, Synchronisations-/Austauschfehler,
  fehlende Zieldateien sowie Kopier- und Umbenennungsfehler. Referenzvergleiche bleiben
  für CSV-Inhalte erhalten; Strukturprüfungen berücksichtigen die autorisierten Änderungen.
- Dies schützt einzelne Dateizugriffe; mehrere zusammengehörige CSV-Dateien bilden
  weiterhin keine gemeinsame Transaktion. Separate Dialogexporte und INI-Schreiben
  sind nicht Teil dieser Änderung. Kein Nachweis gegen physische Datenträgerdefekte.

<!-- Änderung: Entfernung ungenutzter Altbestände bei unveränderter Version dokumentieren. -->

- Die nicht mehr verwendeten Funktionen `textarea_to_string`, `string_to_textarea`,
  `datum_mit_strich` und `tablefield_to_int` aus dem Hauptmodul entfernt.
- Der Strukturvergleich nimmt genau diese vier Originaldefinitionen aus und prüft
  ihre Entfernung. Alle übrigen Funktionen werden weiterhin verglichen.
- Aktive Text-, Datums- und Tabellenumwandlungen unverändert; insbesondere bleibt
  `tablefields_to_int` erhalten. Version und Versionsanzeige bleiben auf Benutzerwunsch
  unverändert. Keine neue EXE und kein neuer Versionsrelease.

## Version 2.047 – 09.11.2026

<!-- Änderung 2.047: Gemeinsame Mitgliederaktualisierung und Vergleichsprüfungen dokumentieren. -->

- `dbs_mitglieder_aktualisieren` in die bestehende Klasse `DatenbankZugriff`
  verschoben. Aktuelle Anwendungswerte ersetzen globale Zugriffe; der bisherige
  Einstiegspunkt und der Aufruf aus der Mitgliederansicht bleiben erhalten.
- Reihenfolge, verschachtelte ID-Suche, Änderungen an den bestehenden Zeilen,
  Speicherbedingungen sowie einzelne Speicher- und Ladeaufrufe unverändert.
  Unnötig gewordene `global`-Deklarationen entfallen beim Instanzzugriff.
- Strukturvergleich von Methode und Adapter ergänzt. Lokale Vergleichsfälle
  prüfen alle 16 Kombinationen der Dateistatuswerte, CSV-Dateien, Listenidentität,
  doppelte und unterschiedlich typisierte IDs, fehlende Treffer, leere Daten,
  Neuladen und Abbrüche bei Speicher-/Ladefehlern.
- Keine fachlichen Korrekturen und keine neue Windows-EXE.

## Version 2.046 – 09.11.2026

<!-- Änderung 2.046: Gemeinsame Exporthilfe und Vergleichsprüfung dokumentieren. -->

- `komma_datei_speichern` unverändert als asynchrone Methode von `ExportHilfe`
  nach `anwendung/exporthilfe.py` verschoben. CSV- und Dialoghilfen werden
  dynamisch von der Anwendung gelesen; der bisherige asynchrone Einstiegspunkt
  und die Aufrufe aus Abrechnung und Rückvergütung bleiben erhalten.
- Vollständiger Strukturvergleich von Methode, Adapter, Import und Initialisierung.
  Lokaler Beispieldatenvergleich prüft bytegleiche CSV-Dateien, unveränderte
  Eingaben, Dialogargumente, Benachrichtigungen, Abbruch und bisherige Fehler.
- Keine fachlichen Korrekturen und keine neue Windows-EXE.

## Version 2.045 – 08.11.2026

<!-- Änderung 2.045: Datenbankauslagerung und Vergleichsprüfungen dokumentieren. -->
- `db_datei_oeffnen` und `db_datei_speichern` nach `DatenbankZugriff` im vorhandenen
  Modul `anwendung/datenhaltung.py` verschoben. Zwei Adapter erhalten die bisherigen
  Aufrufe. Aktuelle Pfade und Dateihilfen werden über die Anwendung gelesen.
- Strukturvergleich der Funktionskörper, Adapter, Initialisierung und Importe
  erweitert. Buchungsreferenz verwendet den echten ausgelagerten Datenbankleser.
- Neuer lokaler Vergleich prüft Lesen, bytegleiches Schreiben, Eingabemutationen,
  Reihenfolge der sechs Ordneranlagen, Pfadwechsel mit derselben Instanz, fehlende
  und leere Dateien sowie bisherige Fehler bei leerer Tabelle und falschem Zieltyp.
- Alle 20 Freigabeprüfungen und Syntaxprüfung bestanden. Vollständiger regulärer
  Praxislauf mit normaler Word-Anbindung bestanden: 73 neue Word-Dateien und 73
  lesbare PDFs, CSV-Referenz identisch und Original-Beispieldaten unverändert.
  Gegen 2.044: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
  Keine verbliebenen ANA-, Word- oder Testbrowserprozesse. Keine neue EXE und
  keine visuelle Dokumentprüfung.

## Version 2.044 – 08.11.2026

<!-- Änderung 2.044: Auslagerung der Datenaufbereitung getrennt dokumentieren. -->
- Fünf unveränderte Funktionen nach `anwendung/datenaufbereitung.py` verschoben:
  `string_in_dict`, `listcsv_to_dict`, `jahr_in_datum`, `tablefields_to_dotfloat`
  und `tablefields_to_int`. Direkte Importe erhalten bisherige Namen und Aufrufe.
- Strukturvergleich um Funktionskörper und vollständige Importliste erweitert.
  Referenz- und Buchungstests verwenden die tatsächlichen importierten Funktionen.
- Neuer Vergleich mit lokalen Beispieldaten und Sonderfällen prüft Rückgabewerte,
  Eingabemutationen, Rückgabeidentität und bisheriges Fehlerverhalten gegen Original.
- Der separat festgestellte Anzeigefehler mit zwei Nachkommastellen bleibt unverändert.
- Alle 19 Freigabeprüfungen und Syntaxprüfung bestanden. Vollständiger regulärer
  Praxislauf mit normaler Word-Anbindung bestanden: 73 neue Word-Dateien und 73
  lesbare PDFs, CSV-Referenz identisch, Original-Beispieldaten unverändert.
  Gegen 2.043: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
  Testprozesse beendet. Keine visuelle Dokumentprüfung und keine neue EXE.

## Version 2.043 – 08.11.2026

<!-- Änderung 2.043: Gemeinsame Hilfen und unveränderte Einstiegspunkte dokumentieren. -->
- `db_sichern` und `max_anzahl_ordner` nach `anwendung/sicherung.py` verschoben.
- `change_log` und `change_log_info` nach `anwendung/protokollierung.py` verschoben.
  Beide Hilfen verwenden aktuelle Anwendungswerte; vier Adapter erhalten die Aufrufe.
  Sicherungsreihenfolge, Aufbewahrung, Dateimetadaten, Fehler und Protokollformat bleiben unverändert.
- Vollständiger Strukturvergleich aller vier Funktionen einschließlich Adapter und
  Initialisierung. Neuer lokaler Sicherungsvergleich mit Beispieldatenkopien;
  bestehender Protokolltest prüft die echten ausgelagerten Schreibmethoden.
- Alle 18 Freigabeprüfungen und Syntaxprüfung bestanden. Regulärer vollständiger
  Praxislauf mit 73 neuen Word-Dateien und 73 lesbaren PDFs bestanden; CSV-Referenz
  identisch und Originalbestand unverändert. Word-Paketinhalte, PDF-Seitenzahlen und
  PDF-Texte gegen 2.042 identisch. Keine visuelle Dokumentprüfung, keine neue EXE.
- Der erste Sicherungstest verglich künstliche Dateien mit unterschiedlichen
  Erstellungszeiten; feste Änderungszeiten im Test erlauben den Metadatenvergleich.
  Der Anwendungscode musste dafür nicht korrigiert werden.

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


<!-- Änderung 2.034: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.034 – 08.11.2026

- Abnehmeroberfläche in `AbnehmerOberflaeche` in `anwendung/abnehmer_ui.py`
  ausgelagert: Tabelle, CSV-Upload, Bearbeitung und Speichern.
- Tabellen- und Schaltflächenzustand liegt auf der Ansicht. Gemeinsame Daten,
  Speicherhilfen und die verbundene Abschlagsanpassung bleiben unverändert.
- Acht Adapter erhalten bisherige Aufrufe und refresh-Zugriffe. Alle Methoden
  und Adapter werden strukturell gegen das Original geprüft; gebundene Methoden
  zusätzlich mit lokalen Beispieldaten für Spalten, Bearbeitung einschließlich
  Nullwerten, Abschlagsänderung, CSV-Speicherung, Upload und Formatabweisung.
- Keine neue Windows-EXE. Prüfstand und Einschränkungen siehe TESTBERICHT.md.

<!-- Änderung 2.035: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.035 – 08.11.2026

- Mitgliederbereich mit 22 Methoden in `MitgliederOberflaeche` in
  `anwendung/mitglieder_ui.py` ausgelagert: Tabellenaufbau und Filter,
  Wartungsdialoge, Anschlusswechsel, Mitgliederbearbeitung, Import,
  Speichern, CSV-/Word-Export und Serienbriefdialog.
- Anzeige- und Dialogzustand liegt auf der Ansicht; gemeinsame Daten und Hilfen
  werden über die Anwendung gelesen. Adapter erhalten bestehende Aufrufe und
  refresh-Zugriffe, einschließlich der beiden asynchronen Einstiegspunkte.
- Alle Methoden samt verschachtelten Funktionen und Adapter strukturell gegen
  Original geprüft. Gebundene Methoden mit lokalen Beispieldaten verglichen;
  vollständiger Register-/Abrechnungspraxislauf bestanden. Details und bestehende
  Einschränkung des Wartungsfilters stehen im Prüfbericht.
- Keine neue Windows-EXE erstellt.

<!-- Änderung 2.036: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.036 – 08.11.2026

- Acht Kontodatenmethoden nach `anwendung/kontodaten_ui.py` in die Klasse
  `KontodatenOberflaeche` ausgelagert: Tabellenaufbau, Upload, Laden,
  Bearbeiten einschließlich IBAN-Prüfung, Speichern und Aufbau des Registers.
- Tabelle und Speichern-Schaltfläche gehören zur Ansicht. Gemeinsame Daten und
  die Auswahlfelder für bestehende Buchungsexporte bleiben auf der Anwendung.
  CSV-Berechnungen, Exportfunktionen und Speicherdialoge bleiben unverändert.
- Acht Adapter erhalten bisherige Aufrufe und refresh-Zugriffe. Alle Methoden
  und Adapter strukturell gegen das Original geprüft; gebundene Methoden mit
  lokalen Beispieldaten für Spalten, Bearbeiten, IBAN, Laden, Speichern und Import
  verglichen. Prüfstand und Grenzen siehe TESTBERICHT.md.
- Keine neue Windows-EXE erstellt.

<!-- Änderung 2.037: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.037 – 08.11.2026

- Sechs Werkzeugmethoden in `WerkzeugeOberflaeche` in
  `anwendung/werkzeuge_ui.py` ausgelagert: Registeraufbau, drei asynchrone
  Ordnerauswahlen, ID-Ermittlung und PDF-Zusammenfügen.
- Beschriftungen und Hinweisfeld liegen auf der Ansicht; bisherige Ordnerpfade
  bleiben auf der Anwendung. Sechs Adapter erhalten bestehende Aufrufe.
- Alle Methoden und Adapter strukturell gegen Original geprüft. Gebundene
  Methoden mit echten lokalen PDFs für Ordnerwahl/Abbruch, ID-Zuordnung,
  fehlende und mehrfache Zuordnungen, leere Ordner, Fortschritt und bytegleichen
  PDF-Inhalt einschließlich Seitenreihenfolge mit dem Original verglichen.
- Keine neue Windows-EXE; Prüfstand und Grenzen siehe TESTBERICHT.md.

<!-- Änderung 2.038: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.038 – 08.11.2026

- Vier Oberflächenmethoden in `EinstellungenOberflaeche` in
  `anwendung/einstellungen_ui.py` ausgelagert: Dialogaufbau, Standard-Rücksetzung,
  asynchrone Arbeitsordnerauswahl und Speichern.
- Eingabefelder und Dialoge gehören zur Ansicht. Gemeinsame Konfiguration,
  Einlesen und Pfadbildung bleiben auf der Anwendung. Vier Adapter erhalten
  bestehende Aufrufe; Speicherreihenfolge und Neustartnachfrage bleiben gleich.
- Alle Methoden und Adapter strukturell gegen Original geprüft; bestehende
  INI-Hilfsaufrufe nur für diesen Vergleich in ihre Originalzugriffe zurückgeführt.
- Lokale Konfigurationskopien für bytegleiche INI-Speicherung, Arbeitsordnerwechsel,
  Standard-Rücksetzung, Ordnerwahl/Abbruch und Dialogaufrufe verglichen.
- Keine neue Windows-EXE; Prüfstand und Grenzen siehe TESTBERICHT.md.

<!-- Änderung 2.039: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.039 – 08.11.2026

- Drei Anzeigemethoden in `ChangelogOberflaeche` in `anwendung/changelog_ui.py`
  ausgelagert: Registeraufbau, Markdown-Anzeige und Aktualisierung mit Filter.
- Anzeigeelement und Filter gehören zur Ansicht. Protokollpfad und unveränderte
  Schreibfunktionen bleiben auf der Anwendung. Drei Adapter erhalten bisherige Aufrufe.
- Methoden und Adapter strukturell gegen Original geprüft. Gebundene Methoden
  für alle Filter, fehlende/leere Dateien sowie Aktualisierung nach Schreibzugriffen
  verglichen; Protokolldateien bytegleich. Mangels Beispielprotokoll werden
  Prüfeinträge ausschließlich lokal aus Mitgliederdaten der Beispiele abgeleitet.
- Keine neue Windows-EXE; Prüfstand und Grenzen siehe TESTBERICHT.md.

<!-- Änderung 2.040: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.040 – 08.11.2026

- Fünf Statistikmethoden nach `anwendung/statistik_ui.py` in die Klasse
  `StatistikOberflaeche` ausgelagert: Abnehmerauswahl, Vergleichswerte,
  CSV-Laden, Diagrammaufruf und Aufbau der Statistikoberfläche.
- Auswahlfelder und Plot gehören zur Ansicht; Abnehmerdaten und Abrechnungspfad
  bleiben auf der Anwendung. Fünf Adapter erhalten bestehende Aufrufe.
- Statistikregister bleibt deaktiviert. Bestehende Typbehandlung und das bisherige
  Diagrammverhalten bleiben unverändert; keine fachlichen Korrekturen vorgenommen.
- Methoden und Adapter strukturell gegen Original geprüft. Gebundene Methoden mit
  lokalen Beispieldaten sowie ein gefundener-Werte-Zweig mit expliziten Text-Identen
  und Plotly-Figuren gegen Original verglichen. Prüfgrenzen siehe TESTBERICHT.md.
- Keine neue Windows-EXE erstellt.

<!-- Änderung 2.041: Technischen Umbau versionsbezogen dokumentieren. -->
## Version 2.041 – 08.11.2026

- Sieben Bedienmethoden in `BuchungsexportOberflaeche` in
  `anwendung/buchungsexport_ui.py` ausgelagert: Einlesen der Jahreslisten,
  fünf Export-Speicheraufrufe und nativer CSV-Speicherdialog.
- Auswahlfelder, gemeinsame Daten und CSV-Funktionen bleiben auf der Anwendung.
  Die Bedienhilfe wird ohne UI-Start an diese Anwendung angebunden. Sieben Adapter
  erhalten bestehende Aufrufe; Kontodatenansicht bleibt unverändert.
- Alle Methoden samt asynchronen Adaptern strukturell gegen Original geprüft.
  CSV-Referenztest führt die tatsächlichen gebundenen Bedienmethoden aus und
  ersetzt nur native Dialoge und Meldungen. Sämtliche Referenzfälle bytegleich;
  bestehende freigegebene Fehlerkorrekturen weiter bestätigt.
- Jahreslisten, fehlende/vollständige Auswahl, Dateinamensvorgaben, Speichern
  und Abbruch separat gegen Original geprüft. Prüfgrenzen siehe TESTBERICHT.md.
- Keine neue Windows-EXE erstellt.

<!-- Änderung 2.042: Erneute Umsetzung nach Rücknahme von 2.041 dokumentieren. -->
## Version 2.042 – 08.11.2026

- Buchungsexport-Bedienabläufe erneut wie unter 2.041 beschrieben ausgelagert.
  CSV-Funktionen und Berechnungen bleiben unverändert.
- 2.041 wurde wegen nicht vollständig erfolgreicher regulärer PDF-Praxisprüfung
  durch einen Revert zurückgenommen; der GitHub-Release bleibt zurückgezogen.
- Erneute Übernahme und Veröffentlichung erst nach vollständig erfolgreichem
  regulärem Praxislauf und allen gebündelten Freigabeprüfungen. Kein isolierter
  Ersatz der Word-Instanzbeschaffung für diese Freigabe.
- Eigene neue Versionsnummer erhält die unveränderte Historie und den zurückgezogenen
  Tag 2.041. Keine neue Windows-EXE. Tatsächliche Prüfungen siehe TESTBERICHT.md.
