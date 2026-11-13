"""Änderung nach 2.049: Bestehende Einstellungen ohne neue Speicherlogik gestalten."""
from nicegui import ui
# Änderung nach 2.05.00: Vollsicherung im vorhandenen Einstellungsdialog verwalten.
from anwendung.vollsicherung_ui import sicherungseinstellungen_aufbauen


def einstellungen_gestalten(ansicht, karte, auswahl, standard, speichern, abbrechen):
    # Änderung: Bestehende Eingabefelder und Buttons umziehen, keine Werte neu erzeugen.
    bisher = list(karte.default_slot.children)
    karte.classes('ana-settings-dialog')

    def eingabe(feld, label, hinweis, ziel):
        feld.move(ziel)
        feld.classes('w-full')
        feld.props(remove='size')
        feld.props(f'label="{label}" hint="{hinweis}"')

    with karte:
        with ui.column().classes('ana-settings-header'):
            ui.label('Einstellungen').classes('text-xl font-medium')
            ui.label('Änderungen in allen Tabs gemeinsam speichern.').classes('ana-settings-note')
        # Änderung nach 2.05.00: Themen trennen; bestehende Felder und Aktionen weiterverwenden.
        with ui.tabs().props('no-caps outside-arrows mobile-arrows').classes('ana-settings-tabs w-full') as tabs:
            tab_betreiber = ui.tab('Betreiber und Preise')
            tab_ordner = ui.tab('Arbeitsordner')
            tab_sicherung = ui.tab('Datensicherung')
            tab_darstellung = ui.tab('Darstellung')
        # Änderung: Tabwechsel erhalten ungespeicherte Eingaben; nur der Inhalt scrollt.
        with ui.tab_panels(tabs, value=tab_betreiber, keep_alive=True).classes('ana-settings-body ana-settings-panels w-full'):
            with ui.tab_panel(tab_betreiber).classes('ana-settings-operator'):
                ui.label('Betreiber und Bankverbindung').classes('ana-settings-section')
                with ui.element('div').classes('ana-settings-grid') as betreiber:
                    pass
                ui.label('Wärmepreise').classes('ana-settings-section')
                with ui.element('div').classes('ana-settings-grid') as preise:
                    pass
            with ui.tab_panel(tab_ordner).classes('ana-settings-workfolder'):
                ui.label('Arbeitsordner').classes('ana-settings-section')
                ui.label('Hier liegen Datenbanken, Vorlagen und Abrechnungen.').classes('ana-settings-note')
                with ui.column().classes('ana-settings-folder') as ordner:
                    pass
                with ui.row().classes('ana-button-row') as ordner_aktionen:
                    pass
                ui.label('Ein Ordnerwechsel wird nach dem Speichern und einem Neustart wirksam. Standard ist der Programmordner.').classes('ana-settings-note')
            with ui.tab_panel(tab_sicherung) as inhalt_sicherung:
                pass
            with ui.tab_panel(tab_darstellung).classes('ana-settings-appearance'):
                ui.label('Darstellung und Tabellen').classes('ana-settings-section')
                with ui.element('div').classes('ana-settings-grid') as darstellung:
                    pass
        with ui.row().classes('ana-settings-footer') as aktionen:
            pass

    eingabe(ansicht.ini_betreiber_name, 'Name des Betreibers', 'Name für Abrechnungen und Dokumente', betreiber)
    eingabe(ansicht.ini_glaeubiger_id, 'Gläubiger-ID', 'SEPA-Gläubiger-Identifikationsnummer', betreiber)
    eingabe(ansicht.ini_betreiber_iban, 'IBAN des Betreibers', 'Bankverbindung des Betreibers', betreiber)
    eingabe(ansicht.ini_arbeitspreis, 'Wärmepreis', 'Cent pro Kilowattstunde (Ct/kWh)', preise)
    eingabe(ansicht.ini_grundgebuehr, 'Grundgebühr', 'Euro pro Monat (€/Monat)', preise)
    eingabe(ansicht.ini_farbe_spezial, 'Hervorhebungsfarbe', 'Farbname, z. B. light-blue-10', darstellung)
    eingabe(ansicht.ini_farbe_tabelle_edit, 'Bearbeitbare Tabellenzellen', 'Hex-Farbcode, z. B. #ABCDEF', darstellung)
    eingabe(ansicht.ini_tabelle_pagination, 'Zeilen pro Tabellenseite', 'Bisherige Einstellung für die Seitengröße', darstellung)

    ansicht.ini_arbeitsordner.move(ordner)
    ansicht.ini_arbeitsordner.classes('ana-settings-path')
    auswahl.set_text('Ordner auswählen')
    standard.set_text('Programmordner verwenden')
    for button in (auswahl, standard):
        button.move(ordner_aktionen)
        button.classes('ana-compact-button ana-secondary-button')
    # Änderung: Abbrechen und Speichern bleiben stets in derselben unteren Aktionsleiste.
    abbrechen.move(aktionen)
    abbrechen.classes('ana-compact-button ana-secondary-button')
    speichern.move(aktionen)
    speichern.classes('ana-compact-button ana-settings-save')

    # Änderung: Sicherung im eigenen Tab; Speichern/Abbrechen gelten weiterhin für alle Tabs.
    sicherungseinstellungen_aufbauen(ansicht, inhalt_sicherung)

    # Änderung: Nur die alten Überschriften und nun leeren Layoutcontainer ausblenden.
    for element in bisher:
        if element.parent_slot.parent is karte:
            element.classes('hidden')
