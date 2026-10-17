# Nächster Arbeitsblock: Releases aus dem Canon-Monorepo

Stand: 17.10.2026. Dies ist die priorisierte Arbeitsliste für den nächsten
Arbeitsblock; erledigte Migrationsschritte stehen in [docs/migration.md](docs/migration.md).

**Ziel:** Die drei Pakete unabhängig aus `mathisarends/canon` veröffentlichen
können, mit einem dokumentierten Prozess, den ein Agent nach einem Release-Auftrag
vollständig über CLI und GitHub Actions bedienen kann.

## Bereits fertig

- [x] `packages/fastapi-canon`, `packages/fastapi-streams` und
  `packages/fastapi-wsrpc` samt Quellhistorien zusammengeführt.
- [x] Gemeinsamer uv-Workspace, Root-Lockfile und getrennte Paket-Testprozesse.
- [x] RPC-Nachfolger auf `fastapi-wsrpc` / `fastapi_wsrpc` umbenannt;
  FastAPI ist Pflichtabhängigkeit, die RPC-Engine bleibt erhalten.
- [x] HTTP/SSE/RPC gemeinsam mit Dishka getestet, auch aus installierten Wheels.
- [x] Referenzdienst auf echte Canon-Komposition und Problem Details umgestellt.
- [x] CI unter Linux/Python 3.12–3.14 und Windows/Python 3.14 grün,
  einschließlich der Referenzdienst-Migration:
  [geprüfter Stand `9dddd21`](https://github.com/mathisarends/canon/actions/runs/39031639556).
- [x] GitHub-Beschreibung/Topics und Profil-README in `../mathisarends` aktualisiert.

## 1. Release-Umfang und Versionen festlegen

Die PyPI-Versionen wurden am 17.10.2026 direkt abgefragt:

| Distribution | Version im Workspace | PyPI | Nächste Aktion |
| --- | --- | --- | --- |
| `fastapi-canon` | `0.4.0` plus `Unreleased` | `0.4.0` | Neue Version für die zusätzliche öffentliche API vorbereiten. |
| `fastapi-streams` | `0.0.1` plus `Unreleased` | `0.0.1` | Neue Version für die Codegen-/SDK-Änderungen vorbereiten. |
| `fastapi-wsrpc` | `0.1.0`, unveröffentlicht | JSON-Endpunkt liefert 404 | Erste Veröffentlichung, gegebenenfalls zunächst als Vorabversion. |

- [ ] Änderungen seit dem jeweils veröffentlichten Stand prüfen und Zielversionen
  festlegen. Canon enthält unter anderem `CanonStreamRouter` und `HTTPMethod`;
  Streams enthält Änderungen an generierten Typen, Fehler-Aliasen und SDK-Dokumentation.
  Den Streams-Changelog deshalb auch auf nötige Client-Migrationen prüfen.
- [ ] Die neuen Inhalte von Canon/Streams unter neuen Versionen veröffentlichen;
  die bereits veröffentlichten Versionsstände nicht für geänderte Builds verwenden.
- [ ] Versionsänderungen je betroffenem Paket durchführen: `pyproject.toml`,
  Changelog und bei Streams/RPC auch `__version__`. Canon bezieht seine
  Distribution-Version derzeit aus den Paketmetadaten.
- [ ] Abhängige Pins gemeinsam anpassen: Root-`pyproject.toml`, Canons `streams`
  Extra und Entwicklungsgruppe sowie den Root-`uv.lock`.
- [ ] Den Referenzdienst berücksichtigen: Er verlangt aktuell
  `fastapi-canon>=0.4,<0.5`. Falls Canon auf `0.5.x` geht, muss diese Range mitziehen.
- [ ] Paket-URLs für Canon/Streams auf das neue Entwicklungsrepo und die passenden
  Unterverzeichnisse umstellen; einige Metadaten verweisen noch auf die alten Repos.
- [ ] Beispiel-Clients nach Versions-/Generatoränderungen regenerieren und ihre
  Driftchecks ausführen, insbesondere die RPC-Generator-Manifeste.

**Reihenfolge:** Zielversionen und Release-Änderungen gemeinsam vorbereiten;
Streams vor einem Canon-Release veröffentlichen, das die neue Streams-Version
verlangt. RPC kann unabhängig erscheinen. Keine gemeinsame Versionsnummer erzwingen.

## 2. Einmalige Einrichtung durch Mathis

Diese Einstellungen liegen bei den GitHub-/PyPI-Konten; sie sind im Repo noch
nicht als eingerichtet nachgewiesen. Der folgende Soll-Vertrag muss vor der
Einrichtung mit dem implementierten Workflow übereinstimmen:

| Publisher-Feld | Vorgeschlagener Wert |
| --- | --- |
| GitHub Owner | `mathisarends` |
| Repository | `canon` |
| Workflow-Datei | `release.yml` unter `.github/workflows/` |
| GitHub Environment | `pypi` |

- [ ] Auf PyPI bei **beiden bestehenden Projekten** `fastapi-canon` und
  `fastapi-streams` den Trusted Publisher für dieses Monorepo prüfen und
  gegebenenfalls hinzufügen.
  Vorhandene Publisher der alten Repos sind keine Konfiguration für `canon`.
  [Anleitung für bestehende Projekte](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
- [ ] Für `fastapi-wsrpc` die Namensannahme prüfen und den **Pending Publisher**
  für das neue Projekt prüfen/einrichten. Der erste erfolgreiche Publish erstellt das
  Projekt; ein Pending Publisher reserviert den Namen noch nicht.
  [Anleitung für neue Projekte](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
- [ ] GitHub-Environment `pypi` und die erlaubten Release-Refs konfigurieren.
  Festlegen, ob Veröffentlichungen zusätzlich einen Environment-Reviewer brauchen.
  Die gewählte Regel im Release-Guide festhalten, damit ein Agent weiß, ob nach
  dem Auslösen noch eine menschliche GitHub-Freigabe aussteht.
- [ ] Schreibzugriff für den zum Release beauftragten Agenten auf Repo/Actions
  sicherstellen. PyPI-Authentifizierung soll über GitHub OIDC erfolgen;
  langfristige PyPI-Tokens sind dafür nicht nötig.
- [ ] Klären, ab wann die bisherigen Repos keine eigenen Paket-Releases mehr
  erzeugen sollen. Repos und historische Tags bleiben zunächst erhalten.

## 3. Agententauglichen Release-Prozess implementieren

**Ist-Zustand:** Im Root existiert nur `ci.yml`, kein Publish-Workflow. Die
`.github`-Verzeichnisse unter `packages/` sind importierte, inaktive Alt-Konfiguration.
Insbesondere der alte Streams-Release-Check erwartet `vX.Y.Z` und einen lokalen
Paket-Lockfile; er funktioniert so nicht als Monorepo-Release-Gate.

- [ ] Eine explizite Paket-Zuordnung für Distribution, Verzeichnis, Import,
  Version und Tag-Präfix implementieren. Release-Checks sollen diese Metadaten
  lesen und keine Paket-Business-Module importieren müssen.
- [ ] Nur die drei Bibliotheken als Release-Ziele zulassen; `canon-workspace`
  und der Entwicklungs-Referenzdienst werden nicht als Stack-Pakete publiziert.
- [ ] Paketbezogene Tags einführen:
  `fastapi-canon-vX.Y.Z`, `fastapi-streams-vX.Y.Z`, `fastapi-wsrpc-vX.Y.Z`.
- [ ] Einen gemeinsamen Release-Check bauen: Paket/Tag/Version müssen
  zusammenpassen; Metadaten, vorhandene Versionskonstanten, Changelog und
  Root-Lockfile müssen konsistent sein. Der Release-Commit muss auf `origin/main`
  liegen und genau dieser Commit die vorgeschriebenen Prüfungen bestanden haben.
- [ ] Root-Workflow `.github/workflows/release.yml` hinzufügen: gezielte
  Paket-Auswahl, Versionsangabe, `workflow_dispatch` und ein echter Dry-run.
  Ein Dry-run prüft und baut Artefakte, ohne PyPI, Release-Tags oder GitHub-Releases
  zu verändern. [GitHub-CLI/Dispatch-Dokumentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
- [ ] Veröffentlichung auf das ausgewählte Paket und dessen frische Artefakte
  begrenzen; keine alten oder fremden Wheels aus einem gemeinsamen `dist/` laden.
  Parallele Releases derselben Paketversion verhindern und bereits veröffentlichte
  Versionen vor dem Upload eindeutig erkennen.
- [ ] Publish-Job mit `environment: pypi` und job-lokalem `id-token: write`
  einrichten. Reguläre PR-/CI-Jobs brauchen keine Veröffentlichungsberechtigung.
- [ ] Wheel/sdist, Metadaten, `py.typed`, Templates, CLI-Einstiegspunkte und
  installierte Consumer prüfen. Erst danach die geprüften Artefakte veröffentlichen.
- [ ] Maschinenlesbare Ergebnisse und verständliche Fehler ausgeben:
  Paket, Version, Commit, Tag, Prüfungen, Artefakt-Hashes und Workflow-/PyPI-Links.
  Wiederaufnahme nach einem fehlgeschlagenen Lauf dokumentieren.
- [ ] `docs/releases.md` und `AGENTS.md` um den vollständigen Ablauf ergänzen:
  Release vorbereiten, Versionen ändern, prüfen, committen/PR erstellen,
  Dry-run starten, beauftragte Veröffentlichung auslösen und Ergebnis kontrollieren.
  Ein Agent soll keine alten Repo-Workflows oder undokumentierten Uploads erraten.

**Vorgeschlagene CLI-Schnittstelle – noch nicht implementiert:**

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=NEXT_VERSION -f dry_run=true
```

Der Workflow muss zunächst gebaut werden; `NEXT_VERSION` ist ein Platzhalter.
Nach einem Release-Auftrag soll derselbe dokumentierte Weg auch das echte
Veröffentlichen unterstützen, unter den eingerichteten GitHub-Regeln.

## 4. Verifikation vor dem ersten Publish ergänzen

- [ ] Abhängigkeits-Minima und neueste kompatible Versionen außerhalb des
  Workspace testen: Canon allein, Streams allein, RPC allein und die unterstützten
  Kombinationen. Die gemeinsame Stack-Untergrenze unterscheidet sich von Canon
  allein, weil Streams mindestens FastAPI `0.143.3` benötigt.
- [ ] Getestete Paketversionen und Abhängigkeits-Ranges in
  [docs/compatibility.md](docs/compatibility.md) veröffentlichen. Der gemeinsame
  Lockfile ersetzt diese Consumer-Prüfungen nicht.
- [ ] Mindestens einen tatsächlichen RPC-Consumer auswählen und mit dem neuen
  Paket testen: Installation, `rpckit` → `fastapi_wsrpc`, CLI, Mounting, Dishka,
  Authentifizierung, Subscriptions sowie verwendete Binary-/Raw-Kanäle.
- [ ] Generierte Python-/TypeScript-Clients gegen dessen exportierten Vertrag
  prüfen und nötige Änderungen im [RPC-Migrationsguide](packages/fastapi-wsrpc/docs/migration.md)
  nachtragen. Die konkrete Consumer-Liste ist noch offen.
- [ ] Einen vollständigen Dry-run für jedes zur Veröffentlichung vorgesehene
  Paket bestehen lassen.

Diese vorhandenen Root-Befehle funktionieren bereits:

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
uv run --locked python scripts/check_streams_artifacts.py
```

## 5. Veröffentlichen und danach prüfen

- [ ] Neue Streams-Version veröffentlichen und aus PyPI in einer frischen
  Umgebung installieren; CLI und generierte Clients prüfen.
- [ ] Neue Canon-Version mit der passenden optionalen Streams-Abhängigkeit
  veröffentlichen; Core allein und `fastapi-canon[streams]` aus PyPI prüfen.
- [ ] `fastapi-wsrpc` erstmals veröffentlichen und den ausgewählten Consumer auf
  die PyPI-Version umstellen. Nicht bereits veröffentlichte Consumer-Migrationen behaupten.
- [ ] GitHub-Release-Notizen, Changelogs, Installationsbeispiele und
  Kompatibilitätsstand auf die tatsächlich verfügbaren Versionen aktualisieren.
- [ ] Alte Repos mit einem klaren Hinweis auf das neue Entwicklungsrepo versehen.
  Sie bleiben wie vereinbart bestehen. `pyrpckit` erst nach bewährtem Ersatz und
  einer späteren ausdrücklichen Archivierungsentscheidung archivieren.

**Dieser Arbeitsblock ist abgeschlossen, wenn** alle drei Pakete aus diesem
Repo gezielt releasbar sind, der Agenten-Ablauf dokumentiert und erprobt ist und
die geplanten Veröffentlichungen anschließend aus PyPI verifiziert wurden.
Bis dahin ist die Workspace-Migration fertig, der Release-Umzug aber noch offen.

## Später, nach den ersten Releases

- [ ] Größere Agent-Run-/Remote-Browser-Beispiele anhand echter Consumer ausbauen.
- [ ] RPC-Ergonomie nur bei belegtem Bedarf weiter ändern; keine neue
  Router-/Protokoll-Abstraktion allein wegen der Umbenennung einführen.
- [ ] Optionale Scaffolding-/Template-Hilfen und einen installierbaren Stack-
  Snapshot oder Constraints-Satz evaluieren.
- [ ] Gemeinsame Codegen-Helfer nur bei tatsächlicher stabiler Wiederverwendung
  extrahieren; keine verpflichtende gemeinsame Runtime vorwegnehmen.

## Startauftrag für den nächsten Agenten

> Lies TODO.md und die verlinkten Release-/Kompatibilitätsdokumente. Implementiere
> zuerst die Release-Prüfungen und den agententauglichen Root-Workflow mit Dry-run.
> Bereite die betroffenen Paketversionen und Pins konsistent vor, führe die Gates
> aus und mache kleine, nachvollziehbare Commits. Dokumentiere konkret, welche
> GitHub-/PyPI-Einrichtung Mathis noch erledigen muss. Dieser Vorbereitungsauftrag
> löst noch keine Veröffentlichung aus; ein nachfolgender Release-Auftrag soll
> vollständig über den dann dokumentierten Prozess ausführbar sein.
