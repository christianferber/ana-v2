"""Änderung 2.02: Ausgelagerte Methoden für den bisherigen Strukturvergleich lesen."""
import ast
import copy


def methoden_als_funktionen(basis, originalfunktionen):
    # Änderung: Nur den expliziten Wechsel von globalen Namen auf self und
    # self.anwendung zurückführen; alle fachlichen Anweisungen weiter vergleichen.
    baum = ast.parse((basis / 'anwendung' / 'rueckverguetung_ui.py').read_text(encoding='utf-8'))
    # Änderung: Exakte Protokollrahmen prüfen; ursprüngliche Fachkörper zurückführen.
    from tests.protokoll_struktur import protokoll_rahmen_pruefen
    protokoll_rahmen_pruefen(baum, 'rueckverguetung_ui')
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
        # Änderung nach 2.049: Ausschließlich die neue Standardfarbe des PDF-Knopfs zurückführen.
        if methode.name == 'rueckverguetung_ui':
            # Änderung nach 2.049: Layout und Beschriftung begrenzen; ursprünglichen Fachkörper vergleichen.
            layout, verschieben, beschriften = funktion.body[-4:-1]
            assert isinstance(layout, ast.With) and isinstance(beschriften, ast.For)
            assert ast.unparse(verschieben) == 'aktionsleiste.move(target_index=2)'
            assert [ast.unparse(e.elts[0]) for e in beschriften.iter.elts] == [
                'rueckv_button_erstellen', 'rueckv_button_einlesen', 'rueckv_button_speichern',
                'rueckv_button_download', 'rueckv_button_pdf']
            for teil in (layout, beschriften):
                for k in ast.walk(teil):
                    if isinstance(k, ast.Call):
                        assert isinstance(k.func, ast.Attribute) and k.func.attr in {'row', 'column', 'classes', 'label', 'move', 'set_text'}
            del funktion.body[-4:-1]
            from tests.buttondarstellung_struktur import pdf_anzeige_zurueckfuehren
            pdf_anzeige_zurueckfuehren(funktion, 'rueckv_button_pdf')
            farben = [k for k in ast.walk(funktion) if isinstance(k, ast.Call)
                      and isinstance(k.func, ast.Attribute) and k.func.attr == 'props'
                      and len(k.args) == 1 and isinstance(k.args[0], ast.Constant)
                      and k.args[0].value == 'color=primary']
            assert len(farben) == 1
            farben[0].args[0].value = 'color=red-5'
        # Änderung: Autorisierte Exportabsicherung prüfen; Fachkörper weiter vergleichen.
        from tests.export_struktur import export_dekoratoren_pruefen
        export_dekoratoren_pruefen(funktion)
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
