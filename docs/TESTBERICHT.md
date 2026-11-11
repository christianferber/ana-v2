# Prüfbericht ANA – aktueller Arbeitsstand

<!-- Änderung für v2: Nur Prüfstatus veröffentlichen, keine Beispieldaten. -->

Stand: 11.11.2026

Umgebung: Windows, Python 3.13.5.

- Verbrauchsstatistik aus Jahresabrechnungen: bestanden.
- Serienbrief-Fettformatierung: bestanden.
- PDF-Fortschritt im Button: bestanden.
- Startanzeige und Ladefolge: bestanden.
- Änderungsprotokoll für Daten und Einstellungen: bestanden.
- Exportoberfläche bei Fehlern: bestanden.
- Word-Fehlerbereinigung: bestanden.
- Ausfallsicherheit von CSV und Sicherungen: bestanden.
- Mitgliederaktualisierung gegen Original: bestanden.
- CSV-Speicherhilfe gegen Original: bestanden.
- Datenbankzugriffe gegen Original: bestanden.
- Datenaufbereitung gegen Original: bestanden.
- Sicherung gegen Original: bestanden.
- Buchungsexport-Bedienung gegen Original: bestanden.
- Statistik gegen Original: bestanden.
- Changelog-Anzeige gegen Original: bestanden.
- Einstellungsansicht gegen Original: bestanden.
- Werkzeuge gegen Original: bestanden.
- Kontodatenansicht gegen Original: bestanden.
- Mitgliederansicht gegen Original: bestanden.
- Abnehmeransicht gegen Original: bestanden.
- Zähleransicht gegen Original: bestanden.
- Testprozesse und Startsperre: bestanden.
- Abschlagsansicht gegen Original: bestanden.
- Jahresabrechnung gegen Referenz: bestanden.
- Berechnung und Abbruchbedingungen: bestanden.
- Rückvergütung gegen Referenz: bestanden.
- Buchungs-CSV und freigegebene Fehlerkorrekturen: bestanden.
- Dateien, INI, Pfade und Strukturvergleich: bestanden.
- Dokumentfelder und simulierte Dokumentaufrufe: bestanden.
- Syntax aller Python-Dateien: bestanden.

Bereits durchgeführte Praxistests: Jahresabrechnung und Rückvergütung über die
Oberfläche berechnet, gespeichert und als echte Word-/PDF-Dateien erzeugt.
Dafür wurden isolierte lokale Datenkopien verwendet. Am 06.11.2026 wurde
der vollständige Rückvergütungs-Dokumentlauf mit 73 Word-Dateien und 73
lesbaren PDFs bestanden; CSV-Referenz und Originalbestand wurden geprüft.
Eine visuelle Dokumentprüfung fand aus
Datenschutzgründen nicht im KI-Kontext statt.

Am 06.11.2026 wurde auch der vollständige Abrechnungslauf nach der
Auslagerung der Oberfläche bestanden: 73 Word-Dateien und 73 lesbare PDFs.
CSV-Referenz und unveränderter Originalbestand wurden geprüft. Gegenüber
dem unmittelbar vorherigen Lauf sind Word-Paketinhalte, PDF-Seitenzahlen
und extrahierte PDF-Texte identisch. Keine visuelle Layoutprüfung.

Version 2.031: Abschlagsspalten, Bearbeiten, Upload und CSV-Speicherung
wurden mit lokalen Beispieldaten gegen das Original geprüft. Der Strukturvergleich
bestätigt alle verschobenen Methoden und die verbliebenen Einstiegspunkte.
Die echte Abschlagstabelle und der anschließende vollständige Abrechnungslauf
wurden am 06.11.2026 mit einer isolierten Datenkopie geprüft: CSV-Referenz
identisch, 73 neue Word-Dateien und 73 lesbare PDFs, Originalbestand unverändert.
Bearbeiten und Speichern der Abschläge wurden über gebundene Methoden geprüft;
im Browser wurde die Tabellenanzeige geprüft. Keine visuelle Dokumentprüfung.
Für 2.031 wurde keine neue Windows-EXE erstellt oder geprüft.

Version 2.032: Windows-Prozessgruppe und Startsperre mit echten Unterprozessen
geprüft. Auch ein nach dem Elternprozess weiterlaufendes Kind wurde nach Erfolg
und simuliertem Testfehler beendet; ein konkurrierender Teststart wurde blockiert.
Vollständiger Beispieldaten-Praxislauf am 06.11.2026 bestanden: Abschlagstabelle,
Abrechnung, CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs.
Original-Beispieldaten unverändert. Während des Laufs genau ein ANA-Testhauptprozess
und ein Fensterprozess bestätigt; anschließend null ANA-Prozesse und null Testbrowser.
Frühere Angaben zur vollständigen Fensterbereinigung waren unzutreffend und sind
mit diesem Stand korrigiert. Keine neue EXE; keine visuelle Dokumentprüfung.

Version 2.033: Alle ausgelagerten Zählermethoden und Adapter strukturell
gegen das Original geprüft. Gebundene Methoden mit lokalen Beispieldaten
für Import, Sortierung, Bearbeitung, Korrekturdialoge und CSV-Speicherung
verglichen. Visualisierungsimport einschließlich Zählerwechsel und
Formatabweisung geprüft. Echtes Zählerregister und vollständige Abrechnung
am 06.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,
73 neue Word-Dateien und 73 lesbare PDFs; Originalbestand per SHA256 unverändert.
Gegenüber dem vorherigen Praxislauf: alle Word-Paketinhalte sowie PDF-Seitenzahlen
und extrahierten Texte identisch.
Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.
Keine visuelle Dokumentprüfung im Modellkontext.

Version 2.034: Alle acht ausgelagerten Abnehmermethoden und Adapter gegen
das Original strukturell geprüft. Gebundene Methoden mit lokalen Beispieldaten
für Spalten, Bearbeiten einschließlich Nullwerten und Abschlagsänderung,
CSV-Speicherung, Upload und Formatabweisung verglichen.
Echtes Abnehmerregister und vollständiger Abrechnungslauf am 08.11.2026
mit isolierter Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien
und 73 lesbare PDFs; Originalbestand per SHA256 unverändert.
Gegenüber 2.033: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.
Keine visuelle Dokumentprüfung. Eine vorzeitig neben dem Praxislauf gestartete
Prozessprüfung wurde von der Startsperre blockiert; die abschließende gebündelte
Freigabeprüfung erfolgte nach Ende des Praxislaufs.

Version 2.035: Alle 22 Mitgliedermethoden und Adapter einschließlich
asynchroner Abläufe und verschachtelter Dialogfunktionen strukturell gegen
das Original geprüft. Gebundene Methoden für Filter, Sortierungen, Auswahl,
Upload/Formatabweisung, Speichern, CSV-Export und beide Word-Mitgliederlisten
mit lokalen Beispieldaten verglichen. Bei lückenhaften Wartungsspalten bleibt
der bereits im Original vorhandene KeyError unverändert; dies wurde verglichen.
Die Auslagerung behebt diesen bestehenden Daten-/Filterfehler nicht.
Echtes Mitgliederregister und vollständige Abrechnung am 08.11.2026 mit
isolierter Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien
und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.
Gegenüber 2.034: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
Test-App, Fenster und Testbrowser vollständig beendet. Keine neue EXE.
Keine visuelle Dokumentprüfung im Modellkontext. Bearbeitungs-, Wartungs-
und Serienbriefdialoge strukturell geprüft; kein vollständiger interaktiver
Durchlauf aller Dialogkombinationen. Erster App-Start wegen fehlender
Hilfsimporte fehlgeschlagen; nach Korrektur vollständiger Praxislauf bestanden.

Version 2.036: Alle acht ausgelagerten Kontodatenmethoden und Adapter
strukturell gegen das Original geprüft. Gebundene Methoden mit lokalen
Beispieldaten für Spalten, Freitext-/Datumsänderung, leere Eingabe, gültige
und ungültige IBAN, Laden, byteidentische CSV-Speicherung und Upload verglichen.
Ungeeignete Uploadformate lösen weiterhin denselben Fehler wie im Original aus.
Buchungs-CSV-Referenzprüfung verwendet die echte gebundene Kontolademethode.
Register Buchungsvorlagen mit echter Kontodatentabelle und vollständiger
Abrechnung am 08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz
identisch, 73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per
SHA256 unverändert. Gegenüber 2.035: Word-Paketinhalte, PDF-Seitenzahlen
und Texte identisch. Test-App, Fenster und Browser vollständig beendet.
Erster Praxisversuch wegen falscher Registerbezeichnung im Test gescheitert;
korrigierter vollständiger Lauf bestanden. Keine neue Windows-EXE.
Keine visuelle Dokumentprüfung im Modellkontext. Bearbeitung und Import
über gebundene Methoden geprüft; im Browser wurde die Tabellenanzeige geprüft.

Version 2.037: Alle sechs Werkzeugmethoden samt drei asynchronen
Ordnerauswahlen und Adaptern strukturell gegen das Original geprüft.
Gebundene Methoden mit lokalen PDF-Beispieldateien verglichen: Ordnerwahl
und Abbruch, fehlende Ordner, leere Eingabeordner, ID-Ermittlung, fehlende
und mehrfache Zuordnungen, Hinweise und Fortschritt. Zusammengefügte PDFs
bytegleich zum Original; Seitenzahl, Seitenreihenfolge und Texte bestätigt.
Native Ordnerdialoge wurden durch lokale Testantworten ersetzt.
Echtes Tools-Register und vollständige Abrechnung am 08.11.2026 mit isolierter
Datenkopie bestanden: CSV-Referenz identisch, 73 neue Word-Dateien und 73
lesbare PDFs. Originalbestand per SHA256 unverändert. Gegenüber 2.036:
Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch. Test-App, Fenster
und Browser vollständig beendet. Keine neue Windows-EXE.
Keine visuelle Dokumentprüfung im Modellkontext. PDF-Zusammenfügen über
gebundene Methoden geprüft; im Browser die Werkzeugeanzeige geprüft.

Version 2.038: Alle vier Einstellungsmethoden und Adapter einschließlich
asynchroner Ordnerwahl strukturell gegen Original geprüft. Gebundene Methoden
mit lokalen Konfigurationskopien verglichen: bytegleiche Anwendungs- und
Betreiber-INI, unveränderter/geänderter/leerer Arbeitsordner, Neustartnachfrage,
Dialogabschluss, erneuter Ladeaufruf, Standard-Rücksetzung, Ordnerwahl und Abbruch.
Originalkonfigurationen unverändert. Native Ordnerdialoge durch Testantworten
ersetzt; tatsächliches Herunterfahren nach Arbeitsordnerwechsel nicht ausgeführt.
Echter Einstellungsdialog geöffnet und abgebrochen; vollständige Abrechnung
am 08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,
73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.
Gegenüber 2.037: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
Test-App, Fenster und Browser vollständig beendet. Erster Dialogtest startete
zu früh; nach Warten auf den Button vollständiger Praxislauf bestanden.
Keine neue Windows-EXE; keine visuelle Dokumentprüfung im Modellkontext.

Version 2.039: Alle drei Changelog-Anzeigemethoden und Adapter strukturell
gegen Original geprüft. Schreibfunktionen unverändert. Gebundene Methoden für
alle acht Filter sowie Filter ohne Treffer, fehlende/leere Protokolldateien
und Markdown-Zeilenumbrüche gegen Original verglichen. Aktualisierung nach
beiden Schreibfunktionen geprüft; Protokolldateien bei festen Zeitstempeln
bytegleich. Die Beispieldaten enthalten kein Changelog; Prüfeinträge wurden
ausschließlich lokal aus Beispielmitgliederdaten abgeleitet.
Echtes Changelog-Register mit Filteranzeige und vollständige Abrechnung am
08.11.2026 mit isolierter Datenkopie bestanden: CSV-Referenz identisch,
73 neue Word-Dateien und 73 lesbare PDFs. Originalbestand per SHA256 unverändert.
Gegenüber 2.038: Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
Test-App, Fenster und Browser vollständig beendet. Filterinhalte über gebundene
Methoden geprüft; im Browser die Register- und Filteranzeige geprüft.
Keine neue Windows-EXE; keine visuelle Dokumentprüfung im Modellkontext.

Version 2.040: Alle fünf Statistikmethoden und Adapter strukturell gegen
Original geprüft. Gebundene Methoden mit lokalen Beispielabrechnungen für
Abnehmerauswahl, Vergleichswerte, fehlende Auswahl/Spalten und CSV-Laden
verglichen. Zusätzlich gefundene Werte mit expliziten Text-Identen aus denselben
lokalen Daten geprüft; dies ändert nicht die bisherige Pandas-Typbehandlung.
Erzeugte Plotly-Figuren und Update-Aufrufe gegen Original verglichen.
Bestehende Einschränkung unverändert: Die neu erzeugte Figur wird vom bisherigen
Code nicht dem Plot zugewiesen; numerisch gelesene Identen können am Textvergleich
vorbeigehen. Keine Korrektur oder Aktivierung des Statistikregisters.
Normaler vollständiger Praxislauf am 08.11.2026 ohne Statistikaktivierung
bestanden: CSV-Referenz identisch, 73 neue Word-Dateien und 73 lesbare PDFs.
Originalbestand per SHA256 unverändert. Gegenüber 2.039: Word-Paketinhalte,
PDF-Seitenzahlen und Texte identisch. Test-App, Fenster und Browser beendet.
Keine interaktive Statistikprüfung und keine visuelle Diagramm-/Dokumentprüfung.
Keine neue Windows-EXE erstellt.

Zurückgezogene Version 2.041 (historischer Prüfstand): Alle sieben Buchungsexport-Bedienmethoden und Adapter einschließlich
asynchroner Speicherdialoge strukturell gegen Original geprüft. Alle 17 gebündelten
Prüfungen und Syntaxprüfung bestanden. Sämtliche lokalen CSV-Referenzfälle über
echte gebundene Bedienmethoden bytegleich; freigegebene Fehlerkorrekturen bestätigt.
Jahreslisten, fehlende/vollständige Auswahl, Dateinamensvorgaben, Speichern und
Abbruch gegen Original verglichen. Native Dateidialoge durch Testantworten ersetzt.
Echtes Buchungsvorlagenregister, Berechnung und CSV-Referenz bestanden. Vollständiger
Praxislauf mit isolierter Word-Testinstanz bestanden: 73 neue Word-Dateien und 73
lesbare PDFs. Originalbestand per SHA256 unverändert. Gegenüber 2.040 sind sämtliche
Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch. App, Fenster und Browser beendet.
Prüfgrenze: Die vorhandene, vor Testbeginn gestartete Word-Sitzung wies COM-Aufrufe
als beschäftigt zurück (RPC_E_CALL_REJECTED); zwei normale Praxisversuche scheiterten
mit AttributeError: Open.SaveAs und wurden abgebrochen. Die Benutzersitzung wurde
nicht beendet. Nur im lokalen Praxisstarteinstieg wurde die Word-Beschaffung durch
DispatchEx ersetzt, um eine eigene Prozess-ID zu erhalten. Der Programmcode und der
Konvertierungsablauf bleiben unverändert. Ein erster isolierter Versuch scheiterte
am Hwnd-Zugriff der Testhilfe; nach Prozess-ID-Erfassung ohne Hwnd erfolgreich.
Die reguläre Word-Anbindung wurde in dieser Sitzung nicht vollständig erfolgreich
geprüft; der erfolgreiche Dokumentlauf gilt für die isolierte Testinstanz.
Keine neue Windows-EXE; keine visuelle Dokumentprüfung im Modellkontext.


Version 2.042: Erneute Buchungsexport-Auslagerung nach Rücknahme von 2.041.
Alle sieben Bedienmethoden und Adapter strukturell gegen Original geprüft.
Alle lokalen CSV-Referenzfälle bytegleich; freigegebene Fehlerkorrekturen bestätigt.
Jahreslisten, fehlende/vollständige Auswahl, Dateinamensvorgaben, Speichern und
Abbruch über echte gebundene Methoden mit lokalen Beispieldaten gegen Original verglichen.
Native Dateidialoge wurden im Methodentest durch lokale Testantworten ersetzt.
Vollständiger REGULÄRER Praxislauf am 08.11.2026 erfolgreich: Buchungsvorlagenregister,
Berechnung und CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs. Die normale
Word-Beschaffung über Dispatch wurde unverändert verwendet, ohne DispatchEx-Ersatz
oder isolierten Word-Starteinstieg. Originalbestand per SHA256 unverändert.
Gegenüber 2.040: sämtliche Word-Paketinhalte, PDF-Seitenzahlen und Texte identisch.
Test-App, Fenster und Browser beendet. Die frühere reguläre Word-Blockierung trat
in diesem Lauf nicht auf. Keine dauerhafte Fehlerbehebung der Word-Umgebung behauptet.
Version 2.041 bleibt zurückgezogen; damalige isolierte Tests sind kein Ersatz für
diesen regulären Lauf. Kein neues Windows-EXE-Paket, keine visuelle Dokumentprüfung.


Version 2.043: Alle vier Sicherungs-/Protokollfunktionen, Adapter und frühe
Initialisierung strukturell gegen Original geprüft. Lokale Beispieldatenkopien:
fehlende/leere Datenbank, Dateien mit copy2-Metadaten, Unterordner, neun neueste
Sicherungsordner, abweichende Höchstzahl und fremde Dateien gegen Original geprüft.
Identische Zeitstempel einschließlich bestehendem FileExistsError bei erneutem
Unterordner-Kopieren verglichen. Pfadwechsel mit derselben Hilfsinstanz geprüft.
Erster Testfehler durch unterschiedliche Zeiten künstlicher Testdateien behoben;
keine dafür erforderliche Änderung des Anwendungscodes. Protokollschreiben über
echte ausgelagerte Methoden bytegleich, anschließende Anzeige unverändert.
Regulärer vollständiger Praxislauf am 08.11.2026 bestanden: Buchungsvorlagenregister,
Berechnung, CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs. Normales Dispatch
ohne isolierten Word-Ersatz. Originalbestand unverändert. Gegen 2.042: sämtliche
Word-Paketinhalte, PDF-Seitenzahlen und PDF-Texte identisch. Test-App, Fenster und
Browser beendet; unabhängige Abfrage: keine ANA- und Word-Prozesse vorhanden.
Keine neue EXE und keine visuelle Dokumentprüfung.

Version 2.044: Fünf unveränderte Funktionen zur Datenaufbereitung ausgelagert.
Funktionskörper und vollständige direkte Importliste strukturell gegen Original
geprüft. Referenz- und Buchungsläufe verwenden echte importierte Funktionen.
Neuer Vergleich mit lokalen Beispieldaten und Sonderfällen für Rückgabewerte,
Eingabemutationen, Rückgabeidentität und bisherige Fehler bestanden.
Alle 19 Freigabeprüfungen und Syntaxprüfung bestanden. Regulärer vollständiger
Praxislauf am 08.11.2026: Buchungsvorlagenregister, Berechnung, CSV-Referenz,
73 neue Word-Dateien und 73 lesbare PDFs. Normales Dispatch ohne isolierten
Word-Ersatz. Original-Beispieldaten unverändert. Gegen 2.043: Word-Paketinhalte,
PDF-Seitenzahlen und PDF-Texte identisch. Test-App, Fenster und Browser beendet.
Unabhängige Prozessabfrage bestätigt null ANA-, Word- und Testbrowserprozesse.
Keine neue EXE, keine visuelle Dokumentprüfung. Versionsanzeige mit zwei
Nachkommastellen bleibt unverändert; dies ist keine Korrektur dieses Anzeigefehlers.

Version 2.045: Zwei Datenbankzugriffe unverändert in DatenbankZugriff
im bestehenden Datenhaltungsmodul ausgelagert. Körper, Adapter, Initialisierung
und Importe strukturell gegen Original geprüft. Buchungsreferenz verwendet
den echten ausgelagerten Datenbankleser. Lokale Beispielkopien für Lesen,
bytegleiches Schreiben, Eingabemutationen, Reihenfolge der sechs Ordneranlagen,
Pfadwechsel mit derselben Instanz, fehlende/leere Dateien und bestehende Fehler
bei leerer Tabelle und falschem Zieltyp gegen Original geprüft.
Alle 20 Freigabeprüfungen und Syntaxprüfung bestanden. Regulärer vollständiger
Praxislauf am 08.11.2026: Buchungsvorlagenregister, Berechnung, CSV-Referenz,
73 neue Word-Dateien und 73 lesbare PDFs. Normale Word-Anbindung ohne isolierten
Ersatz. Originalbestand unverändert. Gegen 2.044: Word-Paketinhalte, PDF-Seitenzahlen
und PDF-Texte identisch. App, Fenster und Browser beendet. Unabhängige Abfrage:
null ANA-, Word- und Testbrowserprozesse. Keine neue EXE, keine visuelle
Dokumentprüfung. Versionsanzeige mit zwei Nachkommastellen bleibt unverändert.

Version 2.046: Gemeinsame asynchrone CSV-Speicherung unverändert in ExportHilfe
ausgelagert. Vollständiger Strukturvergleich von Methode, Adapter, Import und
Initialisierung bestanden. Lokale Beispieldaten und Sonderfälle: bytegleiche
CSV-Dateien, unveränderte Eingaben, gleiche Dialogargumente und Benachrichtigungen,
Abbruch sowie bisherige Fehler bei leerer Tabelle, falschem Zieltyp und Dialogfehler.
Native Dateidialoge im Vergleich durch lokale Testantworten ersetzt.
Alle 21 Freigabeprüfungen und Syntaxprüfung bestanden. Regulärer vollständiger
Praxislauf am 09.11.2026 mit normaler Word-Anbindung bestanden: Buchungsvorlagenregister,
Berechnung, CSV-Referenz, 73 neue Word-Dateien und 73 lesbare PDFs.
Original-Beispieldaten unverändert. Gegen 2.045: Word-Paketinhalte, PDF-Seitenzahlen
und PDF-Texte identisch. Test-App, Fenster und Browser vollständig beendet;
unabhängige Prozessabfrage bestätigt null ANA-, Word- und Testbrowserprozesse.
Keine neue Windows-EXE und keine visuelle Dokumentprüfung. Der bekannte
Versionsanzeigefehler mit zwei Nachkommastellen bleibt unverändert.

Version 2.047: Gemeinsame Mitgliederaktualisierung in DatenbankZugriff
ausgelagert. Strukturvergleich prüft vollständige Methode und Adapter;
nur globale Deklarationen entfallen bei den Anwendungszugriffen.
Lokale Beispieldaten und Sonderfälle für alle 16 Dateistatuskombinationen,
bytegleiche CSV-Dateien, Zeilenänderungen, Listenidentität, doppelte und
unterschiedlich typisierte IDs, fehlende Treffer und leere Daten bestanden.
Speicher-/Ladereihenfolge, erneutes Lesen aktueller Mitgliederwerte und
Abbruchverhalten bei Speicher-/Ladefehlern sowie fehlender Ident geprüft.
Alle 22 Freigabeprüfungen und Syntaxprüfung bestanden. Regulärer vollständiger
Praxislauf am 09.11.2026 mit normaler Word-Anbindung bestanden: Mitgliederregister
mit echter Tabellenanzeige, Berechnung, CSV-Referenz, 73 neue Word-Dateien
und 73 lesbare PDFs. Die Aktualisierung selbst wurde über den echten Adapter
und gebundene Methode mit lokalen Daten geprüft; im Browser die Mitgliederanzeige.
Original-Beispieldaten unverändert. Gegen 2.046: Word-Paketinhalte, PDF-Seitenzahlen
und PDF-Texte identisch. App, Fenster und Browser vollständig beendet;
unabhängige Prozessabfrage bestätigt null ANA-, Word- und Testbrowserprozesse.
Keine neue EXE, keine visuelle Dokumentprüfung. Bekannter Versionsanzeigefehler
mit zwei Nachkommastellen bleibt unverändert.

Vorhandene Release-Archive werden nicht als Nachweis für nachträgliche Quelländerungen verwendet.
Separate Prüfungen der Verzeichnisumstellung sind in docs/STRUKTUR.md dokumentiert.

<!-- Änderung: Abschlussprüfung der Word-Fehlerbereinigung vom 10.11.2026. -->
## Word-Fehlerbereinigung – 10.11.2026

- Alle 24 Freigabeprüfungen einschließlich 20 simulierter Word-Fehlerpfade und
  Syntaxprüfung erfolgreich. Der erste Strukturvergleich erwartete noch den alten
  Ressourcenablauf; nach gezielter Anpassung gesamte Freigabeprüfung bestanden.
- Echtes Word mit synthetischem lokalem Dokument: gezielter SaveAs-Abbruch,
  erfolgreiches Close/Quit und anschließender erneuter PDF-Export bestanden.
- Vollständiger regulärer Abrechnungs-Praxislauf mit normaler Word-Anbindung und
  isolierten lokalen Beispieldaten erfolgreich. 73 neue Word-/PDF-Paare;
  CSV-Referenz und Originalbestand unverändert. Gegen vorherigen Praxislauf:
  Word-Paketinhalte, PDF-Texte und Seitenzahlen identisch.
- App, Fenster und Testbrowser beendet. Unabhängige Prozessabfrage ohne passende
  ANA-, Word- oder Testbrowserprozesse. Keine visuelle Dokumentprüfung.
- Keine Simulation physischer Word-Hänger, keine Garantie bei fehlschlagendem Quit.
  Close-/Quit-Fehler können den ursprünglichen Fehler weiterhin überdecken.
  UI-Fehlermeldungen, Parallelexportsperre und Mitgliederlisten nicht geändert.
- Version/Anzeige 2.047 unverändert; keine neue EXE oder neuer Versionsrelease.

<!-- Änderung: Prüfung der Exportoberfläche vom 10.11.2026. -->
## Exportoberfläche – 10.11.2026

- Alle 25 Freigabeprüfungen und Syntaxprüfung bestanden. Ergänzte tatsächliche
  Mitgliederlisten-Fehlertests nachträglich ebenfalls erfolgreich: jeweils Fehler
  beim Erstellen und Speichern, Fehleranzeige und erneute Knopffreigabe.
- Gezielte Tests aller drei Ansichten: Doppelstart während laufender Arbeit
  verhindert; Vorbereitungs-/Hintergrund-/Threadstartfehler berücksichtigt;
  Freigabe erst nach Threadende, erneuter Versuch möglich, keine internen
  Fehlermeldungen oder Dateninhalte im Meldungstext.
- Regulärer vollständiger Abrechnungslauf mit normaler Word-Anbindung und lokalen
  Beispieldaten bestanden: 73 neue Word-/PDF-Paare, CSV-Referenz und Originalbestand
  unverändert. Gegen vorherigen Stand Word-Paketinhalte, PDF-Texte und Seitenzahlen identisch.
- Rückvergütung im echten Testbrowser: gezielter erster PDF-Fehler sichtbar,
  Exportknopf wieder verfügbar, nächster Versuch mit normaler Word-Anbindung
  erfolgreich. Ein vorhandener Datensatz wie im regulären Rückvergütungs-Smoke-Test;
  CSV-Referenz, lesbares PDF und unveränderter Originalbestand geprüft.
- Test-App, Fenster und Browser beendet; unabhängige Prozessprüfung anschließend.
- Mitgliederlistenfehler mit tatsächlichen Methoden und Ersatz-UI geprüft;
  kein zusätzlicher Browserlauf für diese Listen. Keine visuelle Dokumentprüfung.
- Sperre gilt für erneute Starts derselben Ansicht. Unterschiedliche Exportbereiche
  sind nicht gegenseitig gesperrt. Ein tatsächlich hängender Hintergrundprozess
  bleibt gesperrt; kein automatischer Abbruch oder Wiederanlauf.
- Version/Anzeige 2.047 unverändert, keine neue EXE und kein neuer Versionsrelease.

<!-- Änderung: Vollständigerer Änderungsnachweis für Daten und Einstellungen. -->
## Änderungsprotokoll – 10.11.2026

- Alle 26 Freigabeprüfungen und Syntaxprüfung bestanden. Nach Ergänzung der drei
  Filter und Fehlerbehandlung gezielt Protokollierung, Changelog und gesamten
  Strukturvergleich nochmals erfolgreich geprüft; abschließende Syntax bestanden.
- 22 Protokollrahmen werden mit exakten Aufrufen geprüft; danach vollständiger
  Vergleich der bisherigen Fachkörper. Fachreferenztests isolieren ausschließlich
  die neue zusätzliche Protokollausgabe. Vorhandene Detailprotokolle unverändert.
- Eigene Protokolltests mit tatsächlichen lokalen Logdateien: Datenänderung,
  identische Bestände, neue/geänderte/identische Datenbankdatei, sofortige
  Mitgliederanlage, beide Einstellungsdateien, teilweise fehlgeschlagener
  Kontoimport, unlesbarer Ausgangsstand und Protokollfehler. Ursprüngliche
  Ausnahmen bleiben erhalten. Lokale Beispieldatenkopie verwendet, Quelle unverändert.
- Regulärer vollständiger Abrechnungs-Praxislauf mit normaler Word-Anbindung
  erfolgreich. 73 neue Word-/PDF-Paare, CSV-Referenz und Originalbestand unverändert.
  Gegen vorherigen Stand Word-Paketinhalte, PDF-Texte und Seitenzahlen identisch.
- Praxisprotokolle: tatsächliche Mindestabnahme-/Datenbankänderungen erfasst;
  unveränderte Jahresabrechnungsdatei ohne zusätzlichen Dateieintrag.
  Rückvergütungs-Speichereintrag im echten Praxisprotokoll bestätigt.
- Rückvergütung mit regulärer Word-Anbindung über die Oberfläche erfolgreich,
  ein Datensatz wie im vorhandenen Smoke-Test; CSV und Originalbestand geprüft.
- App, Fenster und Browser beendet; unabhängige Abfrage ohne ANA-, Word- und
  Testbrowserprozesse. Keine visuelle Dokumentprüfung.
- Grenze: Bei fehlenden Schreibrechten, Protokolldatenträgerfehlern oder unlesbarem
  Ausgangsstand ist keine lückenlose Protokollierung garantiert; feste RuntimeWarning,
  Fachablauf bleibt erhalten. Zusammenfassungen nennen Aktion/Bestände/Dateien;
  vorhandene detaillierte Feldprotokolle bleiben ergänzend bestehen.
- Exporte und Sicherungen gemäß Benutzerentscheidung nicht zusätzlich erfasst;
  keine Änderung der Importlogik. Version/Anzeige 2.047 unverändert, keine neue EXE.

<!-- Änderung: Native Startanzeige im Python-Startweg geprüft. -->
## Startanzeige – 10.11.2026

- Alle 27 Freigabeprüfungen und Syntaxprüfung bestanden. Nach Umstellung auf
  einen laufenden Aktivitätsbalken den Startanzeigentest erneut erfolgreich geprüft;
  abschließende Syntaxprüfung ebenfalls bestanden.
- Echte native Tk-Fenster wiederholt geöffnet/geschlossen: automatische Fertigmeldung,
  Kontextabschluss, Freigabe der Fensterthreads und anschließende Speicherbereinigung.
  Ausfall ohne Tk und Startfehler geprüft; Fachstart darf dadurch nicht verhindert werden.
- Ladefolge: ana importiert die Fachoberfläche erst innerhalb der geöffneten Startanzeige.
- Regulärer vollständiger Praxislauf mit echter Startanzeige und normaler Word-
  Anbindung bestanden. Das Startfenster schließt nach tatsächlicher Verbindung
  selbständig; Abschlussmarker vorhanden, kein Ausfallhinweis im lokalen App-Protokoll.
- 73 neue Word-/PDF-Paare, CSV-Referenz und Originalbestand unverändert. Gegen
  vorherigen Praxislauf Word-Paketinhalte, PDF-Texte und Seitenzahlen identisch.
- Test-App, Fenster und Browser beendet; unabhängige Abfrage ohne ANA-, Word-,
  Testbrowser- oder Startvorschauprozesse. Keine visuelle Dokumentprüfung.
- Optische Kontrolle der reinen Startanzeige versucht; Computer-Use-Werkzeug meldet
  fehlende Node-Laufzeit. Keine Screenshotprüfung durchgeführt, Vorschau beendet.
  Funktionale Prüfung der nativen Fenster einschließlich echter App-Verbindung bestanden.
- Kein EXE-Build und kein Test eines neuen Windows-Pakets. Python313 enthält Tk 8.6.
  Version/Anzeige 2.047 unverändert, keine neue EXE und kein neuer Versionsrelease.

<!-- Änderung 2.048: Abschließende Quellfreigabeprüfung. -->
## Freigabe Version 2.048 – 10.11.2026

Version 2.048 bündelt die Startanzeige, erweiterte Änderungsprotokolle,
Exportfehlerbehandlung und sichere CSV-/Datenbankspeicherung und Sicherungen.
Am 10.11.2026 alle 27 Freigabeprüfungen und Syntaxprüfung bestanden.
Regulärer vollständiger Praxislauf mit normaler Word-Anbindung und echter
Startanzeige erfolgreich: 73 neue Word-/PDF-Paare, CSV-Referenz und
Originalbestand unverändert. Die Startanzeige schließt selbständig.
Keine neue EXE kompiliert oder geprüft. Bekannte zweistellige Formatierung
der Versionsanzeige bleibt erhalten; die Versionskonstante lautet 2.048.

Gegen den vorherigen Praxislauf Word-Paketinhalte, PDF-Texte und Seitenzahlen
identisch. Test-App/Fenster/Browser beendet, unabhängige Abfrage ohne ANA-,
Word- oder Testbrowserprozesse. Keine visuelle Dokumentprüfung. Optische Prüfung
der Startanzeige durch fehlende Node-Laufzeit des Computer-Use-Werkzeugs blockiert;
native Fenster und vollständiger App-Start funktional erfolgreich geprüft.

## Arbeitsstand nach 2.049 – Serienbrief-Fettdruck, 11.11.2026

<!-- Änderung nach 2.049: Lokale Serienbriefprüfung dokumentieren. -->

- Tatsächliche Serienbrieferstellung mit lokaler Vorlage und Mitgliederdaten:
  lesbare Word-Dateien, Fettformat, Platzhalter und mehrzeilige Bereiche bestanden.
- Aufgeteilte und unvollständige Markierungen geprüft; ohne Markierung bleiben
  sämtliche Word-XML-Teile unverändert. Originaldatenbank unverändert.
- Im aktuellen Lauf erneut bestanden. Keine visuelle Dokumentprüfung.

## Arbeitsstand nach 2.049 – Verbrauchsstatistik, 11.11.2026

<!-- Änderung nach 2.049: Jahreswerte und neue echte Browserbedienung dokumentieren. -->

- Alle 30 Freigabeprüfungen einschließlich Syntax bestanden.
- Verbrauch und Mindestabnahme sämtlicher vorhandener lokaler Jahresdateien
  unabhängig aus den CSV-Dateien gelesen und gegen die neue Aufbereitung geprüft.
- Text-Ident mit führenden Nullen, chronologische Reihenfolge, echte Nullwerte,
  fehlende Jahre/Abnehmer, ungültige Zahlen, falsche Spalten und doppelte Treffer
  geprüft. Echte NiceGUI-Elemente und beide Plotly-Datenreihen bestanden.
- Vollständiger regulärer Praxislauf mit normaler Word-Anbindung bestanden:
  .lokal/oberflaechentest-20261111-232012-517799. Statistik im echten Browser:
  zwei Dropdowns, zwei Abnehmer nacheinander ausgewählt, beide Jahresreihen exakt
  mit lokaler Aufbereitung verglichen, Layout bei 1440/800 Pixeln bestanden.
- Danach Einstellungen, Berechnung, Speichern/CSV-Referenz und 73 neue Word-/PDF-
  Paare erfolgreich. Original-Beispieldaten vollständig per Prüfsummen unverändert.
- Test-App, Fenster und Testbrowser beendet. Keine visuelle Screenshot- oder
  Dokumentprüfung; keine EXE, keine Veröffentlichung. Version bleibt 2.049.

<!-- Änderung nach 2.049: Abschließenden lokalen Dokumentvergleich ergänzen. -->
Die 73 neuen Word-Paketinhalte und die Texte/Seitenzahlen der 73 PDFs sind
gegenüber dem vorherigen Praxislauf vom 11.11.2026 unverändert. Lokale Vergleichshilfe:
.lokal/statistik_dokumentvergleich_20261111.py.
