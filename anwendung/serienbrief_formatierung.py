"""Änderung nach 2.049: Fettmarkierungen in fertigen Serienbrieffeldern darstellen."""
from copy import deepcopy
import re

from lxml import etree


def fettmarkierungen_anwenden(document):
    # Änderung: Nur vollständige Paare auswerten; Vorlagenformat und Umbrüche erhalten.
    w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    for absatz in (p for part in document.parts.values() for p in part.iter(w + 'p')):
        texte = list(absatz.iter(w + 't'))
        gesamttext = ''.join(element.text or '' for element in texte)
        paare = list(re.finditer(r'<bold>((?:(?!</?bold>).)*)</bold>', gesamttext, re.DOTALL))
        if not paare:
            continue
        entfernen = set()
        fett = set()
        for paar in paare:
            entfernen.update(range(paar.start(), paar.start(1)))
            entfernen.update(range(paar.end(1), paar.end()))
            fett.update(range(paar.start(1), paar.end(1)))
        position = 0
        # Änderung: Textstücke in eigene Word-Runs aufteilen, bestehende Eigenschaften kopieren.
        for element in texte:
            text = element.text or ''
            run = element.getparent()
            if run.tag != w + 'r':
                position += len(text)
                continue
            stuecke = []
            for index, zeichen in enumerate(text, position):
                if index in entfernen:
                    continue
                ist_fett = index in fett
                if stuecke and stuecke[-1][0] == ist_fett:
                    stuecke[-1][1] += zeichen
                else:
                    stuecke.append([ist_fett, zeichen])
            position += len(text)
            if not any(index in entfernen or index in fett
                       for index in range(position - len(text), position)):
                continue
            # Änderung: Vor-/Nachlauf mit Tabs oder Zeilenumbrüchen bleibt an gleicher Stelle.
            nachlauf = deepcopy(run)
            for kind in list(nachlauf):
                if kind.tag != w + 'rPr':
                    nachlauf.remove(kind)
            for kind in list(run)[list(run).index(element) + 1:]:
                run.remove(kind)
                nachlauf.append(kind)
            eltern = run.getparent()
            einfuegen = eltern.index(run) + 1
            for ist_fett, inhalt in stuecke:
                neu = etree.Element(run.tag, run.attrib)
                eigenschaften = run.find(w + 'rPr')
                if eigenschaften is not None:
                    neu.append(deepcopy(eigenschaften))
                if ist_fett:
                    eigenschaften = neu.find(w + 'rPr')
                    if eigenschaften is None:
                        eigenschaften = etree.SubElement(neu, w + 'rPr')
                    for name in ('b', 'bCs'):
                        for alt in list(eigenschaften.findall(w + name)):
                            eigenschaften.remove(alt)
                        etree.SubElement(eigenschaften, w + name).set(w + 'val', '1')
                neu_text = etree.SubElement(neu, w + 't')
                neu_text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                neu_text.text = inhalt
                eltern.insert(einfuegen, neu)
                einfuegen += 1
            run.remove(element)
            eltern.insert(einfuegen, nachlauf)
