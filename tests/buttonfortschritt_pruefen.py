"""Änderung nach 2.049: Prozentwerte und Einbettung der echten Fortschrittskomponente prüfen."""
from nicegui import ui
from anwendung.buttonfortschritt import ButtonFortschritt


def pruefen():
    button = ui.button('PDF erstellen')
    fortschritt = ButtonFortschritt(button)
    assert fortschritt.anzeige.parent_slot.parent is button
    # Änderung nach 2.049: Auch die sichtbare Prozentzahl muss zum Button gehören.
    assert fortschritt.prozent.parent_slot.parent is button
    assert 'invisible' in fortschritt.anzeige.classes
    for prozent in (0, 37.5, 100, 0):
        fortschritt.set_value(prozent)
        assert fortschritt.value == prozent
        assert fortschritt.anzeige.value == prozent / 100
        assert fortschritt.prozent.text == f'{prozent:g} %'
    fortschritt.value = 65
    assert fortschritt.anzeige.value == .65
    fortschritt.classes(remove='invisible')
    assert 'invisible' not in fortschritt.anzeige.classes
    assert 'invisible' not in fortschritt.prozent.classes
    fortschritt.classes(add='invisible')
    assert 'invisible' in fortschritt.prozent.classes
    button.delete()
    print('Buttonfortschritt: Einbettung, Prozentmaßstab, Neustart und Sichtbarkeit bestanden.')


if __name__ == '__main__':
    pruefen()
