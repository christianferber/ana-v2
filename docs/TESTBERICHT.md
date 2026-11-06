# Prüfbericht ANA – aktueller Arbeitsstand

<!-- Änderung für v2: Nur Prüfstatus veröffentlichen, keine Beispieldaten. -->

Stand: 06.11.2026

Umgebung: Windows, Python 3.13.5.

- Zähleransicht gegen Original: bestanden.
- Testprozesse und Startsperre: bestanden.
- Abschlagsansicht gegen Original: bestanden.
- Jahresabrechnung gegen Referenz: bestanden.
- Berechnung und Abbruchbedingungen: bestanden.
- Rückvergütung gegen Referenz: bestanden.
- Buchungs-CSV und freigegebene Fehlerkorrekturen: bestanden.
- Dateien, INI, Pfade und Strukturvergleich: bestanden.
- Dokumentfelder und simulierte Dokumentaufrufe: bestanden.
- Syntax aller Python-Dateien: bestanden.

Bereits durchgeführte Praxistests: Jahresabrechnung und Rückvergütung über die
Oberfläche berechnet, gespeichert und als echte Word-/PDF-Dateien erzeugt.
Dafür wurden isolierte lokale Datenkopien verwendet. Am 06.11.2026 wurde
der vollständige Rückvergütungs-Dokumentlauf mit 73 Word-Dateien und 73
lesbaren PDFs bestanden; CSV-Referenz und Originalbestand wurden geprüft.
Eine visuelle Dokumentprüfung fand aus
Datenschutzgründen nicht im KI-Kontext statt.

Am 06.11.2026 wurde auch der vollständige Abrechnungslauf nach der
Auslagerung der Oberfläche bestanden: 73 Word-Dateien und 73 lesbare PDFs.
CSV-Referenz und unveränderter Originalbestand wurden geprüft. Gegenüber
dem unmittelbar vorherigen Lauf sind Word-Paketinhalte, PDF-Seitenzahlen
und extrahierte PDF-Texte identisch. Keine visuelle Layoutprüfung.

Version 2.031: Abschlagsspalten, Bearbeiten, Upload und CSV-Speicherung
wurden mit lokalen Beispieldaten gegen das Original geprüft. Der Strukturvergleich
bestätigt alle verschobenen Methoden und die verbliebenen Einstiegspunkte.
Die echte Abschlagstabelle und der anschließende vollständige Abrechnungslauf
wurden am 06.11.2026 mit einer isolierten Datenkopie geprüft: CSV-Referenz
identisch, 73 neue Word-Dateien und 73 lesbare PDFs, Originalbestand unverändert.
Bearbeiten und Speichern der Abschläge wurden über gebundene Methoden geprüft;
im Browser wurde die Tabellenanzeige geprüft. Keine visuelle Dokumentprüfung.
Für 2.031 wurde keine neue Windows-EXE erstellt oder geprüft.

Version 2.032: Windows-Prozessgruppe und Startsperre mit echten Unterprozessen
geprüft. Auch ein nach dem Elternprozess weiterlaufendes Kind wurde nach Erfolg
und simuliertem Testfehler beendet; ein konkurrierender Teststart wurde blockiert.
Vollständiger Beispieldaten-Praxislauf am 06.11.2026 bestanden: Abschlagstabelle,
Abrechnung, CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs.
Original-Beispieldaten unverändert. Während des Laufs genau ein ANA-Testhauptprozess
und ein Fensterprozess bestätigt; anschließend null ANA-Prozesse und null Testbrowser.
Frühere Angaben zur vollständigen Fensterbereinigung waren unzutreffend und sind
mit diesem Stand korrigiert. Keine neue EXE; keine visuelle Dokumentprüfung.

Version 2.033: Alle ausgelagerten Zählermethoden und Adapter strukturell
gegen das Original geprüft. Gebundene Methoden mit lokalen Beispieldaten
für Import, Sortierung, Bearbeitung, Korrekturdialoge und CSV-Speicherung
verglichen. Visualisierungsimport einschließlich Zählerwechsel und
Formatabweisung geprüft. Echtes Zählerregister und vollständige Abrechnung
am 06.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,
73 neue Word-Dateien und 73 lesbare PDFs; Originalbestand per SHA256 unverändert.
Gegenüber dem vorherigen Praxislauf: alle Word-Paketinhalte sowie PDF-Seitenzahlen
und extrahierten Texte identisch.
Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.
Keine visuelle Dokumentprüfung im Modellkontext.

Vorhandene Release-Archive werden nicht als Nachweis für nachträgliche Quelländerungen verwendet.
Separate Prüfungen der Verzeichnisumstellung sind in docs/STRUKTUR.md dokumentiert.
