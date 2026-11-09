"""Änderung 2.043: Verschobene Hilfen und alle Adapter vollständig vergleichen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Ausschließlich qualifizierte Anwendungszugriffe zurückführen.
    class Anwendungszugriffe(ast.NodeTransformer):
        def visit_Attribute(self, knoten):
            if (isinstance(knoten.value, ast.Attribute) and knoten.value.attr == 'anwendung'
                    and isinstance(knoten.value.value, ast.Name) and knoten.value.value.id == 'self'):
                return ast.copy_location(ast.Name(id=knoten.attr, ctx=knoten.ctx), knoten)
            return self.generic_visit(knoten)

    haupt = ast.parse((basis / 'anwendung/oberflaeche.py').read_text(encoding='utf-8'))
    adapter = {k.name: k for k in haupt.body if isinstance(k, ast.FunctionDef)}
    ergebnis = {}
    for modul, klasse, namen in (
            # Änderung 2.045: Datenbankzugriffe samt Adaptern und Initialisierung prüfen.
            # Änderung 2.047: Auch die gemeinsame Mitgliederaktualisierung vollständig prüfen.
            ('datenhaltung', 'DatenbankZugriff', {'db_datei_oeffnen', 'db_datei_speichern', 'dbs_mitglieder_aktualisieren'}),
            ('sicherung', 'Sicherung', {'db_sichern', 'max_anzahl_ordner'}),
            ('protokollierung', 'Protokollierung', {'change_log', 'change_log_info'})):
        baum = ast.parse((basis / ('anwendung/' + modul + '.py')).read_text(encoding='utf-8'))
        typ = next(k for k in baum.body if isinstance(k, ast.ClassDef) and k.name == klasse)
        methoden = [k for k in typ.body if isinstance(k, ast.FunctionDef) and k.name != '__init__']
        assert {k.name for k in methoden} == namen
        for methode in methoden:
            funktion = Anwendungszugriffe().visit(copy.deepcopy(methode))
            assert funktion.args.args.pop(0).arg == 'self'
            original = copy.deepcopy(originalfunktionen[funktion.name])
            if funktion.name == 'dbs_mitglieder_aktualisieren':
                # Änderung 2.047: Nur die durch Instanzzugriffe ersetzten global-Deklarationen ausnehmen.
                globale = [k for k in original.body if isinstance(k, ast.Global)]
                assert [k.names for k in globale] == [[n] for n in (
                    'abnehmer_db', 'zaehler_db', 'abschlag_db', 'konto_db',
                    'db_abnehmer', 'db_zaehler', 'db_abschlag', 'db_konto')]
                original.body = [k for k in original.body if not isinstance(k, ast.Global)]
                assert ast.dump(funktion) == ast.dump(original)
                # Änderung: Für den anschließenden Gesamtvergleich die geprüften Deklarationen ergänzen.
                funktion.body = globale + funktion.body
            elif funktion.name == 'db_datei_speichern':
                # Änderung: Nur die letzten drei direkten Schreibanweisungen durch die sichere Hilfe ersetzen.
                erwartet = copy.deepcopy(original)
                erwartet.body[-3:] = ast.parse('text_sicher_speichern(dbfile, csvstring)').body
                assert ast.dump(funktion) == ast.dump(erwartet)
                funktion = original
            elif funktion.name == 'db_sichern':
                # Änderung: Bewusst abgesicherte Dateizugriffe durch Inhalts- und Fehlertests prüfen.
                assert ast.dump(funktion.args) == ast.dump(original.args)
                funktion = original
            else:
                assert ast.dump(funktion) == ast.dump(original)
            erwartet = copy.deepcopy(originalfunktionen[funktion.name])
            args = ', '.join(a.arg for a in erwartet.args.args)
            erwartet.body = ast.parse('return ' + modul + '_hilfe.' + funktion.name + '(' + args + ')').body
            assert ast.dump(adapter[funktion.name]) == ast.dump(erwartet)
            ergebnis[funktion.name] = funktion
        # Änderung: Frühe Initialisierung und richtiger Modulimport müssen erhalten bleiben.
        assert any(isinstance(k, ast.ImportFrom) and k.module == 'anwendung.' + modul
                   and any(n.name == klasse for n in k.names) for k in haupt.body)
        erwartet = ast.parse(modul + '_hilfe = ' + klasse + '(sys.modules[__name__])').body[0]
        assert any(ast.dump(k) == ast.dump(erwartet) for k in haupt.body)
    return ergebnis
