"""Änderung für v2: CSV-Buchungsexporte ausschließlich lokal bytegenau vergleichen.

Der native Speicherdialog wird durch einen lokalen Ausgabepfad ersetzt.
Originale Beispieldaten werden nur gelesen. Inhalte und Fehlermeldungen
werden nicht ausgegeben. Referenzdateien liegen unter .lokal.
"""

import ast
import asyncio
import contextlib
import copy
import csv
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

from datenhaltung import datei_oeffnen
from einstellungen import ini_datei_lesen

BASIS = Path(__file__).resolve().parent
REFERENZ = BASIS / '.lokal' / 'buchungsreferenz'
EXPORTNAMEN = ('csv_grundgebuehr', 'csv_abschlag', 'csv_abrechnung_lastschrift',
               'csv_abrechnung_ueberweisung', 'csv_rueckv')


def umgebung_laden(original, daten):
    # Änderung für v2: Originalfunktionen ohne Import/Start der Anwendung laden.
    quelle = BASIS.parent / '_Vorlagen' / 'ana' / 'ana.py' if original else BASIS / 'ana.py'
    baum = ast.parse(quelle.read_text(encoding='utf-8-sig'))
    namen = set(EXPORTNAMEN) | {name + '_speichern' for name in EXPORTNAMEN}
    namen |= {'buchung_datei_speichern', 'konto_aus_db', 'db_datei_oeffnen', 'tablefields_to_dotfloat'}
    if original:
        namen |= {'round_half_up', 'dictlist_to_csv'}
    funktionen = [k for k in baum.body if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) and k.name in namen]
    assert {k.name for k in funktionen} == namen
    umgebung = {'datetime': datetime, 'Decimal': Decimal, 'ROUND_HALF_UP': ROUND_HALF_UP,
                'Path': Path, 'csv': __import__('csv'), 'datei_oeffnen': datei_oeffnen,
                'ordner_datenbank': str(daten / 'Datenbank'), 'db_konto': 'db_kontodaten.csv',
                'ordner_abrechnungen': str(daten / 'Abrechnungen'),
                'ordner_rueckv': str(daten / 'Rückvergütungen'),
                'konto_grid_ui': SimpleNamespace(refresh=lambda: None),
                'webview': SimpleNamespace(SAVE_DIALOG=0)}
    if not original:
        # Änderung für v2: Tatsächliche ausgelagerte Exportfunktionen verwenden.
        import buchungsvorlagen
        umgebung.update({name: getattr(buchungsvorlagen, name) for name in (
            'grundgebuehr_csv', 'abschlag_csv', 'abrechnung_lastschrift_csv',
            'abrechnung_ueberweisung_csv', 'rueckverguetung_csv')})
    exec(compile(ast.Module(body=funktionen, type_ignores=[]), 'buchungsexporte', 'exec'), umgebung)
    betreiber = ini_datei_lesen(daten / 'ana-betreiber.ini')['Betreiber']
    umgebung.update({'betreiber_name': betreiber['BetreiberName'],
                     'betreiber_iban': betreiber['BetreiberIBAN'],
                     'betreiber_glaeubigerid': betreiber['GlaeubigerID'],
                     'grundgebuehr': float(betreiber['Grundgebuehr'])})
    umgebung['konto_db'] = datei_oeffnen(daten / 'Datenbank' / 'db_kontodaten.csv')
    umgebung['abschlag_db'] = umgebung['tablefields_to_dotfloat'](
        datei_oeffnen(daten / 'Datenbank' / 'db_abschlag.csv'))
    return umgebung


def faelle_erstellen(daten, umgebung):
    # Änderung für v2: Alle vorhandenen Jahre, Quartale und beide Netto-Schalterstellungen prüfen.
    faelle = [{'export': 'csv_grundgebuehr'}]
    for feld in umgebung['abschlag_db'][0]:
        if 'Abschlag-' in feld:
            for quartal in ('Q1', 'Q2', 'Q3', 'Q4'):
                faelle.append({'export': 'csv_abschlag', 'jahr': feld[-4:], 'quartal': quartal})
    for datei in sorted((daten / 'Abrechnungen').glob('Abrechnung-*/Abrechnung-*.csv')):
        jahr = datei.parent.name[-4:]
        for export in ('csv_abrechnung_lastschrift', 'csv_abrechnung_ueberweisung'):
            for netto in (False, True):
                faelle.append({'export': export, 'jahr': jahr, 'netto': netto})
    for datei in sorted((daten / 'Rückvergütungen').glob('Rückvergütung-*/Rückvergütung-*.csv')):
        for netto in (False, True):
            faelle.append({'export': 'csv_rueckv', 'jahr': datei.parent.name[-4:], 'netto': netto})
    return faelle


def fall_ausfuehren(umgebung, fall, ausgabe):
    # Änderung für v2: Originalen asynchronen Speicherablauf inklusive Textmodus ausführen.
    meldungen = []
    async def speichern(*args, **kwargs):
        return str(ausgabe)
    umgebung.update({
        'abschlagsjahr_dropdown': SimpleNamespace(value=fall.get('jahr')),
        'quartal_dropdown': SimpleNamespace(value=fall.get('quartal')),
        'abrechnungsjahr_dropdown': SimpleNamespace(value=fall.get('jahr')),
        'rueckvjahr_dropdown': SimpleNamespace(value=fall.get('jahr')),
        'vonnetto_switch': SimpleNamespace(value=fall.get('netto')),
        'app': SimpleNamespace(native=SimpleNamespace(main_window=SimpleNamespace(create_file_dialog=speichern))),
        'ui': SimpleNamespace(notify=lambda *args, **kwargs: meldungen.append(True)),
    })
    vorher = copy.deepcopy((umgebung['konto_db'], umgebung['abschlag_db']))
    try:
        asyncio.run(umgebung[fall['export'] + '_speichern']())
        assert ausgabe.is_file() and len(meldungen) == 1
        status = {'status': 'ok'}
    except Exception as fehler:
        # Änderung für v2: Bestehende Fehler erfassen, ohne sie während des Umbaus zu korrigieren.
        if isinstance(fehler, AssertionError):
            raise
        status = {'status': 'fehler', 'typ': type(fehler).__name__}
    assert vorher == (umgebung['konto_db'], umgebung['abschlag_db'])
    return status


def korrektur_pruefen(ausgabe, fall, daten, konten):
    # Änderung für v2: Freigegebene Fehlerkorrekturen unabhängig von der Exportfunktion prüfen.
    # Nur vorhandene Beispieldaten lokal verwenden; CSV-Beträge nicht ausgeben.
    quelle = daten / 'Rückvergütungen' / ('Rückvergütung-' + fall['jahr']) / ('Rückvergütung-' + fall['jahr'] + '.csv')
    rueckv = datei_oeffnen(quelle)
    betraege = []
    for konto in konten:
        for zeile in rueckv:
            if konto['Ident'] != zeile['Ident']:
                continue
            if fall['netto']:
                # Unabhängige Sollberechnung mit kaufmännischer Rundung auf Cent.
                assert 'MwSt bis ZA' not in rueckv[0]
                netto = Decimal(zeile['Rückvergütung Netto'])
                mwst = Decimal(zeile['MwSt-Satz'])
                brutto = (netto + netto * mwst / Decimal(100)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP)
                betraege.append(str(float(brutto)).replace('.', ','))
            else:
                assert 'MwSt bis ZA' in rueckv[0]
                betraege.append(str(zeile['Rückvergütung gesamt']).replace('.', ','))
    with ausgabe.open() as datei:
        geschrieben = list(csv.DictReader(datei, delimiter=';'))
    assert betraege and [zeile['Betrag'] for zeile in geschrieben] == betraege


def main():
    if sys.argv[1:] not in (['erstellen'], ['pruefen']):
        print('Aufruf: python buchungsvorlagen_pruefen.py erstellen | pruefen')
        return 2
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            daten = Path(ini_datei_lesen(BASIS / 'ana.ini')['Anwendung']['Arbeitsordner']).resolve()
            assert daten == (BASIS.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
            alt = umgebung_laden(True, daten)
            faelle = faelle_erstellen(daten, alt)
            if sys.argv[1] == 'erstellen':
                assert not REFERENZ.exists()
                REFERENZ.mkdir(parents=True)
                manifest = []
                for nummer, fall in enumerate(faelle):
                    status = fall_ausfuehren(alt, fall, REFERENZ / ('fall-' + str(nummer) + '.csv'))
                    manifest.append({'fall': fall, **status})
                (REFERENZ / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            else:
                neu = umgebung_laden(False, daten)
                manifest = json.loads((REFERENZ / 'manifest.json').read_text(encoding='utf-8'))
                assert faelle == [eintrag['fall'] for eintrag in manifest]
                korrekturen = set()
                with tempfile.TemporaryDirectory(dir=BASIS / '.lokal') as temp:
                    for nummer, eintrag in enumerate(manifest):
                        links, rechts = Path(temp) / 'alt.csv', Path(temp) / 'neu.csv'
                        for pfad in (links, rechts):
                            if pfad.exists():
                                pfad.unlink()
                        vorher = fall_ausfuehren(alt, eintrag['fall'], links)
                        nachher = fall_ausfuehren(neu, eintrag['fall'], rechts)
                        # Änderung für v2: Originalreferenzen unverändert lassen; nur die zwei
                        # ausdrücklich freigegebenen Fehler dürfen jetzt erfolgreich exportieren.
                        assert vorher == {k: v for k, v in eintrag.items() if k != 'fall'}
                        assert nachher == {'status': 'ok'}
                        if vorher['status'] == 'ok':
                            assert links.read_bytes() == rechts.read_bytes() == (
                                REFERENZ / ('fall-' + str(nummer) + '.csv')).read_bytes()
                        else:
                            assert eintrag['fall']['export'] == 'csv_rueckv'
                            variante = (eintrag['fall']['netto'], vorher['typ'])
                            assert variante in {(False, 'KeyError'), (True, 'TypeError')}
                            korrektur_pruefen(rechts, eintrag['fall'], daten, neu['konto_db'])
                            korrekturen.add(variante)
                assert korrekturen == {(False, 'KeyError'), (True, 'TypeError')}
            alle_arten = {m['fall']['export'] for m in manifest if m['status'] == 'ok'}
            vorhandene_fehler = any(m['status'] != 'ok' for m in manifest)
        print('Buchungsreferenzen lokal erstellt.' if sys.argv[1] == 'erstellen'
              else 'Unveränderte Exporte bytegleich; beide Fehlerkorrekturen und Sollbeträge geprüft.')
        print('Erfolgreicher Export für alle fünf Vorlagenarten vorhanden: ' + str(set(EXPORTNAMEN) == alle_arten))
        if vorhandene_fehler and sys.argv[1] == 'erstellen':
            print('Hinweis: Einzelne Exportvarianten scheitern bereits in der Vorlage; Verhalten beibehalten.')
            # Änderung für v2: Nur feste Funktionsnamen, Schalterstellung und Fehlertyp melden.
            # Keine Jahre, Namen, Kontodaten oder Fehlermeldungstexte ausgeben.
            varianten = {(m['fall']['export'], bool(m['fall'].get('netto')), m['typ'])
                         for m in manifest if m['status'] == 'fehler'}
            for export, netto, typ in sorted(varianten):
                print('Bestehender Fehler: ' + export + ', Netto-Modus: ' + str(netto) + ', Typ: ' + typ)
        return 0
    except Exception as fehler:
        print('Buchungsvorlagenprüfung nicht abgeschlossen. Fehlertyp: ' + type(fehler).__name__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
