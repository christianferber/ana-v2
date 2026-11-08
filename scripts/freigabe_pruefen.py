# Änderung für v2: In scripts/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Lokale Freigabeprüfungen ohne Ausgabe von Beispieldaten bündeln."""

from datetime import datetime
from pathlib import Path
import hashlib
import subprocess
import sys


def main():
    basis = Path(__file__).resolve().parents[1]
    pruefungen = [
        # Änderung 2.039: Changelog-Filter und Anzeige ausschließlich lokal vergleichen.
        ('Changelog-Anzeige gegen Original', ['-m', 'tests.changelog_pruefen']),
        # Änderung 2.038: Einstellungsdialog und INI-Speicherung lokal vergleichen.
        ('Einstellungsansicht gegen Original', ['-m', 'tests.einstellungen_pruefen']),
        # Änderung 2.037: Werkzeuge mit ausschließlich lokalen PDF-Beispieldaten vergleichen.
        ('Werkzeuge gegen Original', ['-m', 'tests.werkzeuge_pruefen']),
        # Änderung 2.036: Gebundene Kontodatenmethoden mit lokalen Beispieldaten vergleichen.
        ('Kontodatenansicht gegen Original', ['-m', 'tests.kontodaten_pruefen']),
        # Änderung 2.035: Mitgliederansicht mit lokalen Beispieldaten vergleichen.
        ('Mitgliederansicht gegen Original', ['-m', 'tests.mitglieder_pruefen']),
        # Änderung 2.034: Abnehmeransicht mit lokalen Beispieldaten vergleichen.
        ('Abnehmeransicht gegen Original', ['-m', 'tests.abnehmer_pruefen']),
        # Änderung 2.033: Gebundene Zählermethoden mit lokalen Beispieldaten vergleichen.
        ('Zähleransicht gegen Original', ['-m', 'tests.zaehler_pruefen']),
        # Änderung: Parallele Tests und verwaiste Fensterprozesse verhindern.
        ('Testprozesse und Startsperre', ['-m', 'tests.testprozesse_pruefen']),
        # Änderung: Ausgelagerte Abschlagsansicht mit Beispieldaten gegen Original prüfen.
        ('Abschlagsansicht gegen Original', ['-m', 'tests.abschlag_pruefen']),
        # Änderung für v2: Prüfprogramme aus ihrem eigenen Paket starten.
        ('Jahresabrechnung gegen Referenz', ['-m', 'tests.referenz_pruefen', 'pruefen']),
        ('Berechnung und Abbruchbedingungen', ['-m', 'tests.berechnungen_pruefen']),
        ('Rückvergütung gegen Referenz', ['-m', 'tests.rueckverguetung_pruefen', 'pruefen']),
        ('Buchungs-CSV und freigegebene Fehlerkorrekturen', ['-m', 'tests.buchungsvorlagen_pruefen', 'pruefen']),
        ('Dateien, INI, Pfade und Strukturvergleich', ['-m', 'tests.dateihilfen_pruefen']),
        ('Dokumentfelder und simulierte Dokumentaufrufe', ['-m', 'tests.dokumente_pruefen']),
    ]
    bericht = ['# Prüfbericht ANA – aktueller Arbeitsstand', '',
               '<!-- Änderung für v2: Nur Prüfstatus veröffentlichen, keine Beispieldaten. -->', '',
               'Stand: ' + datetime.now().strftime('%d.%m.%Y'), '',
               'Umgebung: Windows, Python ' + sys.version.split()[0] + '.', '']
    erfolgreich = True
    for name, argumente in pruefungen:
        # Änderung für v2: Vollständige Werkzeugausgaben nur in lokalem Prüfprotokoll ablegen.
        ergebnis = subprocess.run([sys.executable, *argumente], cwd=basis,
                                  capture_output=True, text=True, errors='replace')
        lokal = basis / '.lokal'
        lokal.mkdir(exist_ok=True)
        (lokal / ('freigabe-' + argumente[1] + '.log')).write_text(
            ergebnis.stdout + ergebnis.stderr, encoding='utf-8')
        status = 'bestanden' if ergebnis.returncode == 0 else 'nicht bestanden'
        erfolgreich = erfolgreich and ergebnis.returncode == 0
        print(name + ': ' + status, flush=True)
        bericht.append('- ' + name + ': ' + status + '.')
    # Änderung für v2: Alle Quellen kompilieren, ohne die Anwendung zu starten.
    try:
        # Änderung für v2: Nur Quellordner prüfen, keine lokalen Daten-/Buildverzeichnisse.
        for ordner in (basis, basis / 'anwendung', basis / 'tests', basis / 'scripts'):
            for datei in ordner.glob('*.py'):
                compile(datei.read_text(encoding='utf-8-sig'), datei.name, 'exec')
        bericht.append('- Syntax aller Python-Dateien: bestanden.')
    except Exception:
        erfolgreich = False
        bericht.append('- Syntax aller Python-Dateien: nicht bestanden.')
    # Änderung: Abgeschlossenen vollständigen Rückvergütungslauf vom 06.11.2026 dokumentieren.
    bericht += ['', 'Bereits durchgeführte Praxistests: Jahresabrechnung und Rückvergütung über die',
                'Oberfläche berechnet, gespeichert und als echte Word-/PDF-Dateien erzeugt.',
                'Dafür wurden isolierte lokale Datenkopien verwendet. Am 06.11.2026 wurde',
                'der vollständige Rückvergütungs-Dokumentlauf mit 73 Word-Dateien und 73',
                'lesbaren PDFs bestanden; CSV-Referenz und Originalbestand wurden geprüft.',
                'Eine visuelle Dokumentprüfung fand aus',
                'Datenschutzgründen nicht im KI-Kontext statt.', '']
    # Änderung 2.03: Vollständigen Abrechnungslauf nach Auslagerung dokumentieren.
    bericht += ['Am 06.11.2026 wurde auch der vollständige Abrechnungslauf nach der',
                'Auslagerung der Oberfläche bestanden: 73 Word-Dateien und 73 lesbare PDFs.',
                'CSV-Referenz und unveränderter Originalbestand wurden geprüft. Gegenüber',
                'dem unmittelbar vorherigen Lauf sind Word-Paketinhalte, PDF-Seitenzahlen',
                'und extrahierte PDF-Texte identisch. Keine visuelle Layoutprüfung.', '']
    # Änderung 2.031: Abgeschlossene Prüfung der Abschlagsauslagerung dokumentieren.
    bericht += ['Version 2.031: Abschlagsspalten, Bearbeiten, Upload und CSV-Speicherung',
                'wurden mit lokalen Beispieldaten gegen das Original geprüft. Der Strukturvergleich',
                'bestätigt alle verschobenen Methoden und die verbliebenen Einstiegspunkte.',
                'Die echte Abschlagstabelle und der anschließende vollständige Abrechnungslauf',
                'wurden am 06.11.2026 mit einer isolierten Datenkopie geprüft: CSV-Referenz',
                'identisch, 73 neue Word-Dateien und 73 lesbare PDFs, Originalbestand unverändert.',
                'Bearbeiten und Speichern der Abschläge wurden über gebundene Methoden geprüft;',
                'im Browser wurde die Tabellenanzeige geprüft. Keine visuelle Dokumentprüfung.',
                'Für 2.031 wurde keine neue Windows-EXE erstellt oder geprüft.', '']
    # Änderung 2.032: Tatsächlich geprüfte vollständige Prozessbereinigung festhalten.
    bericht += ['Version 2.032: Windows-Prozessgruppe und Startsperre mit echten Unterprozessen', 'geprüft. Auch ein nach dem Elternprozess weiterlaufendes Kind wurde nach Erfolg', 'und simuliertem Testfehler beendet; ein konkurrierender Teststart wurde blockiert.', 'Vollständiger Beispieldaten-Praxislauf am 06.11.2026 bestanden: Abschlagstabelle,', 'Abrechnung, CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs.', 'Original-Beispieldaten unverändert. Während des Laufs genau ein ANA-Testhauptprozess', 'und ein Fensterprozess bestätigt; anschließend null ANA-Prozesse und null Testbrowser.', 'Frühere Angaben zur vollständigen Fensterbereinigung waren unzutreffend und sind', 'mit diesem Stand korrigiert. Keine neue EXE; keine visuelle Dokumentprüfung.', '']
    # Änderung 2.033: Abgeschlossenen lokalen Zähler-Praxislauf dokumentieren.
    bericht += ['Version 2.033: Alle ausgelagerten Zählermethoden und Adapter strukturell',
                'gegen das Original geprüft. Gebundene Methoden mit lokalen Beispieldaten',
                'für Import, Sortierung, Bearbeitung, Korrekturdialoge und CSV-Speicherung',
                'verglichen. Visualisierungsimport einschließlich Zählerwechsel und',
                'Formatabweisung geprüft. Echtes Zählerregister und vollständige Abrechnung',
                'am 06.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,',
                '73 neue Word-Dateien und 73 lesbare PDFs; Originalbestand per SHA256 unverändert.',
                'Gegenüber dem vorherigen Praxislauf: alle Word-Paketinhalte sowie PDF-Seitenzahlen',
                'und extrahierten Texte identisch.',
                'Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.',
                'Keine visuelle Dokumentprüfung im Modellkontext.', '']
    # Änderung 2.034: Abgeschlossenen Abnehmer-Praxislauf festhalten.
    bericht += ['Version 2.034: Alle acht ausgelagerten Abnehmermethoden und Adapter gegen',
                'das Original strukturell geprüft. Gebundene Methoden mit lokalen Beispieldaten',
                'für Spalten, Bearbeiten einschließlich Nullwerten und Abschlagsänderung,',
                'CSV-Speicherung, Upload und Formatabweisung verglichen.',
                'Echtes Abnehmerregister und vollständiger Abrechnungslauf am 08.11.2026',
                'mit isolierter Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien',
                'und 73 lesbare PDFs; Originalbestand per SHA256 unverändert.',
                'Gegenüber 2.033: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.',
                'Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.',
                'Keine visuelle Dokumentprüfung. Eine vorzeitig neben dem Praxislauf gestartete',
                'Prozessprüfung wurde von der Startsperre blockiert; die abschließende gebündelte',
                'Freigabeprüfung erfolgte nach Ende des Praxislaufs.', '']
    # Änderung 2.035: Abgeschlossenen Mitglieder-Praxislauf dokumentieren.
    bericht += ['Version 2.035: Alle 22 Mitgliedermethoden und Adapter einschließlich',
                'asynchroner Abläufe und verschachtelter Dialogfunktionen strukturell gegen',
                'das Original geprüft. Gebundene Methoden für Filter, Sortierungen, Auswahl,',
                'Upload/Formatabweisung, Speichern, CSV-Export und beide Word-Mitgliederlisten',
                'mit lokalen Beispieldaten verglichen. Bei lückenhaften Wartungsspalten bleibt',
                'der bereits im Original vorhandene KeyError unverändert; dies wurde verglichen.',
                'Die Auslagerung behebt diesen bestehenden Daten-/Filterfehler nicht.',
                'Echtes Mitgliederregister und vollständige Abrechnung am 08.11.2026 mit',
                'isolierter Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien',
                'und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.',
                'Gegenüber 2.034: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.',
                'Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.',
                'Keine visuelle Dokumentprüfung im Modellkontext. Bearbeitungs-, Wartungs-',
                'und Serienbriefdialoge strukturell geprüft; kein vollständiger interaktiver',
                'Durchlauf aller Dialogkombinationen. Erster App-Start wegen fehlender',
                'Hilfsimporte fehlgeschlagen; nach Korrektur vollständiger Praxislauf bestanden.', '']
    # Änderung 2.036: Abgeschlossenen Kontodaten-Praxislauf dokumentieren.
    bericht += ['Version 2.036: Alle acht ausgelagerten Kontodatenmethoden und Adapter',
                'strukturell gegen das Original geprüft. Gebundene Methoden mit lokalen',
                'Beispieldaten für Spalten, Freitext-/Datumsänderung, leere Eingabe, gültige',
                'und ungültige IBAN, Laden, byteidentische CSV-Speicherung und Upload verglichen.',
                'Ungeeignete Uploadformate lösen weiterhin denselben Fehler wie im Original aus.',
                'Buchungs-CSV-Referenzprüfung verwendet die echte gebundene Kontolademethode.',
                'Register Buchungsvorlagen mit echter Kontodatentabelle und vollständiger',
                'Abrechnung am 08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz',
                'identisch, 73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per',
                'SHA256 unverändert. Gegenüber 2.035: Word-Paketinhalte, PDF-Seitenzahlen',
                'und Texte identisch. Test-App, Fenster und Browser vollständig beendet.',
                'Erster Praxisversuch wegen falscher Registerbezeichnung im Test gescheitert;',
                'korrigierter vollständiger Lauf bestanden. Keine neue Windows-EXE.',
                'Keine visuelle Dokumentprüfung im Modellkontext. Bearbeitung und Import',
                'über gebundene Methoden geprüft; im Browser wurde die Tabellenanzeige geprüft.', '']
    # Änderung 2.037: Abgeschlossenen Werkzeuge-Praxislauf dokumentieren.
    bericht += ['Version 2.037: Alle sechs Werkzeugmethoden samt drei asynchronen',
                'Ordnerauswahlen und Adaptern strukturell gegen das Original geprüft.',
                'Gebundene Methoden mit lokalen PDF-Beispieldateien verglichen: Ordnerwahl',
                'und Abbruch, fehlende Ordner, leere Eingabeordner, ID-Ermittlung, fehlende',
                'und mehrfache Zuordnungen, Hinweise und Fortschritt. Zusammengefügte PDFs',
                'bytegleich zum Original; Seitenzahl, Seitenreihenfolge und Texte bestätigt.',
                'Native Ordnerdialoge wurden durch lokale Testantworten ersetzt.',
                'Echtes Tools-Register und vollständige Abrechnung am 08.11.2026 mit isolierter',
                'Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien und 73',
                'lesbare PDFs. Originalbestand per SHA256 unverändert. Gegenüber 2.036:',
                'Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch. Test-App, Fenster',
                'und Browser vollständig beendet. Keine neue Windows-EXE.',
                'Keine visuelle Dokumentprüfung im Modellkontext. PDF-Zusammenfügen über',
                'gebundene Methoden geprüft; im Browser die Werkzeugeanzeige geprüft.', '']
    # Änderung 2.038: Abgeschlossenen Einstellungs-Praxislauf dokumentieren.
    bericht += ['Version 2.038: Alle vier Einstellungsmethoden und Adapter einschließlich',
                'asynchroner Ordnerwahl strukturell gegen Original geprüft. Gebundene Methoden',
                'mit lokalen Konfigurationskopien verglichen: bytegleiche Anwendungs- und',
                'Betreiber-INI, unveränderter/geänderter/leerer Arbeitsordner, Neustartnachfrage,',
                'Dialogabschluss, erneuter Ladeaufruf, Standard-Rücksetzung, Ordnerwahl und Abbruch.',
                'Originalkonfigurationen unverändert. Native Ordnerdialoge durch Testantworten',
                'ersetzt; tatsächliches Herunterfahren nach Arbeitsordnerwechsel nicht ausgeführt.',
                'Echter Einstellungsdialog geöffnet und abgebrochen; vollständige Abrechnung',
                'am 08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,',
                '73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.',
                'Gegenüber 2.037: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.',
                'Test-App, Fenster und Browser vollständig beendet. Erster Dialogtest startete',
                'zu früh; nach Warten auf den Button vollständiger Praxislauf bestanden.',
                'Keine neue Windows-EXE; keine visuelle Dokumentprüfung im Modellkontext.', '']
    # Änderung 2.039: Abgeschlossenen Changelog-Praxislauf dokumentieren.
    bericht += ['Version 2.039: Alle drei Changelog-Anzeigemethoden und Adapter strukturell',
                'gegen Original geprüft. Schreibfunktionen unverändert. Gebundene Methoden für',
                'alle acht Filter sowie Filter ohne Treffer, fehlende/leere Protokolldateien',
                'und Markdown-Zeilenumbrüche gegen Original verglichen. Aktualisierung nach',
                'beiden Schreibfunktionen geprüft; Protokolldateien bei festen Zeitstempeln',
                'bytegleich. Die Beispieldaten enthalten kein Changelog; Prüfeinträge wurden',
                'ausschließlich lokal aus Beispielmitgliederdaten abgeleitet.',
                'Echtes Changelog-Register mit Filteranzeige und vollständige Abrechnung am',
                '08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,',
                '73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.',
                'Gegenüber 2.038: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.',
                'Test-App, Fenster und Browser vollständig beendet. Filterinhalte über gebundene',
                'Methoden geprüft; im Browser die Register- und Filteranzeige geprüft.',
                'Keine neue Windows-EXE; keine visuelle Dokumentprüfung im Modellkontext.', '']
    # Änderung für v2: Einen EXE-Test nur für das tatsächlich geprüfte Paket bestätigen.
    paket = basis / 'release' / 'ANA-2.00-Windows-x64.zip'
    pruefsumme = basis / '.lokal' / 'exe-smoketest.sha256'
    # Änderung für v2: Ein Paket des veröffentlichten Stands bestätigt keine nachträglichen Quelländerungen.
    # Änderung für v2: Prüfungen auch aus einem Quellarchiv ohne Git-Installation ermöglichen.
    try:
        sauber = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=basis,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except FileNotFoundError:
        sauber = False
    if sauber and paket.is_file() and pruefsumme.is_file() and (
            hashlib.sha256(paket.read_bytes()).hexdigest() == pruefsumme.read_text(encoding='utf-8-sig').strip().lower()):
        bericht += ['Windows-Paket: Start aus dem fertigen ZIP ohne Beispieldaten bestanden.',
                    'Natives Fenster, lokale HTTP-Oberfläche und Versionsanzeige 2.00 geprüft.', '']
    else:
        bericht += ['Vorhandene Release-Archive werden nicht als Nachweis für nachträgliche Quelländerungen verwendet.',
                    'Separate Prüfungen der Verzeichnisumstellung sind in docs/STRUKTUR.md dokumentiert.', '']
    (basis / 'docs' / 'TESTBERICHT.md').write_text('\n'.join(bericht), encoding='utf-8')
    return 0 if erfolgreich else 1


if __name__ == '__main__':
    sys.exit(main())
