"""Änderung 2.02: Ausgelagerte Methoden für den bisherigen Strukturvergleich lesen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Nur den expliziten Wechsel von globalen Namen auf self und
    # self.anwendung zurückführen; alle fachlichen Anweisungen weiter vergleichen.
    baum = ast.parse((basis / 'anwendung' / 'rueckverguetung_ui.py').read_text(encoding='utf-8'))
    klasse = next(k for k in baum.body if isinstance(k, ast.ClassDef))

    class NamenZurueckfuehren(ast.NodeTransformer):
        def visit_Attribute(self, knoten):
            if isinstance(knoten.value, ast.Name) and knoten.value.id == 'self':
                return ast.copy_location(ast.Name(id=knoten.attr, ctx=knoten.ctx), knoten)
            if (isinstance(knoten.value, ast.Attribute) and knoten.value.attr == 'anwendung'
                    and isinstance(knoten.value.value, ast.Name) and knoten.value.value.id == 'self'):
                return ast.copy_location(ast.Name(id=knoten.attr, ctx=knoten.ctx), knoten)
            return self.generic_visit(knoten)

    funktionen = {}
    for methode in klasse.body:
        if not isinstance(methode, (ast.FunctionDef, ast.AsyncFunctionDef)) or methode.name == '__init__':
            continue
        assert methode.args.args[0].arg == 'self'
        funktion = NamenZurueckfuehren().visit(copy.deepcopy(methode))
        funktion.args.args = funktion.args.args[1:]
        # Änderung: Der bestehende Vergleich erfasst synchrone Funktionen.
        # Den asynchronen CSV-Einstieg daher zusätzlich explizit prüfen.
        if isinstance(funktion, ast.AsyncFunctionDef):
            erwartet = ast.parse('async def csv_komma_rueckv_download():\n'
                '    filename = "Rückvergütung " + rueckv_jahre_dropdown.value + ".csv"\n'
                '    await komma_datei_speichern(rueckv_table, filename)').body[0]
            assert ast.dump(funktion) == ast.dump(erwartet)
            continue
        # Änderung: Früher nötige global-Deklarationen ausschließlich im
        # Prüfspeicher ergänzen. In der Klasse ersetzen Attribute diese Deklarationen.
        globale = [copy.deepcopy(k) for k in originalfunktionen[methode.name].body if isinstance(k, ast.Global)]
        funktion.body = globale + funktion.body
        funktionen[funktion.name] = funktion
    return funktionen
