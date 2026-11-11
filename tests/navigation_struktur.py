"""Änderung 2.049: Fachbindungen unabhängig vom neuen Navigationslayout prüfen."""
import ast
import copy


def hauptfenster_vergleichen(alt, neu):
    # Änderung 2.049: Nur Darstellung darf abweichen, Start und Panelinhalte nicht.
    def aufrufe(knoten, name):
        return [k for k in ast.walk(knoten) if isinstance(k, ast.Call)
                and isinstance(k.func, ast.Attribute)
                and isinstance(k.func.value, ast.Name)
                and k.func.value.id == 'ui' and k.func.attr == name]

    def gleich(links, rechts):
        assert ast.dump(links) == ast.dump(rechts)

    for vorher, nachher in zip(alt.body[:2], neu.body[:2]):
        gleich(vorher, nachher)
    gleich(alt.body[-1], neu.body[-1])
    # Änderung 2.049: Namen, Reihenfolge und Registerwechsel-Callback erhalten.
    vorher = aufrufe(alt, 'tab')
    nachher = aufrufe(neu, 'tab')
    assert len(vorher) == len(nachher) == 9
    for links, rechts in zip(vorher, nachher):
        gleich(links.args[0], rechts.args[0])
        assert all(k.arg == 'icon' for k in rechts.keywords)
    gleich(aufrufe(alt, 'tabs')[0], aufrufe(neu, 'tabs')[0])
    # Änderung 2.049: Alle Panels mit ihrem vollständigen Fachkörper vergleichen.
    def panels(funktion):
        return [k for k in ast.walk(funktion) if isinstance(k, ast.With)
                and any(aufrufe(item.context_expr, 'tab_panel') for item in k.items)]
    assert len(panels(alt)) == len(panels(neu)) == 9
    for links, rechts in zip(panels(alt), panels(neu)):
        gleich(links, rechts)
    vorher = aufrufe(alt, 'tab_panels')[0]
    nachher = copy.deepcopy(aufrufe(neu, 'tab_panels')[0])
    behalten = [k for k in nachher.keywords if k.arg == 'keep_alive']
    assert len(behalten) == 1 and behalten[0].value.value is True
    nachher.keywords = [k for k in nachher.keywords if k.arg != 'keep_alive']
    gleich(vorher, nachher)
    # Änderung 2.049: Nur vorhandene Programmeinstiege und Drawer-Toggle zulassen.
    callbacks = [ast.unparse(k.value) for a in aufrufe(neu, 'button')
                 for k in a.keywords if k.arg == 'on_click']
    # Änderung 2.049: Einstellungen ausschließlich in der Seitenleiste anbieten.
    assert sorted(callbacks) == sorted(['einstellungen_ui',
                                      'app.shutdown', 'navigation.toggle'])
