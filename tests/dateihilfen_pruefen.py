# Änderung für v2: In tests/ eingeordnet; Modul- und Dateipfade angepasst.
"""Änderung für v2: Ausgelagerte Dateihilfen lokal mit der Vorlage vergleichen.

Beispieldaten werden nur gelesen. Schreibprüfungen erfolgen in einem temporären
Ordner innerhalb von .lokal. Es werden ausschließlich feste Statusmeldungen ausgegeben.
"""

import ast
import configparser
import copy
import contextlib
import io
from pathlib import Path
import tempfile

from anwendung import datenhaltung
# Änderung für v2: Auch die ausgelagerte Pfadbildung gegen die Vorlage prüfen.
from anwendung.einstellungen import pfade_erstellen, ini_datei_lesen, ini_datei_schreiben


class IniZugriffeErweitern(ast.NodeTransformer):
    # Änderung für v2: Neue Hilfsaufrufe für den Strukturvergleich in Originalzugriffe zurückführen.
    def visit_Assign(self, knoten):
        if isinstance(knoten.value, ast.Call) and isinstance(knoten.value.func, ast.Name):
            if knoten.value.func.id == 'ini_datei_lesen':
                ziel = knoten.targets[0].id
                vorlage = ast.parse(
                    "with open(datei, 'r', encoding='utf-8') as f:\n"
                    f"    {ziel}.read_file(f)"
                ).body[0]
                vorlage.items[0].context_expr.args[0] = knoten.value.args[0]
                return vorlage
        return self.generic_visit(knoten)

    def visit_Expr(self, knoten):
        if isinstance(knoten.value, ast.Call) and isinstance(knoten.value.func, ast.Name):
            if knoten.value.func.id == 'ini_datei_schreiben':
                vorlage = ast.parse(
                    "with open(datei, 'w', encoding='utf-8') as configfile:\n"
                    "    config.write(configfile)"
                ).body[0]
                vorlage.items[0].context_expr.args[0] = knoten.value.args[0]
                vorlage.body[0].value.func.value = knoten.value.args[1]
                return vorlage
        return self.generic_visit(knoten)


class DokumentAufrufeErweitern(ast.NodeTransformer):
    # Änderung für v2: Ausgelagerte Dokumentabläufe zum Strukturvergleich wieder einsetzen.
    def __init__(self, funktionen):
        self.funktionen = funktionen

    def visit_Expr(self, knoten):
        aufruf = knoten.value
        if isinstance(aufruf, ast.Call) and isinstance(aufruf.func, ast.Name):
            if aufruf.func.id in self.funktionen:
                funktion = self.funktionen[aufruf.func.id]
                argumente = dict(zip((arg.arg for arg in funktion.args.args), aufruf.args))

                class ArgumenteEinsetzen(ast.NodeTransformer):
                    def visit_Name(self, name):
                        if isinstance(name.ctx, ast.Load) and name.id in argumente:
                            return copy.deepcopy(argumente[name.id])
                        return name

                return [ArgumenteEinsetzen().visit(copy.deepcopy(zeile))
                        for zeile in funktion.body]
        return self.generic_visit(knoten)


class BerechnungsAufrufErweitern(ast.NodeTransformer):
    # Änderung für v2: Rechenkern mit Original-Oberflächenwerten strukturell vergleichen.
    def __init__(self, funktion):
        self.funktion = funktion

    def visit_Assign(self, knoten):
        if not (isinstance(knoten.value, ast.Call) and isinstance(knoten.value.func, ast.Name)
                and knoten.value.func.id == 'abrechnung_berechnen'):
            return self.generic_visit(knoten)
        # Änderung für v2: Übergabe aller Daten und Oberflächenwerte explizit absichern.
        erwartet = ast.parse(
            'abrechnung = abrechnung_berechnen(\n'
            '    abnehmer_db, zaehler_db, abschlag_db, arbeitspreis, grundgebuehr,\n'
            '    jahre_dropdown.value, mwst_jahr.value, za_switch.value, za_datum.value,\n'
            '    za_mwst != [], za_mwst.value if za_mwst != [] else None)'
        ).body[0]
        assert ast.dump(knoten) == ast.dump(erwartet)
        argumente = dict(zip((arg.arg for arg in self.funktion.args.args), knoten.value.args))
        # Der Steuerwert wird im Original nur innerhalb der geprüften Zwischenablesung gelesen.
        argumente['zwischen_mwst'] = ast.parse('za_mwst.value', mode='eval').body

        class OriginalWerteEinsetzen(ast.NodeTransformer):
            def visit_Name(self, name):
                if isinstance(name.ctx, ast.Load) and name.id in argumente:
                    return copy.deepcopy(argumente[name.id])
                return name

            def visit_Call(self, aufruf):
                aufruf = self.generic_visit(aufruf)
                if isinstance(aufruf.func, ast.Name) and aufruf.func.id == 'letzte_mindestabnahme':
                    assert len(aufruf.args) == 2 and ast.dump(aufruf.args[1]) == ast.dump(ast.Name(id='abnehmer_db', ctx=ast.Load()))
                    aufruf.args = aufruf.args[:1]
                return aufruf

        assert isinstance(self.funktion.body[-1], ast.Return)
        assert ast.dump(self.funktion.body[-1].value) == ast.dump(ast.Name(id='abrechnung', ctx=ast.Load()))
        return [OriginalWerteEinsetzen().visit(copy.deepcopy(zeile))
                for zeile in self.funktion.body[:-1]]


class RueckverguetungsAufrufErweitern(ast.NodeTransformer):
    # Änderung für v2: Tabellenaufbau mit den bisherigen Oberflächenwerten vergleichen.
    def __init__(self, funktion):
        self.funktion = funktion

    def visit_Assign(self, knoten):
        if isinstance(knoten.value, ast.Call) and isinstance(knoten.value.func, ast.Name):
            if knoten.value.func.id == 'rueckverguetung_vorbereiten':
                erwartet = ast.parse('rueckv_tabelle = rueckverguetung_vorbereiten(abrechnung_datei, rueckv_jahre_dropdown.value)').body[0]
                assert ast.dump(knoten) == ast.dump(erwartet)
                class JahrEinsetzen(ast.NodeTransformer):
                    def visit_Name(self, name):
                        if name.id == 'jahr' and isinstance(name.ctx, ast.Load):
                            return ast.parse('rueckv_jahre_dropdown.value', mode='eval').body
                        return name
                assert ast.dump(self.funktion.body[0]) == ast.dump(ast.parse('rueckv_tabelle = []').body[0])
                assert ast.dump(self.funktion.body[-1]) == ast.dump(ast.parse('return rueckv_tabelle').body[0])
                return [JahrEinsetzen().visit(copy.deepcopy(zeile)) for zeile in self.funktion.body[1:-1]]
        return self.generic_visit(knoten)

    def visit_If(self, knoten):
        erwartet = ast.parse('if abrechnung_datei:\n'
                             '    rueckv_mwst = abrechnung_datei[-1]["MwSt-Satz"]\n'
                             '    if "Abrechnung ab ZA" in abrechnung_datei[0].keys():\n'
                             '        rueckv_mwst2 = abrechnung_datei[-1]["ZA MwSt"]').body[0]
        if ast.dump(knoten) == ast.dump(erwartet):
            # Die im Original in der Schleife gesetzten globalen Steuerwerte sind damit identisch.
            return []
        return self.generic_visit(knoten)


class BuchungsAufrufErweitern(ast.NodeTransformer):
    # Änderung für v2: Exportfunktionen mit ihren ursprünglichen Eingaben strukturell vergleichen.
    def __init__(self, funktionen):
        self.funktionen = funktionen

    def visit_Return(self, knoten):
        aufruf = knoten.value
        if isinstance(aufruf, ast.Call) and isinstance(aufruf.func, ast.Name):
            if aufruf.func.id in self.funktionen:
                funktion = self.funktionen[aufruf.func.id]
                assert not aufruf.keywords and len(aufruf.args) == len(funktion.args.args)
                argumente = dict(zip((arg.arg for arg in funktion.args.args), aufruf.args))
                class EingabenEinsetzen(ast.NodeTransformer):
                    def visit_Name(self, name):
                        if isinstance(name.ctx, ast.Load) and name.id in argumente:
                            return copy.deepcopy(argumente[name.id])
                        return name
                return [EingabenEinsetzen().visit(copy.deepcopy(zeile)) for zeile in funktion.body]
        return self.generic_visit(knoten)


class FreigegebeneBuchungskorrekturen(ast.NodeTransformer):
    # Änderung für v2: Im Vorlagenvergleich ausschließlich die zwei vom Benutzer
    # freigegebenen Fehlerkorrekturen zulassen; alle anderen Abläufe bleiben vergleichbar.
    def __init__(self):
        self.anzahl = 0

    def visit_Assign(self, knoten):
        alt_netto = ast.parse('csvzeile["Betrag"] = str(round_half_up(Decimal((rueckvrow["Rückvergütung Netto"]) * (1 + Decimal(rueckvrow["MwSt-Satz"]) / 100)),2)).replace(".",",")').body[0]
        alt_brutto = ast.parse('csvzeile["Betrag"] = str(rueckvrow["Rückvergütung"]).replace(".",",")').body[0]
        if ast.dump(knoten) == ast.dump(alt_netto):
            self.anzahl += 1
            return ast.parse('csvzeile["Betrag"] = str(round_half_up(Decimal(rueckvrow["Rückvergütung Netto"]) * (1 + Decimal(rueckvrow["MwSt-Satz"]) / 100),2)).replace(".",",")').body[0]
        if ast.dump(knoten) == ast.dump(alt_brutto):
            self.anzahl += 1
            return ast.parse('if "MwSt bis ZA" in rueckv[0].keys():\n'
                             '    csvzeile["Betrag"] = str(rueckvrow["Rückvergütung gesamt"]).replace(".",",")\n'
                             'else:\n'
                             '    csvzeile["Betrag"] = str(rueckvrow["Rückvergütung"]).replace(".",",")').body[0]
        return self.generic_visit(knoten)


def pruefen():
    # Änderung für v2: Struktur aller Originalfunktionen vergleichen, ohne ANA zu starten.
    basis = Path(__file__).resolve().parents[1]
    original = basis.parent / '_Vorlagen' / 'ana' / 'ana.py'
    alt = ast.parse(original.read_text(encoding='utf-8-sig'))
    neu = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8-sig'))
    modul = ast.parse((basis / 'anwendung' / 'datenhaltung.py').read_text(encoding='utf-8'))
    # Änderung für v2: Ausgelagerte Feldformatierung ebenfalls strukturell vergleichen.
    feldmodul = ast.parse((basis / 'anwendung' / 'dokumentfelder.py').read_text(encoding='utf-8'))
    # Änderung für v2: Dokumenthelfer als eingesetzte Originalabläufe vergleichen.
    dokumentmodul = ast.parse((basis / 'anwendung' / 'dokumente.py').read_text(encoding='utf-8'))
    dokumentfunktionen = {k.name: k for k in dokumentmodul.body if isinstance(k, ast.FunctionDef)}
    # Änderung für v2: Auch die ausgelagerten CSV-Vorlagen in die Strukturprüfung aufnehmen.
    buchungsmodul = ast.parse((basis / 'anwendung' / 'buchungsvorlagen.py').read_text(encoding='utf-8'))
    buchungsfunktionen = {k.name: k for k in buchungsmodul.body if isinstance(k, ast.FunctionDef)}
    alte_funktionen = {k.name: k for k in alt.body if isinstance(k, ast.FunctionDef)}
    # Änderung für v2: Nur die drei statischen Ressourcenpfade des Hauptfensters normalisieren.
    class RessourcenEinsetzen(ast.NodeTransformer):
        def visit_Constant(self, knoten):
            namen = {'./ANA Logo.png': 'ANA logo.png', 'Logo NWS.JPG': 'Logo NWS.JPG',
                     'ANA-favicon.ico': 'ANA-favicon.ico'}
            if isinstance(knoten.value, str) and knoten.value in namen:
                return ast.parse('str(RESSOURCEN / ' + repr(namen[knoten.value]) + ')', mode='eval').body
            return knoten
    alte_funktionen['main'] = RessourcenEinsetzen().visit(copy.deepcopy(alte_funktionen['main']))
    # Änderung für v2: Vorlage bleibt unverändert; erwartete Korrekturen nur im Prüfspeicher anwenden.
    korrekturen = FreigegebeneBuchungskorrekturen()
    alte_funktionen['csv_rueckv'] = korrekturen.visit(copy.deepcopy(alte_funktionen['csv_rueckv']))
    assert korrekturen.anzahl == 2
    neue_funktionen = {k.name: k for k in neu.body + modul.body + feldmodul.body if isinstance(k, ast.FunctionDef)}
    # Änderung 2.02: Auch die ausgelagerten Methoden weiterhin vollständig vergleichen.
    from tests.rueckv_struktur import methoden_als_funktionen
    neue_funktionen.update(methoden_als_funktionen(basis, alte_funktionen))
    # Änderung 2.03: Auch die Abrechnungsansicht samt verschachtelten Dialogen prüfen.
    from tests.abrechnung_struktur import methoden_als_funktionen as abrechnungsmethoden
    neue_funktionen.update(abrechnungsmethoden(basis, alte_funktionen))
    # Änderung 2.02: Anbindung der neuen Ansicht zusätzlich exakt absichern.
    adapter = {k.name: k for k in neu.body if isinstance(k, ast.FunctionDef)}
    # Änderung 2.03: Die zwei Einstiegspunkte der neuen Abrechnungsansicht absichern.
    erwartet = ast.parse('def jahre_abrechnung():\n'
                         '    abrechnung_ansicht.jahre_abrechnung()').body[0]
    assert ast.dump(adapter['jahre_abrechnung']) == ast.dump(erwartet)
    erwartet = ast.parse('def abrechnung_ui():\n'
        '    global abrechnung_ansicht\n'
        '    abrechnung_ansicht = AbrechnungOberflaeche(sys.modules[__name__])\n'
        '    abrechnung_ansicht.abrechnung_ui()').body[0]
    assert ast.dump(adapter['abrechnung_ui']) == ast.dump(erwartet)
    erwartet = ast.parse('def rueckv_jahre_einlesen():\n'
                         '    rueckverguetung_ansicht.rueckv_jahre_einlesen()').body[0]
    assert ast.dump(adapter['rueckv_jahre_einlesen']) == ast.dump(erwartet)
    erwartet = ast.parse('def rueckverguetung_ui():\n'
        '    global rueckverguetung_ansicht\n'
        '    rueckverguetung_ansicht = RueckverguetungOberflaeche(sys.modules[__name__])\n'
        '    rueckverguetung_ansicht.rueckverguetung_ui()').body[0]
    assert ast.dump(adapter['rueckverguetung_ui']) == ast.dump(erwartet)
    # Änderung für v2: Verschobene Rechenhilfen prüfen, den vorhandenen Adapter beibehalten.
    rechenmodul = ast.parse((basis / 'anwendung' / 'berechnungen.py').read_text(encoding='utf-8'))
    rechenfunktionen = {k.name: k for k in rechenmodul.body if isinstance(k, ast.FunctionDef)}
    for name, funktion in rechenfunktionen.items():
        if name in alte_funktionen and name != 'letzte_mindestabnahme':
            neue_funktionen[name] = funktion
    assert alte_funktionen.keys() == neue_funktionen.keys()
    for name in alte_funktionen:
        # Änderung: Die freigegebene Stapelkonvertierung hat einen neuen Ablauf.
        # Ihren unveränderten GUI-Adapter hier, COM-Verhalten in dokumente_pruefen prüfen.
        if name == 'rueckv_pdf_process':
            erwartet = ast.parse('def rueckv_pdf_process():\n'
                '    global ordner_rueckv_word\n'
                '    global ordner_rueckv_pdf\n'
                '    global pdfstop\n'
                '    rueckverguetung_pdf_konvertieren(ordner_rueckv_word, ordner_rueckv_pdf, rueckv_progress_pdf.set_value)').body[0]
            assert ast.dump(neue_funktionen[name]) == ast.dump(erwartet)
            continue
        # Änderung für v2: Den umgebauten Pfadadapter unten durch Ausführen vergleichen.
        if name == 'pfade_setzen':
            continue
        if name == 'letzte_mindestabnahme':
            # Änderung für v2: Nur explizite Datenübergabe ergänzen; Suchalgorithmus bleibt gleich.
            adapter = ast.parse('def letzte_mindestabnahme(Ident):\n'
                                '    return mindestabnahme_berechnen(Ident, abnehmer_db)').body[0]
            assert ast.dump(neue_funktionen[name]) == ast.dump(adapter)
            helper = copy.deepcopy(rechenfunktionen[name])
            assert [arg.arg for arg in helper.args.args] == ['Ident', 'abnehmer_db']
            helper.args.args = helper.args.args[:1]
            assert ast.dump(alte_funktionen[name]) == ast.dump(helper)
            continue
        if name == 'rueckv_tabelle_berechnen':
            # Änderung für v2: Adapter exakt prüfen und den ausgelagerten Rechenkörper zurückführen.
            erwartet = ast.parse('def rueckv_tabelle_berechnen(table):\n'
                '    if table == []:\n'
                '        return table\n'
                '    return rueckverguetung_berechnen(\n'
                '        table, rueckv_prozent.value, rueckv_datum_beschluss.value, rueckv_mwst,\n'
                '        rueckv_mwst2 if "MwSt bis ZA" in table[0].keys() else None)').body[0]
            assert ast.dump(neue_funktionen[name]) == ast.dump(erwartet)
            helper = copy.deepcopy(rechenfunktionen['rueckverguetung_berechnen'])
            assert [arg.arg for arg in helper.args.args] == ['table', 'prozent', 'beschlussdatum', 'rueckv_mwst', 'rueckv_mwst2']
            helper.name = name
            helper.args = copy.deepcopy(alte_funktionen[name].args)
            class EingabenEinsetzen(ast.NodeTransformer):
                def visit_Name(self, knoten):
                    namen = {'prozent': 'rueckv_prozent.value', 'beschlussdatum': 'rueckv_datum_beschluss.value'}
                    if knoten.id in namen and isinstance(knoten.ctx, ast.Load):
                        return ast.parse(namen[knoten.id], mode='eval').body
                    return knoten
            helper = EingabenEinsetzen().visit(helper)
            assert ast.dump(alte_funktionen[name]) == ast.dump(helper)
            continue
        # Änderung für v2: Bei INI-Funktionen nur die dokumentierten Dateizugriffe erlauben.
        vergleich = neue_funktionen[name]
        if name in ('ini_einlesen', 'ini_speichern'):
            vergleich = IniZugriffeErweitern().visit(copy.deepcopy(vergleich))
        if name == 'abrechnung_erstellen_gui':
            vergleich = BerechnungsAufrufErweitern(rechenfunktionen['abrechnung_berechnen']).visit(copy.deepcopy(vergleich))
        if name == 'rueckv_tabelle_erstellen':
            vergleich = RueckverguetungsAufrufErweitern(rechenfunktionen['rueckverguetung_vorbereiten']).visit(copy.deepcopy(vergleich))
        if name in ('csv_grundgebuehr', 'csv_abschlag', 'csv_abrechnung_lastschrift',
                    'csv_abrechnung_ueberweisung', 'csv_rueckv'):
            vergleich = BuchungsAufrufErweitern(buchungsfunktionen).visit(copy.deepcopy(vergleich))
        if name in ('abrechnungen_word_erstellen', 'abr_pdf_process',
                    'rueckv_word_erstellen', 'rueckv_pdf_process'):
            vergleich = DokumentAufrufeErweitern(dokumentfunktionen).visit(copy.deepcopy(vergleich))
        assert ast.dump(alte_funktionen[name]) == ast.dump(vergleich)

    # Änderung für v2: Den Import der ausgelagerten Funktionen zusätzlich kontrollieren.
    namen = {k.name for k in modul.body if isinstance(k, ast.FunctionDef)}
    importe = [k for k in neu.body if isinstance(k, ast.ImportFrom) and k.module == 'anwendung.datenhaltung']
    assert len(importe) == 1 and {k.name for k in importe[0].names} == namen
    # Änderung für v2: Alle fünf Vorlagen müssen über den tatsächlichen Modulimport verfügbar sein.
    buchungsimporte = [k for k in neu.body if isinstance(k, ast.ImportFrom) and k.module == 'anwendung.buchungsvorlagen']
    assert len(buchungsimporte) == 1
    assert {k.name for k in buchungsimporte[0].names} == set(buchungsfunktionen)
    # Änderung für v2: Alle ausgelagerten Formatierungsfunktionen müssen in ANA verfügbar bleiben.
    feldnamen = {k.name for k in feldmodul.body if isinstance(k, ast.FunctionDef)}
    feldimporte = [k for k in neu.body if isinstance(k, ast.ImportFrom) and k.module == 'anwendung.dokumentfelder']
    assert len(feldimporte) == 1 and {k.name for k in feldimporte[0].names} == feldnamen

    alte_hilfen = ast.Module(body=[alte_funktionen[name] for name in namen], type_ignores=[])
    umgebung = {'Path': Path, 'csv': __import__('csv')}
    exec(compile(alte_hilfen, 'original_dateihilfen', 'exec'), umgebung)

    # Änderung für v2: Ausschließlich den festgelegten Beispielordner zulassen.
    config = configparser.ConfigParser()
    config.read(basis / 'ana.ini', encoding='utf-8')
    daten = Path(config['Anwendung']['arbeitsordner']).resolve()
    assert daten == (basis.parent / '_Vorlagen' / 'ana Beispieldaten').resolve()
    # Änderung für v2: Alle bisherigen globalen Pfadwerte inklusive Standardfall prüfen.
    pfadnamen = ('arbeitsordner', 'ordner_abrechnungen', 'ordner_rueckv', 'ordner_logs',
                 'ordner_datenbank', 'ordner_sicherungen', 'ordner_downloads', 'ordner_vorlagen')
    for arbeitsordner in ('', '.', 'relativer Ordner', 'C:\\Test\\', str(daten)):
        alt_pfade = {'arbeitsordner': arbeitsordner}
        neu_pfade = {'arbeitsordner': arbeitsordner, 'pfade_erstellen': pfade_erstellen}
        for funktion, umgebung_pfade in ((alte_funktionen['pfade_setzen'], alt_pfade),
                                         (neue_funktionen['pfade_setzen'], neu_pfade)):
            exec(compile(ast.Module(body=[funktion], type_ignores=[]), 'pfadpruefung', 'exec'),
                 umgebung_pfade)
            umgebung_pfade['pfade_setzen']()
        assert {name: alt_pfade[name] for name in pfadnamen} == {
            name: neu_pfade[name] for name in pfadnamen}
    lokal = basis / '.lokal'
    lokal.mkdir(exist_ok=True)
    anzahl = 0
    with tempfile.TemporaryDirectory(dir=lokal) as ordner:
        temp = Path(ordner)
        # Änderung für v2: INI-Lesen und -Schreiben mit lokalen Kopien vergleichen.
        for datei in (basis / 'ana.ini', daten / 'ana-betreiber.ini'):
            vorher_config = configparser.ConfigParser()
            with datei.open('r', encoding='utf-8') as f:
                vorher_config.read_file(f)
            nachher_config = ini_datei_lesen(datei)
            assert vorher_config == nachher_config
            with (temp / 'alt.ini').open('w', encoding='utf-8') as f:
                vorher_config.write(f)
            ini_datei_schreiben(temp / 'neu.ini', nachher_config)
            assert (temp / 'alt.ini').read_bytes() == (temp / 'neu.ini').read_bytes()
            assert ini_datei_lesen(temp / 'neu.ini') == vorher_config
        for datei in daten.rglob('*.csv'):
            # Änderung für v2: Leseergebnisse, Serialisierung und Seiteneffekte vergleichen.
            vorher = umgebung['datei_oeffnen'](datei)
            nachher = datenhaltung.datei_oeffnen(datei)
            assert vorher == nachher
            assert umgebung['import_file'](datei) == datenhaltung.import_file(datei)
            assert umgebung['import_csv_inhalt'](iter(datei.read_text().splitlines())) == (
                datenhaltung.import_csv_inhalt(iter(datei.read_text().splitlines())))
            if vorher:
                links, rechts = copy.deepcopy(vorher), copy.deepcopy(nachher)
                assert umgebung['dictlist_to_csv'](links) == datenhaltung.dictlist_to_csv(rechts)
                assert links == rechts
                umgebung['datei_speichern'](temp / 'alt.csv', copy.deepcopy(vorher))
                datenhaltung.datei_speichern(temp / 'neu.csv', copy.deepcopy(nachher))
                assert (temp / 'alt.csv').read_bytes() == (temp / 'neu.csv').read_bytes()
            anzahl += 1
        assert anzahl > 0
        # Änderung für v2: Bestehendes Verhalten bei fehlenden Dateien/Ordnern erhalten.
        assert umgebung['datei_oeffnen'](temp / 'fehlt.csv') == datenhaltung.datei_oeffnen(temp / 'fehlt.csv')
        datenhaltung.check_ordner_exists(temp / 'neu')
        datenhaltung.check_ordner_exists(temp / 'neu')
        assert (temp / 'neu').is_dir()


if __name__ == '__main__':
    try:
        # Änderung für v2: Keine datenhaltigen Ausgaben oder Tracebacks weitergeben.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pruefen()
        print('Datei-, INI- und Pfadprüfung bestanden; Abläufe einschließlich freigegebener Korrekturen bestätigt.')
    except Exception as fehler:
        print('Dateihilfenprüfung: nicht abgeschlossen. Fehlertyp: ' + type(fehler).__name__)
        raise SystemExit(1)
