"""Änderung nach 2.049: Bestehende Prozentmeldungen als Balken im Button darstellen."""
from nicegui import ui


class ButtonFortschritt:
    # Änderung: Exporte behalten ihre bisherige Schnittstelle mit Werten von 0 bis 100.
    def __init__(self, button):
        self._wert = 0
        button.classes('ana-progress-button')
        with button:
            # Änderung nach 2.049: Den gemeldeten Prozentwert zusätzlich lesbar im Button zeigen.
            self.prozent = ui.label('0 %').classes('ana-button-percent invisible')
            self.anzeige = ui.linear_progress(value=0, show_value=False, color='primary')
            self.anzeige.classes('ana-button-progress invisible').props('aria-label="PDF-Fortschritt"')

    @property
    def value(self):
        return self._wert

    @value.setter
    def value(self, wert):
        # Änderung: Nur den Darstellungsmaßstab von Prozent auf Quasar 0 bis 1 umrechnen.
        self._wert = wert
        self.prozent.set_text(f'{wert:g} %')
        self.anzeige.set_value(wert / 100)

    def set_value(self, wert):
        self.value = wert

    def classes(self, *args, **kwargs):
        # Änderung: Vorhandene Aufrufe zum Ein-/Ausblenden weiterreichen.
        self.anzeige.classes(*args, **kwargs)
        # Änderung nach 2.049: Zahl und Balken gemeinsam ein-/ausblenden.
        self.prozent.classes(*args, **kwargs)
        return self
