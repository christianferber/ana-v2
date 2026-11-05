"""Änderung für v2: Lokale Freigabeprüfungen ohne Ausgabe von Beispieldaten bündeln."""

from datetime import datetime
from pathlib import Path
import hashlib
import subprocess
import sys


def main():
    basis = Path(__file__).resolve().parent
    pruefungen = [
        ('Jahresabrechnung gegen Referenz', ['referenz_pruefen.py', 'pruefen']),
        ('Berechnung und Abbruchbedingungen', ['berechnungen_pruefen.py']),
        ('Rückvergütung gegen Referenz', ['rueckverguetung_pruefen.py', 'pruefen']),
        ('Buchungs-CSV und freigegebene Fehlerkorrekturen', ['buchungsvorlagen_pruefen.py', 'pruefen']),
        ('Dateien, INI, Pfade und Strukturvergleich', ['dateihilfen_pruefen.py']),
        ('Dokumentfelder und simulierte Dokumentaufrufe', ['dokumente_pruefen.py']),
    ]
    bericht = ['# Freigabeprüfung ANA 2.00', '',
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
        (lokal / ('freigabe-' + argumente[0] + '.log')).write_text(
            ergebnis.stdout + ergebnis.stderr, encoding='utf-8')
        status = 'bestanden' if ergebnis.returncode == 0 else 'nicht bestanden'
        erfolgreich = erfolgreich and ergebnis.returncode == 0
        print(name + ': ' + status, flush=True)
        bericht.append('- ' + name + ': ' + status + '.')
    # Änderung für v2: Alle Quellen kompilieren, ohne die Anwendung zu starten.
    try:
        for datei in basis.glob('*.py'):
            compile(datei.read_text(encoding='utf-8-sig'), datei.name, 'exec')
        bericht.append('- Syntax aller Python-Dateien: bestanden.')
    except Exception:
        erfolgreich = False
        bericht.append('- Syntax aller Python-Dateien: nicht bestanden.')
    bericht += ['', 'Bereits durchgeführte Praxistests: Jahresabrechnung und Rückvergütung über die',
                'Oberfläche berechnet, gespeichert und als echte Word-/PDF-Dateien erzeugt.',
                'Dafür wurden isolierte lokale Datenkopien verwendet; bei der Rückvergütung',
                'ein vorhandener Datensatz. Der vollständige Rückvergütungs-Dokumentlauf',
                'überschritt das Testzeitlimit. Eine visuelle Dokumentprüfung fand aus',
                'Datenschutzgründen nicht im KI-Kontext statt.', '']
    # Änderung für v2: Einen EXE-Test nur für das tatsächlich geprüfte Paket bestätigen.
    paket = basis / 'release' / 'ANA-2.00-Windows-x64.zip'
    pruefsumme = basis / '.lokal' / 'exe-smoketest.sha256'
    if paket.is_file() and pruefsumme.is_file() and (
            hashlib.sha256(paket.read_bytes()).hexdigest() == pruefsumme.read_text(encoding='utf-8-sig').strip().lower()):
        bericht += ['Windows-Paket: Start aus dem fertigen ZIP ohne Beispieldaten bestanden.',
                    'Natives Fenster, lokale HTTP-Oberfläche und Versionsanzeige 2.00 geprüft.', '']
    else:
        bericht += ['Windows-Paket: Eine Startprüfung des aktuellen ZIPs steht noch aus.', '']
    (basis / 'TESTBERICHT.md').write_text('\n'.join(bericht), encoding='utf-8')
    return 0 if erfolgreich else 1


if __name__ == '__main__':
    sys.exit(main())
