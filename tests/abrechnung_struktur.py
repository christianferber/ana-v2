"""Änderung 2.03: Ausgelagerte Abrechnungsabläufe strukturell vergleichen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Nur Zugriffe über self und self.anwendung zurückführen.
    baum = ast.parse((basis / 'anwendung' / 'abrechnung_ui.py').read_text(encoding='utf-8'))
    # Änderung: Exakte Protokollrahmen prüfen; ursprüngliche Fachkörper zurückführen.
    from tests.protokoll_struktur import protokoll_rahmen_pruefen
    protokoll_rahmen_pruefen(baum, 'abrechnung_ui')
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
        # Änderung 2.049: Ausschließlich die vier bekannten Pilot-Stiländerungen zurückführen.
        if methode.name == 'abrechnung_ui':
            # Änderung nach 2.049: Nur Umsatzdarstellung verschieben, Datenbindung erhalten.
            assert ast.unparse(funktion.body[-4]) == 'umsatz_titel.move(umsatz)'
            assert ast.unparse(funktion.body[-3]) == 'label_umsatz.move(umsatz)'
            assert ast.unparse(funktion.body[-2]) == "ergebniszeile.classes('hidden')"
            assert isinstance(funktion.body[-5], ast.With)
            del funktion.body[-5:-1]
            for knoten in ast.walk(funktion):
                if isinstance(knoten, ast.With):
                    for item in knoten.items:
                        if isinstance(item.optional_vars, ast.Name) and item.optional_vars.id in ('eingaben', 'ergebniszeile'):
                            item.optional_vars = None
            for zeile in funktion.body:
                if isinstance(zeile, ast.With):
                    zeile.body = [ast.Expr(value=k.value) if isinstance(k, ast.Assign)
                                  and isinstance(k.targets[0], ast.Name) and k.targets[0].id == 'umsatz_titel'
                                  else k for k in zeile.body]
            from tests.buttondarstellung_struktur import pdf_anzeige_zurueckfuehren
            pdf_anzeige_zurueckfuehren(funktion, 'abr_button_pdf')
            # Änderung nach 2.049: Kompakte Darstellung separat begrenzen;
            # anschließend sämtliche bisherigen Anweisungen unverändert vergleichen.
            layout, verschieben, beschriften = funktion.body[-4:-1]
            assert isinstance(layout, ast.With) and isinstance(beschriften, ast.For)
            assert ast.unparse(verschieben) == 'aktionsleiste.move(target_index=2)'
            erlaubt = {'row', 'column', 'classes', 'label', 'move', 'set_text'}
            for teil in (layout, beschriften):
                for aufruf in (k for k in ast.walk(teil) if isinstance(k, ast.Call)):
                    assert isinstance(aufruf.func, ast.Attribute) and aufruf.func.attr in erlaubt
            assert [(ast.unparse(e.elts[0]), e.elts[1].value, e.elts[2].id)
                    for e in beschriften.iter.elts] == [
                ('abr_button_erstellen', 'Berechnen', 'bearbeiten'),
                ('abr_button_einlesen', 'Laden', 'bearbeiten'),
                ('abr_button_speichern', 'Speichern', 'bearbeiten'),
                ('abr_button_plausibel', 'Prüfen', 'ausgeben'),
                ('abr_button_download', 'CSV', 'ausgeben'),
                ('abr_button_pdf', 'Word/PDF erstellen', 'ausgeben')]
            del funktion.body[-4:-1]
            class PilotStileZurueckfuehren(ast.NodeTransformer):
                anzahl = 0

                def visit_Call(self, knoten):
                    knoten = self.generic_visit(knoten)
                    if isinstance(knoten.func, ast.Attribute) and len(knoten.args) == 1:
                        wert = knoten.args[0]
                        if isinstance(wert, ast.Constant):
                            if knoten.func.attr == 'classes' and wert.value in ('ana-input-row', 'ana-action-row'):
                                self.anzahl += 1
                                return knoten.func.value
                            if knoten.func.attr == 'classes' and wert.value == 'text-2xl font-bold ana-page-title':
                                self.anzahl += 1
                                wert.value = 'text-2xl font-bold'
                            # Änderung nach 2.049: Gefüllte Standardfarbe gezielt zurückführen.
                            if knoten.func.attr == 'props' and wert.value == 'color=primary':
                                self.anzahl += 1
                                wert.value = 'color=red-5'
                    return knoten

            stile = PilotStileZurueckfuehren()
            funktion = stile.visit(funktion)
            assert stile.anzahl == 4
        # Änderung: Autorisierte Exportabsicherung prüfen; Fachkörper weiter vergleichen.
        from tests.export_struktur import export_dekoratoren_pruefen
        export_dekoratoren_pruefen(funktion)
        funktion.args.args = funktion.args.args[1:]
        globale_ergaenzen(vorlagen[methode.name], funktion)
        if isinstance(funktion, ast.AsyncFunctionDef):
            # Änderung: Speicherablauf und CSV-Download vollständig vergleichen.
            assert ast.dump(funktion) == ast.dump(vorlagen[methode.name])
        else:
            funktionen[funktion.name] = funktion
    return funktionen
