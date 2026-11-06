# Prüfbericht ANA – aktueller Arbeitsstand

<!-- Änderung für v2: Nur Prüfstatus veröffentlichen, keine Beispieldaten. -->

Stand: 06.11.2026

Umgebung: Windows, Python 3.13.5.

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

Vorhandene Release-Archive werden nicht als Nachweis für nachträgliche Quelländerungen verwendet.
Separate Prüfungen der Verzeichnisumstellung sind in docs/STRUKTUR.md dokumentiert.
