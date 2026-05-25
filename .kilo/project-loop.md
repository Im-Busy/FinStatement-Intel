# Project Decision Loop: DEEPEN / BROADEN / PIVOT / CONCLUDE

This project operates in a continuous analyze→diagnose→improve→validate loop for financial statement analysis workflows.

## How to Decide
After every completed phase or significant analysis, evaluate the evidence against ALL four directions before choosing.
Apply the **hardest gate first** — if CONCLUDE triggers, it wins. Otherwise, prefer DEEPEN over BROADEN over PIVOT.

## DEEPEN — Analysis Reveals Deeper Questions
**Trigger:** Current analysis approach shows promise but specific weaknesses remain.
**Financial analysis scenarios:** Ratio analysis reveals a trend → deepen with DuPont decomposition. Cash flow looks strong → deepen with quality of earnings analysis. Red flag detected → deepen with peer comparison and historical context.

## BROADEN — Current Analysis Is Solid, Expand Scope
**Trigger:** The current analysis pass has completed and produced acceptable results.
**Gate before broadening:** The base analysis must pass its quality gates first. Never broaden incomplete analysis.
**Examples:** Single-company analysis complete → broaden to peer group. CFS analysis solid → broaden to all three statements. Annual data sufficient → broaden to quarterly trends.

## PIVOT — Evidence Contradicts Assumptions
**Trigger:** Evidence from statements contradicts initial hypotheses.
**Examples:** Assumed strong cash position but CFS reveals persistent negative operating cash flow → pivot to distress analysis. Assumed growth story but revenue growth is entirely acquisition-driven → pivot to organic growth analysis.

## CONCLUDE — Sufficient Evidence for a Decision
Three outcomes:
- **DEPLOY:** Analysis is comprehensive, cross-validated, and actionable. Publish report.
- **ARCHIVE:** Company/statement is not analyzable with available data. Document why.
- **ACCEPT LIMITS:** Partial analysis is the best possible given data constraints.

## Analysis Quality Heuristics
| Metric | DEEPEN | BROADEN | PIVOT | CONCLUDE |
|--------|--------|---------|-------|----------|
| Data Completeness | 60-90% | >90% | <50% | >95% |
| Statement Cross-Validation | 2 of 3 | 3 of 3 | 1 of 3 | 3 of 3 + footnotes |
| Years of Data | 2-3 | 3-5 | <2 | 5+ |
| Peer Comparison | Partial | Full | None | Full + industry |
| Red Flags Resolved | Some | Most | Many open | All resolved or documented |

## Loop Protocol
1. Read AGENTS.md → 2. Run extraction → 3. Run parsing → 4. Run analysis → 5. Generate report → 6. Evaluate quality → 7. Decide direction → 8. Document findings
