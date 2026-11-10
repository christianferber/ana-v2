# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Eine echte Beispielabrechnung lokal als Word und PDF erzeugen.

Nur der freigegebene Beispielordner wird gelesen. Ausgaben liegen unter .lokal.
Es werden keine Dateninhalte oder datenhaltigen Dateinamen ausgegeben.
"""

import contextlib
from datetime import datetime
import io
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from mailmerge import MailMerge
from pypdf import PdfReader
from win32com.client import DispatchEx
import pythoncom

from anwendung.datenhaltung import datei_oeffnen
from anwendung import dokumente
# Änderung für v2: Dieselbe ausgelagerte Feldformatierung wie die Anwendung verwenden.
from anwendung.dokumentfelder import mapping_wordfelder
from anwendung.einstellungen import ini_datei_lesen


SCHRITT = 'Vorbereitung'


def erzeugen():
    global SCHRITT
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()

    # Änderung für v2: Nur eine gespeicherte Beispielabrechnung mit passender Vorlage auswählen.
    SCHRITT = 'Passende Vorlage suchen'
    for csv in sorted((daten / 'Abrechnungen').glob('Abrechnung-*/Abrechnung-*.csv'), reverse=True):
        jahr = csv.parent.name.removeprefix('Abrechnung-')
        vorlage = daten / 'Vorlagen' / ('Vorlage-Abrechnung-' + jahr + '.docx')
        if vorlage.is_file():
            zeilen = datei_oeffnen(csv)
            if zeilen:
                zeile = zeilen[0]
                break
    else:
        raise RuntimeError('Keine passende Kombination')

    # Änderung für v2: Eigener Ausgabeordner pro Lauf; bestehende Dokumente nicht überschreiben.
    ausgabe = basis / '.lokal' / ('dokumenttest-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    wordordner = ausgabe / 'word'
    pdfordner = ausgabe / 'pdf'
    wordordner.mkdir(parents=True)
    pdfordner.mkdir()

    SCHRITT = 'Word erzeugen'
    dokumente.abrechnung_word_schreiben([zeile], str(vorlage), str(wordordner), jahr,
                                       mapping_wordfelder)
    dateien = list(wordordner.glob('*.docx'))
    assert len(dateien) == 1
    worddatei = wordordner / 'Beispielabrechnung.docx'
    dateien[0].rename(worddatei)

    # Änderung für v2: DOCX-Paket lokal prüfen; keine XML-Inhalte ausgeben.
    with ZipFile(worddatei) as paket:
        assert paket.testzip() is None
        assert 'word/document.xml' in paket.namelist()
    with MailMerge(str(worddatei)) as dokument:
        assert not dokument.get_merge_fields()

    # Änderung für v2: Echte Word-Konvertierung in einer separaten Word-Instanz testen.
    # Dadurch wird eine bereits vom Benutzer geöffnete Word-Sitzung nicht beendet.
    SCHRITT = 'PDF mit Microsoft Word erzeugen'
    instanzen = []

    def word_starten(name):
        word = DispatchEx(name)
        instanzen.append(word)
        word.DisplayAlerts = 0
        return word

    try:
        # Änderung: Abrechnung verwendet jetzt ebenfalls eine eigene Word-Instanz.
        with patch.object(dokumente, 'DispatchEx', word_starten):
            dokumente.abrechnung_pdf_konvertieren(str(wordordner), str(pdfordner), lambda wert: None)
    finally:
        for word in instanzen:
            try:
                word.Quit()
            except Exception:
                pass
        # Änderung: COM wird bereits von der geprüften Konvertierungsfunktion freigegeben.

    SCHRITT = 'PDF prüfen'
    pdfdatei = pdfordner / 'Beispielabrechnung.pdf'
    assert pdfdatei.is_file() and pdfdatei.stat().st_size > 0
    pdf = PdfReader(pdfdatei)
    assert len(pdf.pages) > 0
    assert any((seite.extract_text() or '').strip() for seite in pdf.pages)

    # Änderung für v2: Nur selbst vergebene, datenfreie Ausgabepfade zurückgeben.
    return worddatei, pdfdatei


if __name__ == '__main__':
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            worddatei, pdfdatei = erzeugen()
        print('Word und PDF erzeugt; lokale Dateiprüfung bestanden.')
        print('WORD: ' + str(worddatei))
        print('PDF: ' + str(pdfdatei))
    except Exception as fehler:
        print('Praxistest nicht abgeschlossen. Schritt: ' + SCHRITT
              + '. Fehlertyp: ' + type(fehler).__name__)
        raise SystemExit(1)
