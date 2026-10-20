# Notes: Corporate Language Model (CLM), arXiv 2609.04377

Avini & Trez (Unisinos / Care Intelligence), posted 2026-09-03, 22 pp, cs.AI. Position paper. Paper: https://arxiv.org/abs/2609.04377 . Board 1 lives in `whiteboard/combined.excalidraw`.

## Thesis
Enterprise AI fails epistemically, not linguistically: models don't know how *this* firm decides. The design question moves from "which model is best" to "which foundation is deepest". Five failure modes become design constraints from day one:
- **P1** tacit knowledge is never written down
- **P2** no firm-specific ontology
- **P3** no audit path
- **P4** sovereignty (LGPD / GDPR / HIPAA)
- **P5** playbooks can't adapt, agents can't be audited

## Architecture
- **Planes**, each needing the one below: Foundation → Tactical → Wisdom-Out → Governance. A transversal Deep Security layer wraps all four.
- **Neurosymbolic Mesh = guarded generation.**
  - The LLM emits a schema-bounded JSON-LD draft.
  - A symbolic validator checks entity admissibility, relation legality, policy and provenance.
  - A failing draft is rejected (not down-ranked), then repaired or regenerated.
  - Only validated output is rendered. The authors say it is not constrained decoding everywhere.
- **Skill Graph.**
  - G = (V, E, τV, τE): 5 node types, 9 edge types, declared in code.
  - Runtime: admissible set S(c), then Score = 0.4·A + 0.4·E − 0.2·R, with R ∈ {0.1, 0.3, 0.6}.
  - E = EMA (α = 0.3) over the last 500 events; deltas +0.15 / +0.05 / −0.10 / −0.05.
  - Claims "the path is the explanation" and gap discovery.
- **Living Digital Twins**: typed surrogates per function. Runtime: hydrate (ACL at retrieval) → simulate → re-weight → adjust register.
- **Deep Security**: three rings (governance, HITL, sovereignty) and four floors.
- **Spec-as-Code**: a SemanticIntent compiles into Business Spec → BDD → tests → Interface Contracts → Tech Spec, in one derivation chain. The compiler is proprietary.
- **6-stage maturity model**, no skipping. Stages 1-3 in production, 4 in test, 5-6 in design.
- **"Wisdom Listener"**: a named compounding hypothesis with 0 production signals.

## Evidence (feasibility only)
- Snapshot 26 Apr 2026: 41 nodes / 100 edges / 2 objections, 232 tests in 24.5 s.
- Hospital: Clinical Aggregator inside the EHR environment with local de-identification. Go-live was *scheduled* 29 Apr, i.e. after the snapshot.
- No baseline, no ablation, no metrics.

## Critique
1. **No tacit-capture mechanism**: skills are hand-coded (the knowledge-acquisition bottleneck).
2. **"Explainable by construction" covers skill selection, not the LLM's output.** Weights are hand-set, and the matcher is substring matching.
3. **The demo domain is sales; the deployment is a hospital.**
4. **Table 1 is self-graded** (CLM wins all 6 rows).
5. **Missing prior art**: expert systems, Palantir Ontology/AIP, constrained decoding, SHACL.
6. **Conflict of interest**: the authors are the vendor's founders, and the "authorship" registration is with a book chamber.
7. **Inconsistency**: §7.2 says stages 5-6 are in design, but §7.3 says the hospital spec was compiled into the 4 artifacts.
8. **Figure 1 labels Tactical "why we trust it"** (a typo).

## Databricks mapping (mine; verify product statuses before external use)
- Foundation → UC + lineage + metric views
- Skill Graph → UC Skills / UC functions as Genie trusted assets
- Twin state → Lakebase
- Guarded generation → structured outputs + UC functions + MLflow 3 judges
- Legacy tools → UC connections / managed MCP
- Rings → Unity AI Gateway + Apps OBO
- **Gap**: the sovereignty floor (air-gapped / local models)

## What came out of it
Corporate Case Law (CCL): our own approach, designed and tested in this repo (WORKLOG.md, docs/ADR.md, RESULTS_v3.md, dbx/REPORT.md).
