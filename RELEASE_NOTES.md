ANA RELEASE NOTES
=================

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

Version 1.15
------------

- Feature: Die Spalten Ident, Name und Vorname werden bei Tabellen fixiert (scrolling deaktiviert)
- Feature: Bei Tabellenänderungen wird kein Refresh der Tabelle durchgeführt und Daten werden durchgängig erst in der DB gespeichert, wenn der Speichern Button gedrückt wird.
- Feature: Fenster beim Start vergrößert
- Feature: Zählerspalten werden absteigend sortiert
- Feature: Netto-Gesamtumsatz wird bei Abrechnung angezeigt
- Feature: Jahre und Daten werden automatisch beim Tab-Wechsel aktualisiert (separater Button entfernt)
- Feature: Tool "PDF Kombinieren" implementiert
- Feature: Farben gemäß NiceUI Farbschema angepasst
- Bugfix: Formatierung Mehrwertsteuer bei Mindestabnahme in PDF-Erzeugung
- Bugfix: Berechnung MwSt und Netto-Betrag bei Mindestabnahme
- Bugfix: Bei Anpassung von Daten direkt in der Zählertabelle werden die Werte erstmal im UI geändert und nicht in der Datenbank gespeichert. Vorher wurden sie direkt in der DB gespeichert.
- Bugfix: Fehler im Editiermodus bei Mitgliedern wurde behoben.
- Bugfix: Anpassungen in Mitglieder werden nun direkt (ohne Neustart) bei Buchungsvorlagen übernommen.
- Bugfix: Erstellung von CSV für Jahresabrechnung Lastschriften mit "von Netto"
- Bugfix: "Speichern" Buttons werden nur aktiviert, wenn neue Daten zu speichern sind

Version 1.14
------------

- Feature: Bei Seriendruck können nun Variablen mit der Syntax %[Variable]% verwendet werden.
- Feature: Bestehende Zählerdaten können jetzt beim Upload nach Auswahl ergänzt oder überschrieben werden.
- Bugfix: Datum für Mitgliederliste (Generalversammlung) wird von Dialog übernommen.
- Bugfix: Dateinamen bei Serienbriefen überprüfen (Ident vs laufende Nr.)
- Bugfix: Bei Abrechnung mit Zählerwechsel wird der Start-Stand des neuen Zählers nun durchgängig mit 0 berücksichtigt.
- Bugfix: Fehler beim Sortieren von importierten Zählerdaten behoben. Wenn bei einem Zählerwechsel das End-Datum der Auswertung nicht das Jahresende war, kam es zu einem Fehler.
- Bugfix: Datenimport Zählerwechsel: Bei nicht vorhandenden Zählerdaten zum Zählerwechsel wird jetzt "-1" eingetragen. Ist das Zählerwechseldatum nicht vorhanden, wird jetzt "NICHT_VORHANDEN" eingetragen.
- Bugfix: Abschlag wurde nach Jahresabrechnung nicht übernommen
- Bugfix: Bei Überprüfung der Zählerdaten werden Änderungen nur im UI übernommen, nicht in der DB gespeichert. Zum Speichern in der DB muss explizit "Zählerdaten speichern" geklickt werden.

Version 1.13
------------
- Feature: Unterstützung für Zwischenablesung bei Rückvergütung implementiert
- Bugfix: Rundungsdifferenzen bei Buchungsvorlagen behoben

Version 1.12
------------
- Buchungsvorlagen: Schalter "Abrechnungsvorlagen von Netto" ist jetzt aktiviert per default.
- Feature: Unterstützung für Rückvergütug bei unterschiedlichen Jahresabrechnug mit Zwischenablesung und unterschiedlichen Mwst-Steuer-Sätzen
- Feature: Mwst-Satz bei Rückvergütungen wird nun automatisch aus Jahresabrechnung ausgelesen
- Bugfix: MwSt-Satz bei Materialumsatz fest bei 19% statt Prozentsatz von Jahresabrechnung

Version 1.11
------------
- Bugfix: Für den Serienbrief werden alle Felder (Spalten) der gefilterten Tabelle verwendet. Diese können als Felder in der Word-Vorlage genutzt werden.
- Bugfix: Fehler beim Neuanlegen und Ändern von Mitgliedern behoben
- Bugfix: Logging bei Mitgliederdaten korrekt implementiert
- Feature: Logging für Wartung implementiert

Version 1.10
------------
- Bugfix: Mitgliederliste für Generalversammlung und Jahresabschluss enthält nun keine doppelten Werte mehr in bestimmten Situationen
- Bugfix: E-Mail Button in Mitgliederseite deaktiviert (da Funktion nicht implementiert)
- Bugfix: Filter wird bei Generalversammlung und Jahresabschluss deaktiviert, nur Sortierung nach Name möglich ist
- Feature: Meldung bzgl. Speicherorts des CSV Downloads, Word Downloads und Serienbriefs wird nun angezeigt
- Feature: neuer Filter "Verbraucher mit Wartungsdaten" zeigt für Anschlüsse mit Wartungseinträgen die letzten 3 Einträge an
- Feature: Datumsauswahl nach Kalender bei neuen Wartungseinträgen


Version 1.09
------------
- Feature: Download für komma-basierte CSV-Datei bei Abrechnung und Rückvergütung implementiert
- Feature: Word und PDF Abrechnungen und Rückvergütungen werden jetzt in "word" bzw. "pdf" Unterverzeichnis des Abrechnungs-/Rückvergütungsjahres gespeichert
- Feature: Plausibilitätsprüfung für Abrechnungen (Starke Abweichungen bei Jahresverbrauch, Veränderung der Mindestabnahme)
- Feature: Filter in Mitglieder-Tab wurden komplett überarbeitet
- Feature: Mitgliederliste kann als Word heruntergeladen werden (für Jahresabschluss und Generalversammlung)
- Feature: gefilterte Mitgliederliste kann als CSV heruntergeladen werden
- Feature: Benachrichtigungen werden farbig dargestellt
- Feature: Serienbrieffunktion bei Mitgliederliste
- Feature: Alle Vorlagen werden jetzt im Unterverzeichnis \vorlagen gespeichert. Für Abrechnungen und Rückvergütungen werden diese nicht mehr im jeweiligen Unterordner abgelegt.
- Feature: Bei Erstellung Abrechnung: Wenn im Vorjahr die Mindestabnahme ausgesetzt wurde (0), erfolgt eine Abfrage, ob dies auch für das bestehende Jahr so beibehalten werden soll
- Bugfix: Mehrwertsteuerberechnung für Zwischenablesung
- Bugfix: Beim Import von Zählerdaten werden bestehende Daten mit gleichem Zählerdatum nicht mehr überschrieben
- Bugfix: Word/PDF Erzeugung nur nach Speichern von Abrechnung bzw. Rückvergütung möglich
- Bugfix: Einige Tasks wie z.B. die Sicherungen wurden beim Programmstart doppelt ausgeführt
- Bugfix: Mitgliederfilter "aktive Mitglieder" wurde entfernt, da gleichzusetzen mit "Aktive Anschlüsse"
- Bugfix: Download für CSV mit Punkt bei Abrechnung und Rückvergütung
- Bugfix: Unterordner werden erst angelegt, wenn die erste Datei gespeichert wird
- Bugfix: Filter bei Mitglieder bereinigt

Version 1.08
------------
- Funktion Mitglieder mit Editierung, Anschlusswechsel und Wartungsdatenbank (Beta)
- Zählerimport wird auch unterstützt, wenn Zählerdatei bis zum 31.12. des Jahres ausgelesen wird, aber und die Daten das Datum 31.12. haben (normalerweise haben die Daten dann das Datum 01.01. des Folgejahres)
- Anpassungen für Abrechnung mit Zwischenablesung
- Abrechnungs- und Rückvergütungstabellen enthalten nun auch eine Spalte für das Abrechnungsjahr und das Folgejahr
- Bugfix: Zählersortierung korrigiert, wenn Zwischenzähler vor Jahresendzähler importiert wurden
- Bugfix: Wenn nachträglich Mindestabnahme auf 0 gesetzt wird, wird der Abschlag für das jeweilige Jahr nicht angepasst
- Bugfix: Rundung bei Mindestvertragssumme bis und ab ZA


Version 1.07
------------
- Bugfix CSV Export Grundgebühr, Jahresabrechnung
- Buttons bei Rückvergütung werden nach Logik ein- und ausgeblendet
- Bei Änderung von Vorname oder Name in den Basisdaten werden auch Abschlag-, Zähler- und Buchungsvorlagen-DBs aktualisiert
- Funktion "Mitglieder" beta


Version 1.06
------------
- Bugfix CSV Export Abschlag
- keine Virenmeldung mehr bei Ausführung
- Bugfix: Erstellung ana-betreiber.ini schlug fehl, wenn der Arbeitsordner das aktuelle Programmverzeichnis war.

Version 1.05
------------
- Option für Abrechnungsexport (Jahresabrechnung und Rückvergütung) bei dem der Bruttopreis vom Nettopreis berechnet wird, um Rundungsprobleme zu verhindern
- Betreiberdaten werden in ana-betreiber.ini im Arbeitsverzeichnis gespeichert und nicht in der ana.ini des Programmverzeichnisses. Ist die Datei nicht vorhanden, wird sie mit Standardwerten erstellt.

Version 1.04
------------
- Unterstützung für die Auswahl des Arbeitsordners unter Einstellungen
- Bugfix Überprüfung bei Abrechnung, ob Mindestabhnahme von Vorjahr vorhanden ist
- Bugfix Reduzierung Abschlag wird auch erlaubt, wenn Abrechnung nach Mindestabnahme (soweit Abschlag dann nicht unter Mindestabnahme liegt)
- Bugfix Bei Mindestabnahme 0 wird der Abschlag nicht auf 0 reduziert

Version 1.03
------------
- 1 statt 2 Buttons für Word/PDF-Erzeugung bei Abrechnung und Rückvergütung
- Anpassung Farbe Button Word/PDF-Erzeugung
- Abschlagsreduzierung greift nur bei Abrechnung nach tatsächlichem Verbrauch
- Bugfix Button-Sichtbarkeit Abrechnungen
- Bugfix Zählerdatenüberprüfung bei Erstellung Abrechnung
- Bugfix Rückvergütungssatz akzeptiert auch Kommawerte
- Bugfix Beim Speichern einer neuen Abrechnung wird Tabelle von DB geladen
- Bugfix Beim Ändern von Zählerdaten über einen Check wird nun auch ein Changelog-Eintrag geschrieben
- Bugfix Abschläge niedriger als die Mindestabnahme werden auf die Mindestabnahme gesetzt

Version 1.02
------------
- Bei Abnehmern mit Mindestabnahme 0 in einem Jahr wird nach der Abrechnung für das nächste Jahr die letzte Mindestabnahme hinterlegt. Ist keine letzte Mindestabnahme vorhanden, wird die ursprüngliche Mindestabnahme verwendet. Ebenso wird der Abschlag entsprechend hinterlegt
- Bugfix speichern Abschlag
- Bei Änderung Mindestabnhame wird automatisch auch der Abschlag für das Jahr entsprechend angepasst. Changelog wurde diesbzgl. auch ergänzt
- Wurde die Mindestabnahme in einem Jahr reduziert, wird der Abschlag gemäß der neuen Mindestabnahme für das Folgejahr verwendet
