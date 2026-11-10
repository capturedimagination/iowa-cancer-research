# Iowa cancer research workspace

Start future Iowa cancer work with `knowledge/INDEX.md`. It routes questions to source memos, saved datasets, the searchable SQLite library, provenance and model-readiness notes. This is a local research corpus; it is not model training or a promise of context outside this project.

- Read `research/model-readiness-checklist.md` and `research/modeling-methods.md` before fitting models or interpreting ecological associations.
- Inspect `research/data-source-catalog.json` to distinguish available local data from sources merely identified for later access.
- Search with `python3 scripts/query_research.py search "terms"`; inspect evidence and originals before making claims. Source PDF extraction is not proof of complete source review.
- Preserve raw sources. Keep dates, units, source IDs, qualifiers, missing/suppressed observations, overlapping samples and hashes. Do not equate hazard, reported mass, ambient concentration, modeled lifetime risk, annual observed cancer or causal attribution.
- Form A TRI quantities are unknown despite raw zero placeholders. Missing facility-years are not zero. Keep Pounds and Grams separate. Title V ton definition is unconfirmed. AirToxScreen source-group and pollutant decompositions must not be added together.
- County rates are descriptive and age-adjusted; rounded average annual counts do not supply exact counts or denominators. Do not fit an exact count model from this summary alone.
- Refresh time-sensitive facts for current questions while preserving dated local snapshots and citing their actual observation periods.
- For treatment simulations and discovery claims, read `research/treatment-discovery/discovery-2026-11-10/README.md` and the relevant frozen protocol, results and novelty audit. Retain failed hypotheses. Computational review is not scientific peer review; the gene signature is not a validated functional persister-state marker. The project has not established a new cancer mechanism or cure.
- `scripts/build_knowledge_base.py` rebuilds derived search/data artifacts from saved sources. It does not refresh data or fit a model.

Follow the user's existing preferences, including Brave for personal browsing and the project-folder destination for research outputs.
