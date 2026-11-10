"""Änderung 2.034: Ausgelagerte Abnehmerabläufe strukturell vergleichen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Nur Zugriffe über self und self.anwendung zurückführen.
    baum = ast.parse((basis / 'anwendung' / 'abnehmer_ui.py').read_text(encoding='utf-8'))
    # Änderung: Exakte Protokollrahmen prüfen; ursprüngliche Fachkörper zurückführen.
    from tests.protokoll_struktur import protokoll_rahmen_pruefen
    protokoll_rahmen_pruefen(baum, 'abnehmer_ui')
    original = ast.parse((basis.parent / '_Vorlagen' / 'ana' / 'ana.py').read_text(encoding='utf-8-sig'))
    vorlagen = {k.name: k for k in original.body if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))}
    klasse = next(k for k in baum.body if isinstance(k, ast.ClassDef))

    class NamenZurueckfuehren(ast.NodeTransformer):
        def visit_Attribute(self, knoten):
            if isinstance(knoten.value, ast.Name) and knoten.value.id == 'self':
                return ast.copy_location(ast.Name(id=knoten.attr, ctx=knoten.ctx), knoten)
            if (isinstance(knoten.value, ast.Attribute) and knoten.value.attr == 'anwendung'
                    and isinstance(knoten.value.value, ast.Name) and knoten.value.value.id == 'self'):
                return ast.copy_location(ast.Name(id=knoten.attr, ctx=knoten.ctx), knoten)
            return self.generic_visit(knoten)

    def globale_ergaenzen(vorlage, neu):
        # Änderung: Auch Deklarationen in verschachtelten Dialogfunktionen und
        # with-Blöcken nur im Prüfspeicher wieder an ihre bisherige Stelle setzen.
        for feld, wert in ast.iter_fields(vorlage):
            if isinstance(wert, list):
                ziel = getattr(neu, feld, [])
                for index, element in enumerate(wert):
                    if isinstance(element, ast.Global):
                        ziel.insert(index, copy.deepcopy(element))
                    elif isinstance(element, ast.AST) and any(isinstance(k, ast.Global) for k in ast.walk(element)):
                        assert index < len(ziel) and type(ziel[index]) is type(element)
                        globale_ergaenzen(element, ziel[index])
            elif isinstance(wert, ast.AST) and any(isinstance(k, ast.Global) for k in ast.walk(wert)):
                globale_ergaenzen(wert, getattr(neu, feld))

    funktionen = {}
    for methode in klasse.body:
        if not isinstance(methode, (ast.FunctionDef, ast.AsyncFunctionDef)) or methode.name == '__init__':
            continue
        assert methode.args.args[0].arg == 'self'
        funktion = NamenZurueckfuehren().visit(copy.deepcopy(methode))
        funktion.args.args = funktion.args.args[1:]
        funktion.decorator_list = copy.deepcopy(vorlagen[methode.name].decorator_list)
        globale_ergaenzen(vorlagen[methode.name], funktion)
        if isinstance(funktion, ast.AsyncFunctionDef):
            # Änderung: Speicherablauf und CSV-Download vollständig vergleichen.
            assert ast.dump(funktion) == ast.dump(vorlagen[methode.name])
        else:
            funktionen[funktion.name] = funktion
    return funktionen
