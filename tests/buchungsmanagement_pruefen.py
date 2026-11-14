"""Änderung nach 2.06.00: Lokale PDF-Beispiele und gezielte Fehler-/Zuordnungsfälle."""
from collections import Counter
import asyncio
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from anwendung.buchungsmanagement import (
    betreff_schluessel, einstellungen_laden, einstellungen_speichern,
    kontoauszuege_lesen, rechnungen_pruefen, rechnungsbetrag_lesen, endbetrag_aus_texten, rechnungsname_lesen,
    ausblendungen_laden, ausblendungen_speichern, AUSBLENDUNGEN_DATEINAME,
    empfaenger_und_zweck, ist_ausgeblendet, regeln_ergaenzen, auswahl_regeln_aendern,
    buchungs_pruef_ids,
)
from anwendung import pdf_texterkennung


def csv_datenbank_pruefen(ziel, buchungen):
    # Änderung: Echte lokale Betreffe nur in einer Testdatenbank speichern; nie Inhalte ausgeben.
    from anwendung.buchungsmanagement_ui import BuchungsmanagementOberflaeche
    # Änderung: Die neue Unicode-CSV mit einem Standard-CSV-Parser prüfen, ohne alte Datenbankleser zu ändern.
    def datei_oeffnen(datei):
        with Path(datei).open(encoding='utf-8-sig', newline='') as quelle:
            return list(csv.DictReader(quelle, delimiter=';'))
    db_datei = ziel / AUSBLENDUNGEN_DATEINAME
    werte = {betreff_schluessel(b['betreff']) for b in buchungen}
    werte.add('sonderfirma; "äöü" 漢字')
    ausblendungen_speichern(db_datei, werte)
    assert ausblendungen_laden(db_datei) == [(w, '', '') for w in sorted(werte)]
    assert db_datei.read_bytes().startswith(b'\xef\xbb\xbf')
    assert [r['Betreff'] for r in datei_oeffnen(db_datei)] == sorted(werte)
    vorher = db_datei.read_bytes()
    with patch('anwendung.datenhaltung.os.replace', side_effect=OSError):
        try:
            ausblendungen_speichern(db_datei, [])
        except OSError:
            pass
        else:
            raise AssertionError('CSV-Schreibfehler fehlt.')
    assert db_datei.read_bytes() == vorher
    assert not list(ziel.glob('.ana-*.tmp'))
    ausblendungen_speichern(db_datei, [])
    assert ausblendungen_laden(db_datei) == []
    assert list(datei_oeffnen(db_datei)) == []
    for inhalt in ['', 'FalscherKopf\n', 'Betreff\nFirma;Zusatz\n', 'Betreff\n"offen\n', 'Betreff\n""\n']:
        db_datei.write_text(inhalt)
        muss_scheitern(lambda: ausblendungen_laden(db_datei))

    # Änderung: Migration, CSV-Vorrang, erneutes Laden und tatsächlichen Datenbankpfad prüfen.
    ordner = ziel / 'migration'
    ordner.mkdir()
    json_datei = ordner / 'buchungsmanagement.json'
    daten = {'kontoordner': 'konto', 'rechnungsordner': 'rechnung', 'ausgeblendet': [' FIRMA A ', 'Firma A']}
    json_datei.write_text(json.dumps(daten), encoding='utf-8')
    protokoll = []
    anwendung = SimpleNamespace(arbeitsordner=str(ordner), ordner_datenbank=str(ordner / 'Datenbank'),
                                change_log_info=lambda *eintrag: protokoll.append(eintrag))
    ansicht = BuchungsmanagementOberflaeche(anwendung)
    ansicht.kontopfad = SimpleNamespace(text='')
    ansicht.rechnungspfad = SimpleNamespace(text='')
    # Änderung: Fehlgeschlagene Übernahme muss die vollständige alte JSON-Datei erhalten.
    alt = json_datei.read_bytes()
    with patch('anwendung.buchungsmanagement_ui.ausblendungen_speichern', side_effect=OSError):
        try:
            ansicht.laden()
        except OSError:
            pass
        else:
            raise AssertionError('Migrationsfehler fehlt.')
    assert json_datei.read_bytes() == alt
    # Änderung: Auch ein Fehler beim anschließenden JSON-Aufräumen darf keine Regeln verlieren.
    with patch('anwendung.buchungsmanagement_ui.einstellungen_speichern', side_effect=OSError):
        try:
            ansicht.laden()
        except OSError:
            pass
        else:
            raise AssertionError('JSON-Aufräumfehler fehlt.')
    assert json_datei.read_bytes() == alt
    assert ausblendungen_laden(ordner / 'Datenbank' / AUSBLENDUNGEN_DATEINAME) == [('firma a', '', '')]
    ansicht.laden()
    assert ansicht.db_datei == ordner / 'Datenbank' / AUSBLENDUNGEN_DATEINAME
    assert ansicht.daten['ausgeblendet'] == [('firma a', '', '')]
    # Änderung: Einspaltige Vorgänger-CSV wird vollständig geprüft und verlustfrei erweitert.
    ansicht.db_datei.write_text('Betreff\nfirma a\n')
    alt_csv = ansicht.db_datei.read_bytes()
    with patch('anwendung.datenhaltung.os.replace', side_effect=OSError):
        try:
            ansicht.laden()
        except OSError:
            pass
        else:
            raise AssertionError('CSV-Formatmigrationsfehler fehlt.')
    assert ansicht.db_datei.read_bytes() == alt_csv
    ansicht.laden()
    assert list(datei_oeffnen(ansicht.db_datei)[0]) == ['Betreff', 'Empfaenger', 'Zweck']
    assert 'ausgeblendet' not in json.loads(json_datei.read_text(encoding='utf-8'))
    assert any(e[0] == 'DATENBANK' for e in protokoll)
    ansicht.ausschluesse_speichern(set())
    # Änderung: Stale JSON-Regeln dürfen eine in CSV reaktivierte Buchung nicht wieder verstecken.
    json_datei.write_text(json.dumps(daten), encoding='utf-8')
    ansicht.laden()
    assert ansicht.daten['ausgeblendet'] == []
    ansicht.ausschluesse_speichern({'firma b'})
    ansicht.laden()
    assert ansicht.daten['ausgeblendet'] == [('firma b', '', '')]
    # Änderung: Eine frische Ansicht übernimmt den auf Platte gespeicherten CSV-Bestand.
    neue_ansicht = BuchungsmanagementOberflaeche(anwendung)
    neue_ansicht.kontopfad = SimpleNamespace(text='')
    neue_ansicht.rechnungspfad = SimpleNamespace(text='')
    neue_ansicht.laden()
    assert neue_ansicht.daten['ausgeblendet'] == [('firma b', '', '')]
    ansicht.db_datei.write_text('FalscherKopf\n')
    json_datei.write_text(json.dumps(daten), encoding='utf-8')
    altes_json = json_datei.read_bytes()
    vorher = ansicht.db_datei.read_bytes()
    muss_scheitern(ansicht.laden)
    assert ansicht.db_datei.read_bytes() == vorher
    assert json_datei.read_bytes() == altes_json
    # Änderung: Wechsel des Arbeitsordners verwendet dessen unabhängige CSV-Datenbank.
    anderer = ziel / 'anderer-arbeitsordner'
    anderer.mkdir()
    anwendung.arbeitsordner = str(anderer)
    anwendung.ordner_datenbank = str(anderer / 'Datenbank')
    ansicht.laden()
    assert ansicht.daten['ausgeblendet'] == [] and ansicht.db_datei.is_file()
    assert ansicht.db_datei == anderer / 'Datenbank' / AUSBLENDUNGEN_DATEINAME
    # Änderung: Die vorhandene herkömmliche Datenbanksicherung muss die neue CSV mitnehmen.
    from anwendung.sicherung import Sicherung
    ansicht.ausschluesse_speichern({'firma c'})
    anwendung.ordner_sicherungen = str(anderer / 'Sicherungen')
    Path(anwendung.ordner_sicherungen).mkdir()
    sicherung = Sicherung(anwendung)
    anwendung.max_anzahl_ordner = sicherung.max_anzahl_ordner
    sicherung.db_sichern('CSV-Test')
    kopien = list(Path(anwendung.ordner_sicherungen).rglob(AUSBLENDUNGEN_DATEINAME))
    assert len(kopien) == 1 and kopien[0].read_bytes() == ansicht.db_datei.read_bytes()
    paarregeln_pruefen(ziel)


def paarregeln_pruefen(ziel):
    # Änderung: Neue Regeln unterscheiden gleiche Gegenpartei mit anderem Zweck und umgekehrt.
    assert empfaenger_und_zweck([' Firma A ', 'Grundgebühr', 'IBAN: DE00 0000 BIC: TEST']) == ('Firma A', 'Grundgebühr')
    assert empfaenger_und_zweck(['Firma A', 'SVWZ: Wartung', 'EREF: 123 MREF: 456']) == ('Firma A', 'Wartung')
    buchungen = [
        {'betreff': 'Erste Anzeige', 'empfaenger': 'Firma A', 'zweck': 'Grundgebühr'},
        {'betreff': 'Andere Anzeige', 'empfaenger': ' FIRMA  A ', 'zweck': ' GRUNDGEBÜHR '},
        {'betreff': 'Versicherung', 'empfaenger': 'Firma A', 'zweck': 'Versicherung'},
        {'betreff': 'Fremde Firma', 'empfaenger': 'Firma B', 'zweck': 'Grundgebühr'},
        {'betreff': 'Unvollständig', 'empfaenger': 'Firma A', 'zweck': ''},
    ]
    regeln = auswahl_regeln_aendern(buchungen, [], buchungen[:1], True)
    assert [ist_ausgeblendet(b, regeln) for b in buchungen] == [True, True, False, False, False]
    datei = ziel / 'paarregeln.csv'
    ausblendungen_speichern(datei, regeln)
    regeln = ausblendungen_laden(datei)
    spaeter = {'betreff': 'Neue spätere Anzeige', 'empfaenger': 'Firma A', 'zweck': 'Grundgebühr'}
    assert ist_ausgeblendet(spaeter, regeln)
    erweitert = regeln_ergaenzen(buchungen + [spaeter], regeln)
    aktiviert = auswahl_regeln_aendern(buchungen + [spaeter], erweitert, buchungen[1:2], False)
    assert not any(ist_ausgeblendet(b, aktiviert) for b in buchungen + [spaeter])
    # Änderung: Reaktivieren einer Gruppe darf einen unabhängigen anderen Zweck nicht freigeben.
    getrennt = auswahl_regeln_aendern(buchungen + [spaeter], erweitert, buchungen[2:3], True)
    aktiviert = auswahl_regeln_aendern(buchungen + [spaeter], getrennt, buchungen[1:2], False)
    assert ist_ausgeblendet(buchungen[2], aktiviert)
    assert not any(ist_ausgeblendet(b, aktiviert) for b in buchungen[:2] + [spaeter])
    gleicher_betreff = {'betreff': 'Erste Anzeige', 'empfaenger': 'Firma C', 'zweck': 'Anderes'}
    assert ist_ausgeblendet(gleicher_betreff, regeln)
    # Änderung: Alte Gegenpartei-Betreffe behalten ihre Wirkung und lassen sich gemeinsam aktivieren.
    alt = {'betreff': 'Firma A · Grundgebühr', 'betreff_alt': 'Firma A', 'empfaenger': 'Firma A', 'zweck': 'Grundgebühr'}
    migriert = regeln_ergaenzen([alt], ['firma a'])
    assert ist_ausgeblendet(alt, migriert)
    assert not auswahl_regeln_aendern([alt], migriert, [alt], False)


async def fortschrittsbereinigung_pruefen():
    # Änderung: Expliziter Client-Kontext macht den Test unabhängig von zuvor importierten UI-Modulen.
    from nicegui.client import Client
    with Client.auto_index_client:
        await _fortschrittsbereinigung_pruefen()


async def _fortschrittsbereinigung_pruefen():
    # Änderung: Echte UI-Elemente auch bei Erfolg und Worker-Fehler vollständig entfernen.
    from nicegui import ui
    from anwendung.buchungsmanagement_ui import BuchungsmanagementOberflaeche
    ansicht = BuchungsmanagementOberflaeche(SimpleNamespace())
    timer_liste = []
    dialog_liste = []
    timer_original, dialog_original = ui.timer, ui.dialog

    def timer_anlegen(*args, **kwargs):
        timer = timer_original(*args, **kwargs)
        timer_liste.append(timer)
        return timer

    def dialog_anlegen(*args, **kwargs):
        dialog = dialog_original(*args, **kwargs)
        dialog_liste.append(dialog)
        return dialog

    async def hintergrund(arbeit, melden):
        return await asyncio.to_thread(arbeit, melden)

    def arbeit(melden):
        melden(0, 1, 'Testphase')
        melden(1, 1, 'Testphase')
        return 'fertig'

    def fehler(melden):
        melden(0, 1, 'Testphase')
        raise ValueError('Testfehler')

    with patch('anwendung.buchungsmanagement_ui.ui.timer', side_effect=timer_anlegen), patch(
            'anwendung.buchungsmanagement_ui.ui.dialog', side_effect=dialog_anlegen), patch(
            'anwendung.buchungsmanagement_ui.run.io_bound', side_effect=hintergrund):
        assert await ansicht.mit_fortschritt(arbeit) == 'fertig'
        try:
            await ansicht.mit_fortschritt(fehler)
        except ValueError:
            pass
        else:
            raise AssertionError('Worker-Fehler fehlt.')
    assert len(timer_liste) == 2 and all(t._is_canceled for t in timer_liste)
    assert all(d.id not in d.client.elements for d in dialog_liste)


def bestand(ordner):
    # Änderung: Alle Originaldateien lokal per Hash auf unveränderten Inhalt prüfen.
    return {p: hashlib.sha256(p.read_bytes()).digest() for p in ordner.rglob('*') if p.is_file()}


def muss_scheitern(aktion):
    try:
        aktion()
    except ValueError:
        return
    raise AssertionError('Ungültiger Fall wurde akzeptiert.')


def pruefen():
    basis = Path(__file__).resolve().parents[1]
    vorlagen = basis.parent / '_Vorlagen'
    konto = vorlagen / 'Kontoauszüge Beispieldaten'
    rechnungen = vorlagen / 'Rechnungen Beispieldaten'
    vorher = {**bestand(konto), **bestand(rechnungen)}
    assert vorher and konto.is_dir() and rechnungen.is_dir()
    # Änderung: Dateizähler jeder Verarbeitungsphase gegen die lokalen Beispiele prüfen.
    meldungen = []
    melden = lambda *m: meldungen.append(m)
    buchungen = kontoauszuege_lesen(konto, melden)
    assert len(buchungen) == 62 and len({b['id'] for b in buchungen}) == 62
    assert all(b['empfaenger'] and b['zweck'] for b in buchungen)
    assert all(b['betreff_alt'] == b['empfaenger'] for b in buchungen)
    assert not any('IBAN:' in b['zweck'] or 'Übertrag' in b['zweck'] for b in buchungen)
    assert sum(b['betrag'].startswith('-') for b in buchungen) == 52
    probleme = rechnungen_pruefen(buchungen, rechnungen, set(), melden)
    assert {m[2] for m in meldungen} == {'Kontoauszüge lesen', 'Rechnungsdateien zuordnen', 'Buchungen und PDF-Beträge prüfen'}
    for phase in {m[2] for m in meldungen}:
        werte = [m for m in meldungen if m[2] == phase]
        assert werte[0][0] == 0 and werte[-1][0] == werte[-1][1]
        assert all(0 <= m[0] <= m[1] for m in werte)
        assert [m[0] for m in werte] == sorted(m[0] for m in werte)
    # Änderung: Erwartungszahlen an den aktuellen lokalen Rechnungsbestand anpassen;
    # Namens-/Zuordnungsfälle und Betragsfälle weiterhin getrennt prüfen.
    assert Counter(p['status'] for p in probleme if not p['status'].startswith('Betrag')) == {
        'Rechnung ohne Buchung': 1, 'Rechnung fehlt': 26}
    assert Counter(p['status'] for p in probleme if p['status'].startswith('Betrag')) == {
        'Betrag nicht prüfbar': 11, 'Betrag abweichend': 1}
    ausgeschlossen = {betreff_schluessel(b['betreff']) for b in buchungen}
    assert not any(p['status'] == 'Rechnung fehlt' for p in rechnungen_pruefen(buchungen, rechnungen, ausgeschlossen))
    assert {**bestand(konto), **bestand(rechnungen)} == vorher

    with tempfile.TemporaryDirectory(dir=basis / '.lokal') as ziel:
        ziel = Path(ziel)
        kontoziel = ziel / 'konto'
        kontoziel.mkdir()
        (kontoziel / 'auszug.pdf').write_bytes(b'Lokale Parser-Testdatei')
        # Änderung: Synthetischer PDF-Lesetext prüft unabhängig erwartete Fachwerte.
        text = ('Kontoauszug\n1/2026\nalter Kontostand vom 30.12.2025\nKopf\n100,00 H\n'
                '31.12. 31.12. Lastschrift PN:1 20,00 S\n Firma A\n'
                '02.01. 02.01. Gutschrift PN:2 50,00 H\n Firma B\n'
                '02.01. 02.01. Lastschrift PN:1 10,00 S\n Firma A\n'
                'neuer Kontostand vom 31.01.2026 120,00 H\n')

        def lesen(inhalt, fortschritt=None):
            reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: inhalt)])
            with patch('anwendung.buchungsmanagement.PdfReader', return_value=reader):
                return kontoauszuege_lesen(kontoziel, fortschritt)

        daten = lesen(text)
        assert [b['id'] for b in daten] == ['20251231', '20260102-1', '20260102-2']
        assert [b['betrag'] for b in daten] == ['-20.00', '50.00', '-10.00']
        # Änderung: Abweichende Wertstellung (auch außerhalb des Auszugszeitraums)
        # darf Buchungstag, Tagesnummer und spätere Rechnungszuordnung nicht ändern.
        anderer_wert = text.replace('31.12. 31.12.', '31.12. 01.01.').replace(
            '02.01. 02.01.', '02.01. 02.02.')
        assert lesen(anderer_wert) == daten
        # Änderung: Bytegleiche Auszugskopie importiert keine Buchung doppelt.
        (kontoziel / 'kopie.PDF').write_bytes((kontoziel / 'auszug.pdf').read_bytes())
        assert lesen(text) == daten
        muss_scheitern(lambda: lesen(text.replace('120,00 H', '121,00 H')))
        fehler_meldungen = []
        muss_scheitern(lambda: lesen(text.replace('120,00 H', '121,00 H'), lambda *m: fehler_meldungen.append(m)))
        assert fehler_meldungen and all(m[0] < m[1] for m in fehler_meldungen)
        muss_scheitern(lambda: lesen(text.replace('20,00 S', '20,00 X')))
        muss_scheitern(lambda: lesen(text.replace('31.12. 31.12.', '32.12. 31.12.')))
        muss_scheitern(lambda: lesen(''))
        (kontoziel / 'kopie.PDF').write_bytes(b'Anderer gleicher Auszug')
        muss_scheitern(lambda: lesen(text))

        rechnungsziel = ziel / 'rechnungen'
        rechnungsziel.mkdir()
        namen = ['20251231 Firma A R1 vom 30122025.pdf',
                 '20260102-1 Firma B R2 vom 01012026.PDF',
                 '20260102-1b Firma B R2 vom 01012026.xml']
        for name in namen:
            (rechnungsziel / name).touch()
        # Änderung: Synthetische Zuordnung isoliert vom echten PDF-Leser prüfen.
        def abgleichen(ausgeblendet=None, vollstaendig=False):
            def betrag(datei):
                return Decimal('50.00') if datei.name.startswith('20260102-1 ') else Decimal('20.00')
            with patch('anwendung.buchungsmanagement.rechnungsbetrag_lesen', side_effect=betrag):
                return rechnungen_pruefen(daten, rechnungsziel, ausgeblendet or set(), vollstaendig=vollstaendig)

        result = abgleichen()
        assert len(result) == 1 and result[0]['id'] == '20260102-2' and result[0]['status'] == 'Rechnung fehlt'
        # Änderung: Vollansicht enthält grüne Zuordnung und unabhängigen grünen Betragsstatus.
        komplett = abgleichen(vollstaendig=True)
        assert len(komplett) == 3
        assert sum(r['status'] == 'OK' and r['betrag_status'] == 'OK' for r in komplett) == 2
        ids = [b['id'] for b in daten]
        assert not abgleichen({'firma a'})
        assert [b['id'] for b in daten] == ids
        # Änderung: Eine übrig gebliebene Tagesbuchung benötigt keinen Nummernanhang mehr.
        neu = ziel / 'aktive-tagesbuchung'
        neu.mkdir()
        (neu / '20260102 Firma A.pdf').touch()
        with patch('anwendung.buchungsmanagement.rechnungsbetrag_lesen', return_value=Decimal('10.00')):
            ergebnis = rechnungen_pruefen(daten, neu, {'firma b'}, vollstaendig=True)
        tag = next(r for r in ergebnis if r.get('id') == '20260102-2')
        assert tag['pruef_id'] == '20260102' and tag['status'] == tag['betrag_status'] == 'OK'
        drei = daten + [{**daten[-1], 'id': '20260102-3', 'betreff': 'Firma C', 'betreff_alt': 'Firma C', 'empfaenger': 'Firma C'}]
        aktive_ids = buchungs_pruef_ids(drei, {'firma b'})
        assert aktive_ids['20260102-2'] == '20260102-1' and aktive_ids['20260102-3'] == '20260102-2'
        # Änderung: Doppelte Hauptrechnung, ungültige Daten und verwaiste Zusätze getrennt melden.
        for name in ['20251231 Andere R3 vom 30122025.pdf', '20260102-2 Firma A R4 vom 32012026.pdf',
                     '20260103 Firma C R5 vom 02012026.pdf', '20260104b Firma C R6 vom 02012026.xml', 'falsch.pdf']:
            (rechnungsziel / name).touch()
        status = Counter(p['status'] for p in abgleichen())
        assert status == {'Mehrere Rechnungen': 1, 'Datum ungültig': 1, 'Rechnung ohne Buchung': 1,
                          'Zusatz ohne Hauptrechnung': 1, 'Dateiname fehlerhaft': 1, 'Rechnung fehlt': 1}
        # Änderung: Fehlendes „vom“ ist jetzt gültig; XML ohne b bleibt fehlerhaft.
        (rechnungsziel / '20260105 Firma D R7 02012026.pdf').touch()
        (rechnungsziel / '20260106 Firma D R8 vom 02012026.xml').touch()
        status = Counter(p['status'] for p in abgleichen())
        assert status['Dateiname fehlerhaft'] == 2 and status['Rechnung ohne Buchung'] == 2
        # Änderung: Abweichung und unlesbares PDF als offene Fälle erhalten, nicht als Treffer.
        for datei_test in list(rechnungsziel.iterdir()):
            if datei_test.name not in namen:
                datei_test.unlink()
        with patch('anwendung.buchungsmanagement.rechnungsbetrag_lesen', return_value=Decimal('19.99')):
            ergebnis = rechnungen_pruefen(daten, rechnungsziel, set())
            assert sum(p['status'] == 'Betrag abweichend' for p in ergebnis) == 2
            assert all(p['rechnungsbetrag'] == '19.99' for p in ergebnis if p['status'] == 'Betrag abweichend')
            komplett = rechnungen_pruefen(daten, rechnungsziel, set(), vollstaendig=True)
            assert sum(r['status'] == 'OK' and r['betrag_status'] == 'Betrag abweichend' for r in komplett) == 2
        with patch('anwendung.buchungsmanagement.rechnungsbetrag_lesen', side_effect=ValueError('Nicht eindeutig')):
            assert sum(p['status'] == 'Betrag nicht prüfbar' for p in rechnungen_pruefen(daten, rechnungsziel, set())) == 2
        datei = ziel / 'buchungsmanagement.json'
        config = einstellungen_laden(datei)
        config['ausgeblendet'] = ['firma a']
        einstellungen_speichern(datei, config)
        pfade = {k: config[k] for k in ('kontoordner', 'rechnungsordner')}
        assert einstellungen_laden(datei) == pfade
        # Änderung: Schreibfehler müssen den bisherigen Stand erhalten.
        with patch.object(Path, 'replace', side_effect=OSError):
            try:
                einstellungen_speichern(datei, {**config, 'ausgeblendet': []})
            except OSError:
                pass
            else:
                raise AssertionError('Schreibfehler fehlt.')
        assert einstellungen_laden(datei) == pfade
        datei.write_text('{"ausgeblendet": "falsch"}', encoding='utf-8')
        muss_scheitern(lambda: einstellungen_laden(datei))
        assert betreff_schluessel('  FIRMA   A ') == 'firma a'
        csv_datenbank_pruefen(ziel, buchungen)
        # Änderung: OCR-Prozess darf Pfade nicht als Code ausführen und Text nur im RAM halten.
        ocrdatei = ziel / "rechnung ' $(test).pdf"
        ocrdatei.write_bytes(b'OCR-Test')
        antwort = SimpleNamespace(returncode=0, stdout=json.dumps(['Gesamtbetrag 42,50 EUR']).encode(), stderr=b'')
        with patch('anwendung.pdf_texterkennung.subprocess.run', return_value=antwort) as prozess:
            assert pdf_texterkennung.pdf_texte_lokal_erkennen(ocrdatei) == ['Gesamtbetrag 42,50 EUR']
            assert pdf_texterkennung.pdf_texte_lokal_erkennen(ocrdatei) == ['Gesamtbetrag 42,50 EUR']
            assert prozess.call_count == 1
            args, kwargs = prozess.call_args
            assert str(ocrdatei) not in ' '.join(args[0])
            assert kwargs['env']['ANA_RECHNUNG_PDF'] == str(ocrdatei.resolve())
            assert not kwargs.get('shell', False) and kwargs['capture_output'] and kwargs['timeout'] == 90
            ocrdatei.write_bytes(b'Geaenderter OCR-Test')
            pdf_texterkennung.pdf_texte_lokal_erkennen(ocrdatei)
            assert prozess.call_count == 2
        ocrdatei.write_bytes(b'Zeitlimit-Test')
        with patch('anwendung.pdf_texterkennung.subprocess.run', side_effect=subprocess.TimeoutExpired('powershell', 90)):
            muss_scheitern(lambda: pdf_texterkennung.pdf_texte_lokal_erkennen(ocrdatei))
        with patch('anwendung.pdf_texterkennung.subprocess.run', return_value=SimpleNamespace(returncode=1)):
            muss_scheitern(lambda: pdf_texterkennung.pdf_texte_lokal_erkennen(ocrdatei))
    # Änderung: Betragsleser mit unabhängigen erwarteten Endbeträgen und irreführenden Einzelpreisen prüfen.
    for text, erwartet in [
        ('Einzelpreis 9,99 EUR\nNetto 100,00 EUR\nMwSt 19,00 EUR\nGesamtbetrag 119,00 EUR', '119.00'),
        ('Rechnungsbetrag\nEUR 1.234,56', '1234.56'),
        ('Brutto-Rechnungsbetrag 119,00 EUR\nNetto-Rechnungsbetrag 100,00 EUR', '119.00'),
        ('Net. Gesamt 99,00 € 2,00 €\nGesamtpreis 101,00 €', '101.00'),
        ('Gesamt netto 100,00\nGesamt Mehrwertsteuer 19,00\nGesamt brutto 119,00', '119.00'),
        ('Zahlbetrag -19,90 EUR', '-19.90'),
        ('Summe 24,00 EUR', '24.00'),
        ('Rechnungsbetrag 24,00 EUR\nRechnungsbetrag 24,00 EUR', '24.00'),
    ]:
        assert endbetrag_aus_texten([text]) == Decimal(erwartet)
    for text in ['Einzelpreis 19,99 EUR', 'MwSt 3,19 EUR', 'Gesamtbetrag 20,00 und 30,00 EUR',
                 'Rechnungsbetrag 20,00 EUR\nZahlbetrag 19,00 EUR', '', 'Rechnungsbetrag 19,00 %']:
        muss_scheitern(lambda text=text: endbetrag_aus_texten([text]))
    # Änderung: Alle optionalen Rechnungsangaben und reine Zwecktexte zulassen.
    for name, erwartet in [
        ('20260102 Abbuchung Grundgebühr', None),
        ('20260102 Firma A', None),
        ('20260102 Firma A R1', None),
        ('20260102 Firma A 12345678', None),
        ('20260102 Firma A R1 01012026', '01012026'),
        ('20260102 Firma A vom 01012026', '01012026'),
        ('20260102 Firma A R1 vom 01012026', '01012026'),
        ('20260102-1b Abbuchung Grundgebühr', None),
        ('20260102 Rückzahlung vom Finanzamt', None),
    ]:
        tag, nr, zusatz, beschreibung, datum = rechnungsname_lesen(name)
        assert tag == '20260102' and beschreibung and datum == erwartet
    for name in ['20260102', '20260102-0 Zweck', '20260102 Zweck vom', '20260102 Zweck vom 01.01.2026',
                 '20260102 01012026']:
        muss_scheitern(lambda name=name: rechnungsname_lesen(name))
    # Änderung: Scanseiten müssen den lokalen OCR-Pfad nutzen; kein Buchungsbetrag als Suchhilfe.
    reader = SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda **kwargs: '')])
    with patch('anwendung.buchungsmanagement.PdfReader', return_value=reader), patch(
            'anwendung.buchungsmanagement.pdf_texte_lokal_erkennen', return_value=['Gesamtbetrag 42,50 EUR']) as ocr:
        assert rechnungsbetrag_lesen(Path('scan.pdf')) == Decimal('42.50')
        ocr.assert_called_once()
    asyncio.run(fortschrittsbereinigung_pruefen())
    print('Buchungsmanagement: lokale Beispiele, PDF-Endbeträge, OCR-Pfad, optionale Rechnungsangaben, Fortschrittszähler, Fehlerfälle und Persistenz bestanden; Originaldateien unverändert.')


if __name__ == '__main__':
    # Änderung: Fehlerdetails verbleiben im lokalen Prüfprotokoll des Freigabeskripts.
    pruefen()
