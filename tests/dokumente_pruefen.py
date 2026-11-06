# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Dokumentaufrufe lokal gegen die Vorlage vergleichen.

Word und PDF werden durch protokollierende Testobjekte ersetzt. Die Prüfung
startet kein Microsoft Word und schreibt keine Dokumente oder Beispieldaten.
"""

import ast
import contextlib
import copy
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from anwendung import dokumente
# Änderung für v2: Dokumenttests verwenden die tatsächlich ausgelagerte Feldformatierung.
from anwendung.dokumentfelder import mapping_wordfelder, format_fuer_serienbrief
from tests.referenz_pruefen import ergebnisse_berechnen
# Änderung für v2: Vorhandene Rückvergütungsbeispiele ausschließlich lokal laden.
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen


def pruefen():
    # Änderung für v2: Originalcode ohne GUI-Start für direkte Ablaufvergleiche laden.
    basis = Path(__file__).resolve().parents[1]
    quelle = basis.parent / '_Vorlagen' / 'ana' / 'ana.py'
    baum = ast.parse(quelle.read_text(encoding='utf-8-sig'))
    funktionen = {k.name: k for k in baum.body if isinstance(k, ast.FunctionDef)}
    namen = ('mapping_wordfelder', 'form_betrag', 'form_zaehler', 'form_mwst', 'form_rvsatz',
             'format_fuer_serienbrief',
             'abr_pdf_process', 'rueckv_pdf_process')
    umgebung = {}
    exec(compile(ast.Module(body=[funktionen[name] for name in namen], type_ignores=[]),
                 'original_dokumente', 'exec'), umgebung)
    schleife = next(k for k in funktionen['abrechnungen_word_erstellen'].body if isinstance(k, ast.For))
    original_word = compile(ast.Module(body=[schleife], type_ignores=[]), 'original_serienschleife', 'exec')

    # Änderung für v2: Echte Beispieldaten nur lokal in Aufrufprotokollen vergleichen.
    for fall in ergebnisse_berechnen():
        # Änderung für v2: Auch die bisherige Änderung der Serienbriefdaten vergleichen.
        links, rechts = copy.deepcopy(fall['ergebnis']), copy.deepcopy(fall['ergebnis'])
        assert umgebung['format_fuer_serienbrief'](links) == format_fuer_serienbrief(rechts)
        assert links == rechts
        protokoll = []

        class Serienbrief:
            def __init__(self, vorlage):
                protokoll.append(('vorlage', vorlage))

            def merge(self, **felder):
                protokoll.append(('felder', felder))

            def write(self, datei):
                protokoll.append(('datei', datei))

        umgebung.update({
            'abrechnung_fuer_pdf': copy.deepcopy(fall['ergebnis']),
            'datei_vorlage_abrechnung': 'vorlage.docx',
            'ordner_abrechnungen_word': 'word',
            'jahre_dropdown': SimpleNamespace(value=fall['jahr']),
            'MailMerge': Serienbrief,
        })
        exec(original_word, umgebung)
        vorher = copy.deepcopy(protokoll)
        protokoll.clear()
        with patch.object(dokumente, 'MailMerge', Serienbrief):
            dokumente.abrechnung_word_schreiben(copy.deepcopy(fall['ergebnis']), 'vorlage.docx',
                                               'word', fall['jahr'], mapping_wordfelder)
        assert protokoll == vorher

    # Änderung für v2: Auch Rückvergütungsfelder und Ausgabedateinamen vergleichen.
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    rueckv_schleife = next(k for k in funktionen['rueckv_word_erstellen'].body if isinstance(k, ast.For))
    original_rueckv = compile(ast.Module(body=[rueckv_schleife], type_ignores=[]),
                              'original_rueckverguetung', 'exec')
    gefunden = False
    for csv in (daten / 'Rückvergütungen').glob('Rückvergütung-*/Rückvergütung-*.csv'):
        zeilen = datei_oeffnen(csv)
        if not zeilen:
            continue
        gefunden = True
        jahr = csv.parent.name.removeprefix('Rückvergütung-')
        protokoll = []
        umgebung.update({'rueckv_fuer_pdf': copy.deepcopy(zeilen),
                         'datei_vorlage_rueckv': 'vorlage.docx', 'ordner_rueckv_word': 'word',
                         'rueckv_jahre_dropdown': SimpleNamespace(value=jahr), 'MailMerge': Serienbrief})
        exec(original_rueckv, umgebung)
        vorher = copy.deepcopy(protokoll)
        protokoll.clear()
        with patch.object(dokumente, 'MailMerge', Serienbrief):
            dokumente.rueckverguetung_word_schreiben(copy.deepcopy(zeilen), 'vorlage.docx',
                                                   'word', jahr, mapping_wordfelder)
        assert protokoll == vorher
    assert gefunden

    # Änderung: Dateifilter und Fortschritt weiterhin gegen das Original prüfen;
    # zusätzlich eine einzige Word-Sitzung und Freigabe im Fehlerfall absichern.
    for dateien in (['a.docx', 'b.DOCX', 'c.docx', 'd.docx', 'ignorieren.txt'], []):
        protokoll = []
        def konvertieren(quelle, ziel):
            protokoll.append(('konvertieren', quelle, ziel))
        def rueckv_fortschritt(wert):
            protokoll.append(('fortschritt', wert))
        com = SimpleNamespace(CoInitialize=lambda: None,
                              CoUninitialize=lambda: None)
        umgebung.update({'pythoncom': com, 'os': dokumente.os, 'convert': konvertieren,
                         'ordner_rueckv_word': 'word', 'ordner_rueckv_pdf': 'pdf',
                         'rueckv_progress_pdf': SimpleNamespace(set_value=rueckv_fortschritt)})
        with patch.object(dokumente.os, 'listdir', return_value=dateien):
            umgebung['rueckv_pdf_process']()
            vorher = copy.deepcopy(protokoll)
            protokoll.clear()
            sitzungen = []
            class RueckvWord:
                def __init__(self):
                    self.Documents = self
                def Open(self, datei):
                    self.quelle = datei
                    return self
                def SaveAs(self, datei, FileFormat):
                    assert FileFormat == 17
                    konvertieren(self.quelle, datei)
                def Close(self, speichern):
                    assert speichern is False
                def Quit(self):
                    sitzungen.append('beendet')
            def rueckv_starten(name):
                assert name == 'Word.Application'
                sitzungen.append('gestartet')
                return RueckvWord()
            # Änderung: Neue COM-Aufrufe nutzen absolute Pfade; die Dateiauswahl
            # und Zielfile-Namen müssen weiterhin dem Original entsprechen.
            vorher = [(eintrag[0], dokumente.os.path.abspath(eintrag[1]),
                       dokumente.os.path.abspath(eintrag[2]))
                      if eintrag[0] == 'konvertieren' else eintrag for eintrag in vorher]
            with patch.object(dokumente, 'pythoncom', com), patch.object(dokumente, 'DispatchEx', rueckv_starten):
                dokumente.rueckverguetung_pdf_konvertieren('word', 'pdf', rueckv_fortschritt)
            assert protokoll == vorher
            assert sitzungen == (['gestartet', 'beendet'] if dateien else [])

    # Änderung: Beim Scheitern der PDF-Erstellung Dokument, Word und COM freigeben.
    aufraeumen = []
    class FehlerWord:
        def __init__(self):
            self.Documents = self
        def Open(self, datei):
            return self
        def SaveAs(self, datei, FileFormat):
            raise RuntimeError('Simulierter Konvertierungsfehler')
        def Close(self, speichern):
            aufraeumen.append('Dokument')
        def Quit(self):
            aufraeumen.append('Word')
    com = SimpleNamespace(CoInitialize=lambda: None,
                          CoUninitialize=lambda: aufraeumen.append('COM'))
    with patch.object(dokumente.os, 'listdir', return_value=['a.docx']), \
            patch.object(dokumente, 'pythoncom', com), \
            patch.object(dokumente, 'DispatchEx', lambda name: FehlerWord()):
        try:
            dokumente.rueckverguetung_pdf_konvertieren('word', 'pdf', lambda wert: None)
        except RuntimeError:
            pass
        else:
            raise AssertionError('Konvertierungsfehler wurde verschluckt')
    assert aufraeumen == ['Dokument', 'Word', 'COM']

    # Änderung für v2: COM-Reihenfolge, Dateifilter und Fortschrittswerte vergleichen.
    for dateien in (['a.docx', 'b.docx', 'ignorieren.txt'], ['a.DOCX'], []):
        protokoll = []

        class Word:
            def __init__(self):
                self.Documents = self

            def Open(self, datei):
                protokoll.append(('oeffnen', datei))
                return self

            def SaveAs(self, datei, FileFormat):
                protokoll.append(('speichern', datei, FileFormat))

            def Close(self, speichern):
                protokoll.append(('schliessen', speichern))

            def Quit(self):
                protokoll.append(('beenden',))

        def starten(name):
            protokoll.append(('starten', name))
            return Word()

        def fortschritt(wert):
            protokoll.append(('fortschritt', wert))

        com = SimpleNamespace(CoInitialize=lambda: protokoll.append(('com',)))
        umgebung.update({'pythoncom': com, 'Dispatch': starten, 'os': dokumente.os,
                         'ordner_abrechnungen_word': 'word', 'ordner_abrechnungen_pdf': 'pdf',
                         'abr_progress_pdf': SimpleNamespace(set_value=fortschritt)})
        with patch.object(dokumente.os, 'listdir', return_value=dateien):
            try:
                umgebung['abr_pdf_process']()
                vorher_fehler = None
            except Exception as fehler:
                vorher_fehler = type(fehler)
            vorher = copy.deepcopy(protokoll)
            protokoll.clear()
            with patch.object(dokumente, 'pythoncom', com), patch.object(dokumente, 'Dispatch', starten):
                try:
                    dokumente.abrechnung_pdf_konvertieren('word', 'pdf', fortschritt)
                    nachher_fehler = None
                except Exception as fehler:
                    nachher_fehler = type(fehler)
            assert protokoll == vorher and vorher_fehler == nachher_fehler


if __name__ == '__main__':
    try:
        # Änderung für v2: Keine Dateninhalte oder datenhaltigen Fehlermeldungen ausgeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Dokumentabläufe: Vergleich bestanden. Word/PDF-Aufrufe wurden simuliert.')
    except Exception as fehler:
        print('Dokumentprüfung nicht abgeschlossen. Fehlertyp: ' + type(fehler).__name__)
        raise SystemExit(1)
