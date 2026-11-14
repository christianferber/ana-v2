# ANA Release Notes

<!-- Änderung 2.06.00: Nur Versionen 2.xx aufführen und Zwischenstände knapp zusammenfassen. -->
<!-- Änderung 2.06.00: Technische Dokumentation wird gemäß Freigabeprozess 7 separat geführt. -->

<!-- Änderung 2.06.01: Geprüften Quellstand bereitstellen; sichtbare Version bleibt 2.06. -->
## Version 2.06 – 14.11.2026

<!-- Änderung nach 2.06.00: Neue Tools und einzeilige Navigation im aktuellen Quellstand. -->
- Feature: Tools mit den Unterbereichen PDF-Zusammenführung und Buchungsmanagement. PDF-Kontoauszüge lokal einlesen, Buchungen nach Betreff ausblenden oder reaktivieren und fehlende bzw. fehlerhaft benannte Rechnungen erkennen.
<!-- Änderung nach 2.06.00: Ergänzte Rechnungsbetragsprüfung mit lokaler Texterkennung. -->
- Verbesserung: Rechnungsendbeträge werden mit den Buchungen verglichen, bei gescannten Rechnungen mit lokaler Windows-Texterkennung. Abweichende und nicht eindeutig lesbare Beträge werden zur Prüfung angezeigt.
<!-- Änderung nach 2.06.00: Gelockerte Dateinamen und sichtbarer Prüffortschritt gemäß ergänzter Vorgabe. -->
- Verbesserung: Rechnungsdateinamen dürfen statt eines Empfängers auch einen Zweck enthalten. Rechnungsnummer, „vom“ und Rechnungsdatum sind optional. Die Prüfung zeigt ihren Fortschritt an.
<!-- Änderung nach 2.06.00: Ausschlüsse in eigener CSV-Datenbank ablegen. -->
- Verbesserung: Ausgeblendete Buchungen werden in einer eigenen CSV-Datei im Datenbankverzeichnis gespeichert. Die bisherige Auswahl wird automatisch übernommen.
<!-- Änderung nach 2.06.00: Empfänger/Zweck anzeigen und passende Buchungen automatisch ausblenden. -->
- Verbesserung: Empfänger und Zweck werden aus den Buchungsdetails ermittelt und angezeigt. Ausblenden erfasst sofort und bei späteren Importen auch Buchungen mit demselben Empfänger und Zweck. Bestehende Ausschlüsse bleiben erhalten.
<!-- Änderung nach 2.06.00: Getrennte Status, reine Anzeigefilter und feste Tabellenüberschriften. -->
- Verbesserung: Rechnungszuordnung und Betrag erhalten getrennte Prüfstatus. Erfolgreiche Ergebnisse lassen sich gezielt ausblenden. Tagesnummern berücksichtigen ausgeblendete Buchungen; die doppelte Betreff-Spalte entfällt.
- Verbesserung: Tabellenüberschriften bleiben beim Scrollen sichtbar.
<!-- Änderung nach 2.06.01: Buchungs-IDs nach Ausblenden und Aktivieren in beiden Ansichten aktualisieren. -->
- Verbesserung: Buchungs-IDs werden nach Ausblenden und Reaktivieren in Umsatzverwaltung und Rechnungsprüfung sofort neu berechnet. Ist nur noch eine Tagesbuchung aktiv, entfällt ihr Nummernanhang.
<!-- Änderung: Maßgeblichen Tag für die Rechnungsbewertung ausdrücklich festhalten. -->
- Hinweis: Für Buchungs-ID und Rechnungszuordnung gilt der Buchungstag des Kontoauszugs, auch bei abweichender Wertstellung.
- Verbesserung: Alle Einträge der Seitennavigation bleiben einzeilig.
<!-- Änderung nach 2.06.00: Fehlende Datenordner anhand des INI-Arbeitsordners ergänzen. -->
- Bugfix: Fehlende Datenordner werden im eingestellten Arbeitsordner angelegt. Bei leerem INI-Pfad wird der Programmordner verwendet.
- Verbesserung: ANA startet automatisch maximiert mit erreichbarem Fenster-X.
- Verbesserung: Kompaktes Windows-Paket mit EXE, Bildern, INI und Release Notes. Die EXE enthält ihre Laufzeitdateien.
- Verbesserung: Kompakte Release Notes nach Versionen 2.xx.

## Version 2.05 – 13.11.2026

- Feature: ZIP-Vollsicherung mit Ordnerwahl, manueller Sicherung, Sicherung beim Beenden und Aufbewahrung in Wochen.
- Verbesserung: Sichtbarer Sicherungsfortschritt und feste Dialoggrößen. Einstellungen übersichtlich in Tabs gegliedert.
- Feature: Verbrauchsübersicht und jährlicher Kostenvergleich mit Verbraucherauswahl, Mindestabnahme und Abweichungen.
- Feature: Fettformatierung in Serienbriefen mit `<bold>Text</bold>`.

## Version 2.04 – 08.–11.11.2026

- Verbesserung: Seitennavigation, kompakte Bedienflächen und Startanzeige mit ANA-Logo.
- Verbesserung: Erweiterte Änderungsprotokolle für Daten und Einstellungen.
- Bugfix: Schutz bestehender Dateien bei Speicher- und Sicherungsfehlern sowie verständliche PDF-Exportfehler.

## Version 2.03 – 06.11.2026

- Verbesserung: Wartung von Jahresabrechnung, Stammdaten, Einstellungen und Werkzeugen.

## Version 2.02 – 06.11.2026

- Verbesserung: Wartung der Rückvergütung.

## Version 2.01 – 06.11.2026

- Verbesserung: Stabilere PDF-Stapelerstellung für Rückvergütungen und Bereinigung der gestarteten Word-Sitzung bei Fehlern.

## Version 2.00 – 05.11.2026

- Bugfix: Korrigierte Buchungs-CSV für Rückvergütungen bei „von Netto“ und Zwischenablesung.
