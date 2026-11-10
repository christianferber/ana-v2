# Prüfung 10.11.2026: Fehlerpfade unverändert aus dem Quelltext lokal simulieren.
import ast
from pathlib import Path
from types import SimpleNamespace

source = ast.parse(Path('anwendung/dokumente.py').read_text(encoding='utf-8-sig'))
for name in ('abrechnung_pdf_konvertieren', 'rueckverguetung_pdf_konvertieren'):
    node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == name)
    for failure in ('keiner', 'start', 'sichtbar', 'liste', 'leer', 'fortschritt', 'open', 'save', 'close', 'quit'):
        events = []
        def event(label):
            events.append(label)
            if failure == label:
                raise RuntimeError(label)
        class Word:
            def __init__(self):
                self.Documents = self
            def __setattr__(self, key, value):
                if key == 'Visible': event('sichtbar')
                object.__setattr__(self, key, value)
            def Open(self, path):
                event('open')
                return self
            def SaveAs(self, *args, **kwargs): event('save')
            def Close(self, *args): event('close')
            def Quit(self): event('quit')
        def start(name):
            event('start')
            return Word()
        def listing(path):
            event('liste')
            return [] if failure == 'leer' else ['test.docx']
        import os
        env = dict(pythoncom=SimpleNamespace(CoInitialize=lambda: event('init'), CoUninitialize=lambda: event('uninit')),
                   Dispatch=start, DispatchEx=start,
                   os=SimpleNamespace(listdir=listing, path=os.path))
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<unveraenderter Quelltext>', 'exec'), env)
        error = 'kein Fehler'
        try:
            env[name]('word', 'pdf', lambda value: event('fortschritt'))
        except Exception as exc:
            error = type(exc).__name__ + ':' + str(exc)
        # Änderung: Freigabeversuche auch bei Fehlern im Öffnen, Speichern und Schließen prüfen.
        if failure in ('liste', 'leer'):
            assert 'start' not in events
        else:
            assert events.count('init') == events.count('uninit') == 1
            if failure != 'start':
                assert events.count('quit') == 1
            if failure in ('save', 'close', 'quit', 'keiner'):
                assert events.count('close') == 1
        if failure in ('keiner', 'leer'):
            assert error == 'kein Fehler'
        else:
            assert error == 'RuntimeError:' + failure

print('Word-Fehlerpfade: 20 lokale Simulationen bestanden; kein Word gestartet.')
