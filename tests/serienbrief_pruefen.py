"""Änderung nach 2.049: Echte Serienbriefe mit lokalen Vorlagen und Daten prüfen."""
import ast
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock

from docx import Document
from lxml import etree
from mailmerge import MailMerge

import anwendung.mitglieder_ui as modul
from anwendung.datenhaltung import datei_oeffnen
from anwendung.einstellungen import ini_datei_lesen
from anwendung.serienbrief_formatierung import fettmarkierungen_anwenden


def pruefen():
    # Änderung: Den tatsächlichen verschachtelten Export synchron und ohne UI ausführen.
    basis = Path(__file__).resolve().parents[1]
    daten = Path(ini_datei_lesen(basis / 'ana.ini')['Anwendung']['Arbeitsordner'])
    quelle = daten / 'Datenbank' / 'db_mitglieder.csv'
    vorher = quelle.read_bytes()
    baum = ast.parse((basis / 'anwendung/mitglieder_ui.py').read_text(encoding='utf-8'))
    dialog = next(k for k in ast.walk(baum) if isinstance(k, ast.FunctionDef) and k.name == 'serienbrief_dialog')
    funktionen = [deepcopy(k) for k in dialog.body if isinstance(k, ast.FunctionDef)
                  and k.name in ('ersetze_variablen', 'serienbrief_erstellen')]
    with TemporaryDirectory(dir=basis / '.lokal') as tmp:
        ausgabe = Path(tmp) / 'word'
        app = SimpleNamespace(ordner_vorlagen=str(daten / 'Vorlagen'))
        ansicht = SimpleNamespace(anwendung=app, ordner_serienbrief=str(ausgabe),
                                 mitglieder_tabelle=datei_oeffnen(quelle),
                                 radio_filter=SimpleNamespace(value='Name'), mgl_progress=Mock())
        umgebung = dict(vars(modul), self=ansicht, ui=Mock(), time=SimpleNamespace(sleep=lambda _: None))
        exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'serienbrief_test', 'exec'), umgebung)
        umgebung['serienbrief_erstellen']('Formatprüfung', 'Normal <bold>%[Name]%</bold> Ende\n<bold>Zeile 1\nZeile 2</bold>')
        dateien = list(ausgabe.glob('*.docx'))
        assert dateien and len(dateien) == len(ansicht.mitglieder_tabelle)
        for datei in dateien:
            doc = Document(datei)
            text = '\n'.join(p.text for p in doc.paragraphs)
            assert '<bold>' not in text and '</bold>' not in text
            assert 'Normal ' in text and ' Ende' in text
            assert any(r.bold and r.text for p in doc.paragraphs for r in p.runs)
            assert any(r.bold and 'Zeile 1' in r.text for p in doc.paragraphs for r in p.runs)
            assert any(r.bold and 'Zeile 2' in r.text for p in doc.paragraphs for r in p.runs)
        assert quelle.read_bytes() == vorher
        # Änderung: Ohne Markierungen müssen alle Vorlagenteile exakt unverändert bleiben.
        with MailMerge(str(daten / 'Vorlagen' / 'Vorlage-Serienbrief.docx')) as dokument:
            dokument.merge(Betreff='Unverändert', Text='Normal\nWeitere Zeile')
            vorher_xml = {name: etree.tostring(teil) for name, teil in dokument.parts.items()}
            fettmarkierungen_anwenden(dokument)
            assert vorher_xml == {name: etree.tostring(teil) for name, teil in dokument.parts.items()}
    # Änderung: Aufgeteilte Markierungen, Vorlagenstil, Umbrüche und ungültige Paare prüfen.
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    p = etree.Element(w + 'p')
    for text in ('Vor <bo', 'ld>Fett', '\nmehr</bo', 'ld> nach <bold>offen'):
        r = etree.SubElement(p, w + 'r')
        etree.SubElement(r, w + 't').text = text
    fettmarkierungen_anwenden(SimpleNamespace(parts={'test': p}))
    assert ''.join(p.itertext()) == 'Vor Fett\nmehr nach <bold>offen'
    assert ''.join(r.find(w + 't').text for r in p if r.find(w + 'rPr/' + w + 'b') is not None) == 'Fett\nmehr'
    print('Serienbrief: lokale Beispieldaten, Word-Ausgabe und Fettmarkierungen bestanden.')


if __name__ == '__main__':
    pruefen()
