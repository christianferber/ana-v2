"""Änderung: Nur die autorisierten Protokollrahmen strukturell ausnehmen."""
import ast

ERWARTET = {'mitglieder_ui': {'anschluss_aendern.aenderung_speichern': 'aenderungen_protokollieren(self.anwendung, '
                                                            "'MITGLIEDER', 'Anschlussnehmer "
                                                            "wechseln', daten=lambda: "
                                                            "{'Mitglieder': "
                                                            'self.anwendung.mitglieder_db})',
                   'mitglieder_neu.aenderung_speichern': 'aenderungen_protokollieren(self.anwendung, '
                                                         "'MITGLIEDER', 'Mitglied anlegen', "
                                                         "daten=lambda: {'Mitglieder': "
                                                         'self.anwendung.mitglieder_db})',
                   'dialog_mitglieder_editieren.save_changes': 'aenderungen_protokollieren(self.anwendung, '
                                                               "'MITGLIEDER', 'Mitglied "
                                                               "bearbeiten', daten=lambda: "
                                                               "{'Mitglieder': "
                                                               'self.anwendung.mitglieder_db})',
                   'dialog_mitglieder_loeschen.loeschen_ja': 'aenderungen_protokollieren(self.anwendung, '
                                                             "'MITGLIEDER', 'Mitglied löschen', "
                                                             "daten=lambda: {'Mitglieder': "
                                                             'self.anwendung.mitglieder_db})',
                   'editiermodus_aendern.nicht_speichern': 'aenderungen_protokollieren(self.anwendung, '
                                                           "'MITGLIEDER', 'Mitgliederänderungen "
                                                           "verwerfen', daten=lambda: "
                                                           "{'Mitglieder': "
                                                           'self.anwendung.mitglieder_db})',
                   'mitglieder_upload': "aenderungen_protokollieren(self.anwendung, 'MITGLIEDER', "
                                        "'Mitglieder importieren', daten=lambda: {'Mitglieder': "
                                        'self.anwendung.mitglieder_db})'},
 'abnehmer_ui': {'abnehmer_upload': "aenderungen_protokollieren(self.anwendung, 'ABNEHMER', "
                                    "'Abnehmer importieren', daten=lambda: {'Abnehmer': "
                                    'self.anwendung.abnehmer_db})',
                 'abnehmer_tabelle_on_change': 'aenderungen_protokollieren(self.anwendung, '
                                               "'ABNEHMER', 'Abnehmerdaten bearbeiten', "
                                               "daten=lambda: {'Abnehmer': "
                                               "self.anwendung.abnehmer_db, 'Abschläge': "
                                               'self.anwendung.abschlag_db})'},
 'abschlag_ui': {'abschlag_upload': "aenderungen_protokollieren(self.anwendung, 'ABSCHLAG', "
                                    "'Abschläge importieren', daten=lambda: {'Abschläge': "
                                    'self.anwendung.abschlag_db})',
                 'abschlag_tabelle_on_change': 'aenderungen_protokollieren(self.anwendung, '
                                               "'ABSCHLAG', 'Abschläge bearbeiten', daten=lambda: "
                                               "{'Abschläge': self.anwendung.abschlag_db})"},
 'kontodaten_ui': {'konto_upload': "aenderungen_protokollieren(self.anwendung, 'KONTODATEN', "
                                   "'Kontodaten importieren', daten=lambda: {'Kontodaten': "
                                   'self.anwendung.konto_db})',
                   'buchung_tabelle_on_change': 'aenderungen_protokollieren(self.anwendung, '
                                                "'KONTODATEN', 'Kontodaten bearbeiten', "
                                                "daten=lambda: {'Kontodaten': "
                                                'self.anwendung.konto_db})'},
 'zaehler_ui': {'zaehler_liste_upload': "aenderungen_protokollieren(self.anwendung, 'ZÄHLER', "
                                        "'Zählerdaten importieren', daten=lambda: {'Zähler': "
                                        "self.anwendung.zaehler_db, 'Abnehmer': "
                                        'self.anwendung.abnehmer_db})',
                'dialog_zaehlerstand_uebernehmen': 'aenderungen_protokollieren(self.anwendung, '
                                                   "'ZÄHLER', 'Zählerstand übernehmen', "
                                                   "daten=lambda: {'Zähler': "
                                                   'self.anwendung.zaehler_db})',
                'zaehler_tabelle_on_change': "aenderungen_protokollieren(self.anwendung, 'ZÄHLER', "
                                             "'Zählerdaten bearbeiten', daten=lambda: {'Zähler': "
                                             'self.anwendung.zaehler_db})'},
 'datenhaltung': {'db_datei_speichern': "aenderungen_protokollieren(self.anwendung, 'DATENBANK', "
                                        "'Datenbank speichern', daten=lambda: {}, dateien=lambda: "
                                        '(Path(self.anwendung.ordner_datenbank) / dbfile,))',
                  'dbs_mitglieder_aktualisieren': 'aenderungen_protokollieren(self.anwendung, '
                                                  "'MITGLIEDERABGLEICH', 'Mitgliedernamen in "
                                                  "abhängigen Datenbeständen aktualisieren', "
                                                  "daten=lambda: {'Abnehmer': "
                                                  "self.anwendung.abnehmer_db, 'Zähler': "
                                                  "self.anwendung.zaehler_db, 'Abschläge': "
                                                  "self.anwendung.abschlag_db, 'Kontodaten': "
                                                  'self.anwendung.konto_db})'},
 'abrechnung_ui': {'abr_speichern.mindestabnahme_pruefen': 'aenderungen_protokollieren(self.anwendung, '
                                                           "'ABNEHMER', 'Mindestabnahme für das "
                                                           "Folgejahr festlegen', daten=lambda: "
                                                           "{'Abnehmer': "
                                                           'self.anwendung.abnehmer_db})',
                   'abr_speichern.abrechnung_speichern_exec': 'aenderungen_protokollieren(self.anwendung, '
                                                              "'ABRECHNUNG', 'Abrechnung und "
                                                              "Folgeabschläge speichern', "
                                                              "daten=lambda: {'Abschläge': "
                                                              'self.anwendung.abschlag_db}, '
                                                              'dateien=lambda: '
                                                              '(self.datei_abrechnung_aktuell,))'},
 'rueckverguetung_ui': {'rueckv_tabelle_on_change': 'aenderungen_protokollieren(self.anwendung, '
                                                    "'RÜCKVERGÜTUNG', 'Rückvergütung bearbeiten', "
                                                    "daten=lambda: {'Rückvergütung': "
                                                    'self.rueckv_table})',
                        'rueckv_speichern_ja': 'aenderungen_protokollieren(self.anwendung, '
                                               "'RÜCKVERGÜTUNG', 'Rückvergütung speichern', "
                                               'daten=lambda: {}, dateien=lambda: '
                                               '(self.datei_rueckv_aktuell,))'},
 'einstellungen_ui': {'ini_speichern': 'aenderungen_protokollieren(self.anwendung, '
                                       "'EINSTELLUNGEN', 'Einstellungen speichern', daten=lambda: "
                                       '{}, dateien=lambda: (self.anwendung.ini, '
                                       'Path(self.anwendung.arbeitsordner) / '
                                       'self.anwendung.ini_betreiber))'}}


def protokoll_rahmen_pruefen(baum, modul):
    gefunden = set()
    def besuchen(node, prefix=''):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                if name in ERWARTET.get(modul, {}):
                    assert isinstance(child.body[0], ast.With)
                    rahmen = child.body[0]
                    assert len(child.body) == len(rahmen.items) == 1
                    erwartet = ast.parse(ERWARTET[modul][name], mode='eval').body
                    assert ast.dump(rahmen.items[0].context_expr) == ast.dump(erwartet)
                    assert rahmen.items[0].optional_vars is None
                    gefunden.add(name)
                    child.body = rahmen.body
                besuchen(child, name + '.')
            else:
                besuchen(child, prefix)
    besuchen(baum)
    assert gefunden == set(ERWARTET.get(modul, {}))
    return baum
