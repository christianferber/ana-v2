ANA RELEASE NOTES
=================

<!-- Änderung: Version 2.x wie Version 1.x aus Sicht der Endbenutzer beschreiben. -->
Features, Verbesserungen und Fehlerkorrekturen für Anwender.
Technische Einzelheiten stehen im [Änderungsprotokoll](docs/AENDERUNGSPROTOKOLL.md).

<!-- Änderung nach 2.05.00: Vollsicherung aus Anwendersicht beschreiben. -->
Build 2.05.01 – 13.11.2026
-------------------------

<!-- Änderung nach 2.05.00: Doppelten Beenden-Knopf aus der Kopfzeile entfernen. -->
Verbesserung: Die Anwendung wird über das Fenster-X geschlossen. Der zusätzliche
Schließen-Knopf in der Kopfzeile entfällt. Die aktivierte Sicherung wird beim Beenden ausgeführt.

<!-- Änderung nach 2.05.00: Einstellungen mit Tabs und gemeinsame Sicherungsanzeige beschreiben. -->
Verbesserung: Die Einstellungen sind in „Betreiber und Preise“, „Arbeitsordner“,
„Datensicherung“ und „Darstellung“ gegliedert. Speichern und Abbrechen gelten für
alle Tabs; Eingaben bleiben beim Wechsel erhalten. Die Aufbewahrung in Wochen
erscheint nur bei eingeschaltetem Aufräumen.

<!-- Änderung nach 2.05.00: Stabile Dialogposition beim Tabwechsel beschreiben. -->
Verbesserung: Der Einstellungsdialog behält beim Tabwechsel dieselbe Größe und
Position. Tabzeile und Aktionsleiste bleiben stehen; längere Inhalte scrollen im Tab.

Verbesserung: Komprimieren und Sichern verwenden einen gemeinsamen Fortschrittsbalken
von 0 bis 100 Prozent, einschließlich der ZIP-Prüfung und des Sicherungsabschlusses.

<!-- Änderung nach 2.05.00: Fehler der Sicherungsfortschrittsanzeige korrigieren. -->
Bugfix: Im Sicherungsbalken erscheint kein interner Zahlenwert mehr. Der Dialog
behält beim Abschluss mit längerem Dateipfad seine Größe; die Schließen-Schaltfläche
bleibt an derselben Position. Komprimierung und ZIP-Prüfung zählen den Fortschritt
blockweise nach verarbeiteter Datenmenge statt nach festen Phasenanteilen.

Feature: In den Einstellungen lässt sich eine ZIP-Vollsicherung mit frei wählbarem
Zielordner erstellen. Sie enthält die gespeicherten Daten des Arbeitsordners,
einschließlich Datenbanken, Vorlagen, Abrechnungen und Rückvergütungen, sowie die
Programmeinstellungen. „Jetzt sichern“ startet eine manuelle Sicherung mit
Fortschrittsbalken. Nicht gespeicherte Eingaben werden nicht übernommen.

Feature: Wahlweise erstellt ANA beim Beenden automatisch eine Sicherung, auch
beim Schließen über das Fenster-X. Währenddessen zeigt ein eigenes Fenster den
Fortschritt. Sicherungsordner und Optionen werden mit den Einstellungen gespeichert.

<!-- Änderung nach 2.05.00: Erfolg der Sicherung beim Beenden sichtbar bestätigen. -->
Verbesserung: Das Sicherungsfenster beim Beenden erscheint mittig im Vordergrund.
Nach erfolgreicher Sicherung zeigt es kurz „Sicherung abgeschlossen“ und 100 Prozent,
bevor die Anwendung vollständig beendet wird.

<!-- Änderung nach 2.05.00: Fortschrittsfenster beim Schließen unabhängig betreiben. -->
Bugfix: Die Anzeige der Beendigungssicherung läuft in einem eigenen Fensterprozess.
Vor Beginn wird geprüft, ob das Fenster sichtbar ist. Falls die Anzeige ausfällt,
wird dies nach der Sicherung ausdrücklich gemeldet.

Verbesserung: Optional werden nach erfolgreicher Sicherung ältere Vollsicherungen
aufgeräumt. Die Aufbewahrung ist in ganzen Wochen wählbar; Vorgabe sind 12 Wochen.
Fremde Dateien und Sicherungen anderer Arbeitsordner bleiben erhalten. Automatische
Sicherung und Aufräumen sind zunächst ausgeschaltet.

<!-- Änderung nach 2.049: Neue Serienbriefformatierung im lokalen Arbeitsstand. -->
Version 2.05.00 – 13.11.2026
--------------------------

<!-- Änderung nach 2.049: kWh-Darstellung ohne Nachkommastellen. -->
Verbesserung: kWh-Werte erscheinen in den Statistiken ohne Nachkommastellen. Eurobeträge und Prozentwerte behalten zwei Nachkommastellen.

<!-- Änderung nach 2.049: Einheiten direkt an Statistikwerten anzeigen. -->
Verbesserung: In den Statistiken stehen Euro, kWh und Prozent direkt bei den Werten statt in den Tabellenüberschriften. Fehlende Werte bleiben als „–“ erkennbar. Auch im Verbrauchsdiagramm steht kWh direkt an den Achsenwerten.

<!-- Änderung nach 2.049: Einheitliche Jahresspalten im Verbraucherbereich beschreiben. -->
Verbesserung: Beide Tabellen unter „Verbraucherspezifisch“ zeigen die Jahre als Spalten. Die Verbrauchstabelle enthält Verbrauch, Mindestabnahme sowie absolute und prozentuale Abweichung als Zeilen. Der Kostenvergleich zeigt dort nur die jährlichen Differenzen ohne erneute Angaben zu Ident, Name und Vorname.

<!-- Änderung nach 2.049: Zweiten Statistikvergleich aus Anwendersicht beschreiben. -->
Feature: „Kostenvergleich zu Mindestabnahme“ zeigt alle Abnehmer in einer gemeinsamen Tabelle mit einer Spalte je Jahr. Jede Jahreszelle enthält die Differenz aus tatsächlichen Wärmekosten und Mindestabnahme in Euro. Positive Differenzen erscheinen grün, negative rot; Null bleibt neutral und fehlende Werte erscheinen als „–“. Die Tabelle ist zunächst nach dem neuesten Jahr aufsteigend sortiert; durch Klick auf eine Jahresspalte lässt sich die Sortierung ändern.

<!-- Änderung nach 2.049: Nullbeginn und Jahrestabelle der Verbrauchsübersicht beschreiben. -->
Verbesserung: Der Verbrauchsgraph beginnt bei 0 kWh. Unter dem Graphen zeigt eine Jahrestabelle Verbrauch, Mindestabnahme und die Abweichung in kWh und Prozent. Die Abweichung ist Verbrauch minus Mindestabnahme; die Prozentangabe bezieht sich auf die Mindestabnahme. Bei Mindestabnahme 0 wird kein Prozentwert angezeigt.

<!-- Änderung nach 2.049: Verbrauchsstatistik aus Sicht der Anwender beschreiben. -->
<!-- Änderung nach 2.049: Allgemeine und verbraucherspezifische Statistiken trennen. -->
Feature: Der Bereich „Statistik“ enthält die Bereiche „Allgemein“ und „Verbraucherspezifisch“. Allgemein zeigt den Kostenvergleich aller Verbraucher. Verbraucherspezifisch steht oben die Verbraucherauswahl über Ident, Name und Vorname; darunter zeigen Verbrauchsübersicht und Kostenvergleich gemeinsam nur die Daten dieses Verbrauchers. Die Verbrauchsübersicht zeigt tatsächlichen Verbrauch und Mindestabnahme aller gespeicherten Jahresabrechnungen als zwei Linien in kWh. Fehlende Jahreswerte erscheinen als Lücken.

Feature: In Serienbriefen lässt sich Text in Betreff und Brieftext mit `<bold>TEXT</bold>` fett darstellen. Das funktioniert auch mit Platzhaltern und Zeilenumbrüchen. Ein Hinweis im Dialog erklärt die Schreibweise.

<!-- Änderung 2.049: UI-Modernisierung aus Sicht der Anwender beschreiben. -->
Version 2.049 – 11.11.2026
-------------------------

Feature: Einklappbare Seitennavigation mit den bisherigen Bereichen, gruppiert nach Stammdaten, Abrechnung und Programm.

Verbesserung: Kompakte Kopfzeile, einheitliche Farben und Abstände sowie übersichtlichere Eingabe- und Aktionsflächen in der Jahresabrechnung. Einstellungen stehen links bei den übrigen Menüpunkten; das rechte Logo ist größer dargestellt.

Verbesserung: Die Startanzeige verwendet das offizielle ANA-Logo und einen sich anhand der Startphasen füllenden Fortschrittsbalken. Sie schließt sich weiterhin automatisch, sobald das Hauptfenster verbunden ist.

Bugfix: Der Menüknopf bleibt auch bei geöffneter mobiler Seitennavigation erreichbar.

Berechnungen, Importabläufe, Dateiformate und Abrechnungsergebnisse bleiben unverändert.

<!-- Änderung 2.048: Bisherigen Wartungsstand als neue Version veröffentlichen. -->
Version 2.048 – 10.11.2026
-------------------------

<!-- Änderung: Sichtbare Rückmeldung beim Programmstart beschreiben. -->
Feature: Beim Start zeigt ANA ein kleines Fenster mit laufendem Fortschrittsbalken und Statusmeldungen. Es schließt sich automatisch, sobald das Hauptfenster verbunden ist. Eine geschätzte Restzeit wird nicht angezeigt.

<!-- Änderung: Vollständigere Änderungsprotokollierung aus Anwendersicht beschreiben. -->
Verbesserung: Daten- und Einstellungsänderungen werden umfassender im Changelog erfasst. Mitgliederänderungen erscheinen bereits bei der Übernahme; Änderungen im Arbeitsspeicher und gespeicherte Dateien werden unterschieden. Bereits erfolgte Teiländerungen nach einem Abbruch sind gekennzeichnet. Für Abrechnungen, Einstellungen und Datenbankspeicherungen stehen zusätzliche Filter bereit.

<!-- Änderung: Verständliche Exportfehler und erneute Startmöglichkeit beschreiben. -->
Bugfix: Fehler beim Erzeugen von Abrechnungen, Rückvergütungen und Mitgliederlisten werden angezeigt. Während eines laufenden Exports ist ein weiterer Start desselben Exports gesperrt. Nach einem Fehler wird der Exportknopf wieder freigegeben.

<!-- Änderung: Bereinigung nach fehlgeschlagenem Abrechnungs-PDF-Export beschreiben. -->
Bugfix: Beim Abrechnungs-PDF-Export wird eine eigene Word-Sitzung verwendet und auch bei einem Exportfehler geschlossen. Bereits geöffnete Word-Sitzungen werden dadurch nicht mitverwendet.

<!-- Änderung: Schutz vor Datenverlust bei Speicher- und Sicherungsfehlern beschreiben. -->
Bugfix: CSV-Dateien werden erst nach vollständigem Schreiben ersetzt. Bei einer fehlgeschlagenen neuen Datensicherung bleiben die bisherigen Sicherungen erhalten. Wiederholte Sicherungen in derselben Sekunde werden getrennt gespeichert.

Dateiformate und Abrechnungsergebnisse bleiben unverändert.

<!-- Änderung 2.047: Interne Wartung aus Anwendersicht dokumentieren. -->
Version 2.047 – 09.11.2026
-------------------------

Interne Wartung der Mitgliederaktualisierung; die Übernahme von Namen und Vornamen in Abnehmer-, Zähler-, Abschlags- und Kontodaten bleibt unverändert.

<!-- Änderung 2.046: Interne Wartung aus Anwendersicht dokumentieren. -->
Version 2.046 – 09.11.2026
-------------------------

Interne Wartung der CSV-Speicherung für Abrechnung und Rückvergütung; Bedienung, Dateiformate und Ergebnisse bleiben unverändert.

<!-- Änderung 2.045: Interne Wartung aus Anwendersicht dokumentieren. -->
Version 2.045 – 08.11.2026
-------------------------

Interne Wartung der Datenbankzugriffe; Laden, Speichern und Dateiformate bleiben unverändert.

<!-- Änderung 2.044: Interne Wartung aus Anwendersicht dokumentieren. -->
Version 2.044 – 08.11.2026
-------------------------

Interne Wartung der Datenaufbereitung; Datenimport, Zahlenumwandlung und Berechnungsergebnisse bleiben unverändert.

<!-- Änderung 2.043: Interne Wartung aus Anwendersicht dokumentieren. -->
Version 2.043 – 08.11.2026
-------------------------

Interne Wartung der Datensicherung und Änderungsprotokolle; Sicherungsverhalten, Protokolle und Bedienung bleiben unverändert.

<!-- Änderung 2.042: Erneute Umsetzung aus Anwendersicht dokumentieren. -->
Version 2.042 – 08.11.2026
-------------------------

Interne Wartung der Buchungsexporte; Auswahl, Speicherdialoge und CSV-Ergebnisse bleiben unverändert.

<!-- Änderung 2.041: Wartung aus Anwendersicht dokumentieren. -->
Version 2.041 – zurückgezogen
-------------------------

Diese Version wurde zurückgezogen und soll nicht verwendet werden.

<!-- Änderung 2.040: Wartung aus Anwendersicht dokumentieren. -->
Version 2.040 – 08.11.2026
-------------------------

Interne Wartung des deaktivierten Statistikbereichs; Bedienung und Ergebnisse bleiben unverändert. Das Statistikregister bleibt deaktiviert.

<!-- Änderung 2.039: Wartung aus Anwendersicht dokumentieren. -->
Version 2.039 – 08.11.2026
-------------------------

Interne Wartung der Changelog-Anzeige; Protokollierung, Bedienung und Filter bleiben unverändert.

<!-- Änderung 2.038: Wartung aus Anwendersicht dokumentieren. -->
Version 2.038 – 08.11.2026
-------------------------

Interne Wartung der Einstellungen; Bedienung, Speicherung und Neustartverhalten bleiben unverändert.

<!-- Änderung 2.037: Wartung aus Anwendersicht dokumentieren. -->
Version 2.037 – 08.11.2026
-------------------------

Interne Wartung der Werkzeuge; Bedienung, PDF-Zuordnung und Ergebnisse bleiben unverändert.

<!-- Änderung 2.036: Wartung aus Anwendersicht dokumentieren. -->
Version 2.036 – 08.11.2026
-------------------------

Interne Wartung der Kontodatenverwaltung; Bedienung, Datenimport und Ergebnisse bleiben unverändert.

<!-- Änderung 2.035: Wartung aus Anwendersicht dokumentieren. -->
Version 2.035 – 08.11.2026
-------------------------

Interne Wartung der Mitgliederverwaltung; Bedienung, Datenimport und Ergebnisse bleiben unverändert.

<!-- Änderung 2.034: Wartung aus Anwendersicht dokumentieren. -->
Version 2.034 – 08.11.2026
-------------------------

Interne Wartung der Abnehmerverwaltung; Bedienung, Datenimport und Ergebnisse bleiben unverändert.

<!-- Änderung 2.033: Wartung aus Anwendersicht dokumentieren. -->
Version 2.033 – 06.11.2026
-------------------------

Interne Wartung der Zählerverwaltung; Bedienung, Datenimport und Ergebnisse bleiben unverändert.

Version 2.032 – 06.11.2026
-------------------------

Keine Änderungen an Bedienung und Funktionen.

Version 2.031 – 06.11.2026
-------------------------

Interne Wartung der Abschlagsverwaltung; Bedienung und Funktionen bleiben unverändert.

Version 2.03 – 06.11.2026
------------------------

Interne Wartung der Jahresabrechnung; Bedienung und Berechnung bleiben unverändert.

Version 2.02 – 06.11.2026
------------------------

Interne Wartung der Rückvergütung; Bedienung und Berechnung bleiben unverändert.

Version 2.01 – 06.11.2026
------------------------

- Verbesserung: PDF-Erstellung für mehrere Rückvergütungen überarbeitet.
- Bugfix: Die für die Rückvergütungs-PDFs gestartete Word-Sitzung wird auch bei einem Konvertierungsfehler geschlossen.

Version 2.00 – 05.11.2026
------------------------

- Bugfix: Fehler beim Erstellen der CSV-Buchungsvorlage für Rückvergütungen mit der Option „von Netto“ behoben.
- Bugfix: Bei Rückvergütungen mit Zwischenablesung enthält die CSV-Buchungsvorlage für Bruttobeträge den korrekten Gesamtbetrag.

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
