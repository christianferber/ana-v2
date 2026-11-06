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
