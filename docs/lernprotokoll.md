# Lernprotokoll Agentic Engineering

CamperLog ist ein Lernprojekt für die Arbeit mit Coding-Agents. Hier steht pro Session, welche Technik wir eingesetzt haben, was funktioniert hat und was nicht. Claude schlägt den Eintrag am Ende einer Session vor, Axi korrigiert.

Aufbau eines Eintrags: **Was** · **Technik** · **Lief gut / lief schlecht** · **Lernpunkt** · optional **Kosten & Modell**

---

## 2026-10-31 — Neuausrichtung: PRD, Architektur, ADRs

**Was:** Die Produktrichtung neu gedacht und als PRD, Architekturbeschreibung, Glossar (CONTEXT.md) und fünf ADRs festgehalten. Lief über zwei Sessions: Die erste wurde unterbrochen, die zweite hat sie fortgesetzt.

**Technik:**
- *Grilling mit Design-Tree* (Skills `grilling` + `domain-modeling`): Fragen in Runden, jede mit Empfehlung, nur Fragen, deren Voraussetzungen schon entschieden sind.
- *Personas als Subagents:* zwei simulierte Camper (Solo-Langzeitreisender, Familie) haben die Grundfragen beantwortet, statt dass nur Axi gefragt wurde.
- *Markt-Recherche als Fork* im Hintergrund, während das Grilling weiterlief.
- *ADRs sparsam:* nur bei schwer umkehrbar + überraschend + echter Abwägung.
- *Session fortsetzen* über das Transkript der vorherigen Session.

**Lief gut:**
- Die Personas haben Spannungen sichtbar gemacht: Jörg wollte *keine* Karte, Sabine wollte sie als Kern, Axi auch. Erst der Widerspruch hat die eigene Vision geschärft.
- Die Recherche hat die Positionierung entschieden („ergänzt Park4Night/Fuelio, ersetzt sie nicht“). Ohne Recherche wäre das eine Bauchentscheidung gewesen.
- Beim Abgleich mit dem Code kam heraus, dass das Dashboard öffentlich ohne Login läuft. Das wurde zu Meilenstein M1.

**Lief schlecht:**
- Das Rohtranskript der alten Session hat zehntausende Tokens in den Hauptkontext geladen. Ein günstiger Subagent (Haiku/Explore) hätte nur die Zusammenfassung liefern können.
- Gepusht, ohne vorher nach einem offenen PR zu schauen: Der Docs-Commit landete im fertigen Fix-PR #10. Es brauchte einen eigenen Branch, PR #11 und einen Force-Push, um das zu trennen.
- Fast eine nicht getroffene Entscheidung ins PRD geschrieben („Trip hat Name/Titel“). Beim Zusammenfassen schleichen sich Annahmen ein.
- Antworten per Spracheingabe kommen teils verstümmelt an („Woo Cin Post“ = „Q14 passt“), und einzelne Fragen blieben unbeantwortet (A1). Der Agent muss seine Deutung offen nennen und Lücken nachfragen.

**Lernpunkte:**
- Simulierte Nutzer liefern Reibung, keine Wahrheit. Wertvoll sind sie dort, wo sie der eigenen Vision widersprechen.
- Teure Lesearbeit (Transkripte, Logs, Recherche) an kleine Subagents geben. Urteils- und Syntheseaufgaben mit viel Gesprächskontext beim Hauptagenten lassen.
- Vor jedem Push prüfen: Gehört der Branch schon zu einem PR?
- Erst Architektur, dann Feature-Zerlegung, weil der Schnitt der Features von Architekturfragen abhängt (z.B. Migrationen).

**Kosten & Modell:** Gestartet auf Sonnet 5, dann auf Opus 5.5 gewechselt. Diskutiert: Grilling und PRD laufen meist auch auf Sonnet gut, Opus lohnt eher für Architektur und schwierige Bugs.

---

## 2026-10-31 — M1 Login: Issues #14 und #15 umgesetzt

**Was:** Meilenstein M1 in zwei gestapelten PRs umgesetzt: Login/Logout für Web und API ([#28](https://github.com/axieccolo1110/camperlog/pull/28), Issue #14), danach Startabbruch ohne Passwort und Secret ([#29](https://github.com/axieccolo1110/camperlog/pull/29), Issue #15). Dazu das Web-Layout responsiv für Handy, Tablet und Rechner gemacht.

**Technik:**
- *Issue als Auftrag:* Story, Akzeptanzkriterien und Hinweise aus dem Issue, dazu Architektur und CLAUDE.md, waren der gesamte Kontext.
- *Gestapelte PRs:* #29 vom Branch von #28 abgezweigt und im PR vermerkt, weil #28 noch nicht gemergt war.
- *Browser-Check mit Playwright* in Handy- und Desktopbreite statt nur Tests.
- *Fester Auftrag mit Report:* Probleme sollten mit Fehlermeldung gemeldet statt umgangen werden.

**Lief gut:**
- Der Browser-Check hat Tabellen und Formulare bei 375 px echt geprüft. Eine Zeile mit `colspan` hätte auf Desktop sonst unbemerkt das Layout zerlegt.
- Der Test mit direktem uvicorn-Start im Subprozess deckt den Railway-Weg ab, den `camperlog serve` allein nicht abdeckt.
- `app` wird erst beim ersten Zugriff gebaut. Dadurch braucht ein Import in Tests keine Umgebungsvariablen.

**Lief schlecht:**
- `make check` war schon vor der Arbeit rot (18 mypy-Fehler in `database.py`). „Fertig, wenn `make check` grün“ ließ sich deshalb nicht erfüllen, ohne fremden Code anzufassen.
- Das Chart ließ sich in der Sandbox nicht prüfen, weil der CDN-Zugriff vom Proxy geblockt wird (403).
- Die Spracheingabe „Oh mitten.“ war nicht eindeutig. Der Agent hat Deutungen angeboten statt zu raten, und „Commit.“ hat sie aufgelöst.

**Lernpunkte:**
- Vor dem Start die Basislinie messen (Tests, Lint, mypy auf `main`). Sonst ist unklar, was der Agent kaputt gemacht hat und was schon kaputt war.
- Bei aufeinander aufbauenden Issues im zweiten PR die Merge-Reihenfolge ausdrücklich dazuschreiben.
- Externe Ressourcen (CDN) sind in Sandboxen oft gesperrt. Das betroffene Stück bleibt dann ungeprüft und gehört ehrlich in den Report.
