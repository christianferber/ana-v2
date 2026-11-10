"""Änderung: Nur freigegebene Export-Dekoratoren im Strukturvergleich normalisieren."""
import ast


def export_dekoratoren_pruefen(methode):
    erwartet = {
        'abrechnungen_dateien_erstellen': "export_start_absichern('abr_button_pdf', 'abrechnung_pdf_background')",
        'abr_pdf_process': 'export_hintergrund_absichern',
        'rueckv_dateien_erstellen': "export_start_absichern('rueckv_button_pdf', 'rueckv_pdf_background')",
        'rueckv_pdf_process': 'export_hintergrund_absichern',
        'mitglieder_word_process': "export_start_absichern('button_word_export', 'word_erstellung_background')",
        'mitglieder_ja_word_erstellen': 'export_hintergrund_absichern',
        'mitglieder_gv_word_erstellen': 'export_hintergrund_absichern',
    }
    if methode.name in erwartet:
        assert [ast.dump(k) for k in methode.decorator_list] == [
            ast.dump(ast.parse(erwartet[methode.name], mode='eval').body)]
        methode.decorator_list = []
