"""Änderung 2.038: Ausgelagerte Einstellungenabläufe strukturell vergleichen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Nur Zugriffe über self und self.anwendung zurückführen.
    baum = ast.parse((basis / 'anwendung' / 'einstellungen_ui.py').read_text(encoding='utf-8'))
    # Änderung: Exakte Protokollrahmen prüfen; ursprüngliche Fachkörper zurückführen.
    from tests.protokoll_struktur import protokoll_rahmen_pruefen
    protokoll_rahmen_pruefen(baum, 'einstellungen_ui')
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

    # Änderung 2.038: Auch asynchrone Adapter vollständig gegen das Original prüfen.
    haupt = ast.parse((basis / 'anwendung' / 'oberflaeche.py').read_text(encoding='utf-8'))
    adapter = {k.name: k for k in haupt.body if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))}
    funktionen = {}
    for methode in klasse.body:
        if not isinstance(methode, (ast.FunctionDef, ast.AsyncFunctionDef)) or methode.name == '__init__':
            continue
        assert methode.args.args[0].arg == 'self'
        funktion = NamenZurueckfuehren().visit(copy.deepcopy(methode))
        if methode.name == 'ini_speichern':
            # Änderung nach 2.05.00: Nur die zwei expliziten Backup-Ergänzungen ausnehmen;
            # alle bisherigen Speicherabläufe weiterhin exakt gegen Original prüfen.
            assert ast.unparse(funktion.body[0]) == 'if not sicherungskonfiguration_pruefen(self):\n    return'
            del funktion.body[0]
            assert ast.unparse(funktion.body[2]) == 'sicherungskonfiguration_ergaenzen(self, config)'
            del funktion.body[2]
        # Änderung nach 2.049: Nur zusätzliche Darstellung und lokale Buttonreferenzen ausnehmen.
        if methode.name == 'einstellungen_ui':
            assert ast.unparse(funktion.body[-2]) == 'einstellungen_gestalten(self, karte, auswahl, standard, speichern, abbrechen)'
            del funktion.body[-2]
            assert funktion.body[1].items[1].optional_vars.id == 'karte'
            funktion.body[1].items[1].optional_vars = None
            class ButtonreferenzenEntfernen(ast.NodeTransformer):
                def visit_Assign(self, knoten):
                    if len(knoten.targets) == 1 and isinstance(knoten.targets[0], ast.Name) and knoten.targets[0].id in {'auswahl', 'standard', 'speichern', 'abbrechen'}:
                        return ast.Expr(value=knoten.value)
                    return self.generic_visit(knoten)
            funktion = ButtonreferenzenEntfernen().visit(funktion)
        funktion.args.args = funktion.args.args[1:]
        funktion.decorator_list = copy.deepcopy(vorlagen[methode.name].decorator_list)
        globale_ergaenzen(vorlagen[methode.name], funktion)
        # Änderung 2.038: Bereits freigegebene INI-Dateihilfen nur im Prüfvergleich zurückführen.
        vergleich = copy.deepcopy(funktion)
        if methode.name == 'ini_speichern':
            from tests.dateihilfen_pruefen import IniZugriffeErweitern
            vergleich = IniZugriffeErweitern().visit(vergleich)
        assert ast.dump(vergleich) == ast.dump(vorlagen[methode.name])
        erwartet = copy.deepcopy(vorlagen[methode.name])
        aufruf = 'return ' + ('await ' if isinstance(funktion, ast.AsyncFunctionDef) else '')
        aufruf += 'einstellungen_ansicht.' + methode.name + '(' + ', '.join(a.arg for a in erwartet.args.args) + ')'
        quelle = ('async ' if isinstance(funktion, ast.AsyncFunctionDef) else '') + 'def adapter():\n    ' + aufruf
        erwartet.body = ast.parse(quelle).body[0].body
        if methode.name == 'einstellungen_ui':
            erwartet.body = ast.parse('global einstellungen_ansicht\neinstellungen_ansicht = EinstellungenOberflaeche(sys.modules[__name__])\n' + aufruf).body
        assert ast.dump(adapter[methode.name]) == ast.dump(erwartet)
        if isinstance(funktion, ast.FunctionDef):
            funktionen[funktion.name] = funktion
    return funktionen
