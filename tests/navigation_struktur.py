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
    # Änderung nach 2.05.00: Den zusätzlichen Shutdown-Hook ausdrücklich prüfen.
    hooks = [k for k in ast.walk(neu) if isinstance(k, ast.Call)
             and ast.unparse(k.func) == 'app.on_shutdown']
    assert len(hooks) == 1
    gleich(hooks[0], ast.parse('app.on_shutdown(vollsicherung.beim_beenden)', mode='eval').body)
    # Änderung 2.049: Namen, Reihenfolge und Registerwechsel-Callback erhalten.
    vorher = aufrufe(alt, 'tab')
    nachher = aufrufe(neu, 'tab')
    # Änderung nach 2.049: Genau den neuen Statistik-Tab zusätzlich erlauben.
    statistik_tabs = [k for k in nachher if k.args[0].value == 'Statistik']
    assert len(statistik_tabs) == 1
    gleich(statistik_tabs[0], ast.parse("ui.tab('Statistik', icon='show_chart')", mode='eval').body)
    nachher.remove(statistik_tabs[0])
    assert len(vorher) == len(nachher) == 9
    for links, rechts in zip(vorher, nachher):
        gleich(links.args[0], rechts.args[0])
        assert all(k.arg == 'icon' for k in rechts.keywords)
    gleich(aufrufe(alt, 'tabs')[0], aufrufe(neu, 'tabs')[0])
    # Änderung 2.049: Alle Panels mit ihrem vollständigen Fachkörper vergleichen.
    def panels(funktion):
        return [k for k in ast.walk(funktion) if isinstance(k, ast.With)
                and any(aufrufe(item.context_expr, 'tab_panel') for item in k.items)]
    # Änderung nach 2.049: Neues Panel exakt prüfen; vorhandene neun Panels weiter vergleichen.
    neue_panels = panels(neu)
    statistik_panel = next(p for p in neue_panels if ast.unparse(p.items[0].context_expr) == 'ui.tab_panel(tab9)')
    gleich(statistik_panel, ast.parse('with ui.tab_panel(tab9):\n'
        '    verbrauchsstatistik = Verbrauchsstatistik(sys.modules[__name__])\n'
        '    verbrauchsstatistik.aufbauen()').body[0])
    neue_panels.remove(statistik_panel)
    assert len(panels(alt)) == len(neue_panels) == 9
    for links, rechts in zip(panels(alt), neue_panels):
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
    # Änderung nach 2.05.00: Zusätzlichen Beenden-Button aus der Kopfzeile entfernt.
    assert sorted(callbacks) == sorted(['einstellungen_ui', 'navigation.toggle'])
