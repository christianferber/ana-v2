"""Änderung nach 2.049: Nur bekannte PDF-Anzeigen auf die Referenzdarstellung zurückführen."""
import ast


def pdf_anzeige_zurueckfuehren(funktion, button, mit_wert=False):
    # Änderung: Nur genau den vereinbarten Buttonadapter akzeptieren, Fachaufrufe erhalten.
    treffer = [k for k in ast.walk(funktion) if isinstance(k, ast.Assign)
               and isinstance(k.value, ast.Call) and isinstance(k.value.func, ast.Name)
               and k.value.func.id == 'ButtonFortschritt']
    assert len(treffer) == 1
    assert len(treffer[0].value.args) == 1 and not treffer[0].value.keywords
    assert ast.unparse(treffer[0].value.args[0]) == button
    quelle = 'ui.circular_progress(min=0, max=100, '
    quelle += 'value=0, color="black")' if mit_wert else 'color="black").classes("invisible")'
    treffer[0].value = ast.parse(quelle, mode='eval').body
