# Project Guidelines: reading-CFS-IS-BS

## Python Environment

This project uses **uv** for Python package and environment management. Always use uv commands:

- `uv run <command>` — Run Python scripts/commands in the project environment
- `uv add <package>` — Add a package to the project
- `uv remove <package>` — Remove a package from the project
- `uv sync` — Sync the environment with the lock file
- `uv pip install <package>` — Install packages using uv's pip interface (if needed)

**NEVER** use `python`, `pip`, `python3`, or `pip3` directly. Always prefix commands with `uv`.

Examples:
- Instead of `python script.py`, use `uv run script.py`
- Instead of `pip install requests`, use `uv add requests`
- Instead of `pip install -r requirements.txt`, use `uv sync`

## Session Start Protocol

**Every new AI session MUST:**

1. Read `.kilo/project-rules.md` — Financial analysis guardrails, statement-specific rules, anti-rationalization
2. Read `.kilo/project-loop.md` — DEEPEN/BROADEN/PIVOT/CONCLUDE decision framework
3. Identify the target: which company, which statements (CFS/IS/BS), what period

## Agent-Centric Workflow — Pipeline Agents

The 4-agent pipeline is inspired by pdf-to-markdown-batch-6tools:

| Agent | File | Purpose |
|-------|------|---------|
| **extractor** | `.kilo/agent/extractor.md` | Extracts financial data from source (PDF, HTML, EDGAR, API) |
| **parser** | `.kilo/agent/parser.md` | Parses raw data into structured financial statements |
| **analyzer** | `.kilo/agent/analyzer.md` | Computes ratios, trends, quality checks, anomalies |
| **reporter** | `.kilo/agent/reporter.md` | Generates analysis report with findings, red flags, recommendations |

### Slash Commands

| Command | Agent Pipeline | Usage |
|---------|---------------|-------|
| `/analyze` | extractor → parser → analyzer → reporter | Full analysis of a company's financial statements |
| `/extract` | extractor only | Extract financial data from source documents |
| `/parse` | parser only | Parse raw data into structured statements |
| `/ratio` | analyzer only | Compute financial ratios and metrics |
| `/report` | reporter only | Generate analysis report from structured data |
| `/sync` | sync agent | Sync private master to public mirror |

## Skill: financial-statement-analysis

The core deliverable of this project is the `financial-statement-analysis` skill at `skills/financial-statement-analysis/SKILL.md`. This skill encodes the complete workflow for analyzing Cash Flow Statements, Income Statements, and Balance Sheets.

### Skill Integration
- The skill is loaded when an agent encounters financial analysis tasks
- It teaches the agent how to approach CFS/IS/BS analysis systematically
- It includes ratio definitions, quality checks, warning sign patterns, and reporting templates

## Target Directory Conventions

```
root/
├── .kilo/
│   ├── global-rules.md          # Behavioral, git, coding standards
│   ├── project-rules.md         # Financial analysis guardrails + pipeline architecture
│   ├── project-loop.md          # DEEPEN/BROADEN/PIVOT/CONCLUDE
│   ├── agent/                   # Pipeline agent definitions
│   │   ├── extractor.md
│   │   ├── parser.md
│   │   ├── analyzer.md
│   │   └── reporter.md
│   └── command/                 # Slash command definitions
│       ├── analyze.md
│       ├── extract.md
│       ├── parse.md
│       ├── ratio.md
│       └── report.md
├── src/
│   ├── extraction/              # Data extraction from PDF, HTML, EDGAR, API
│   ├── parsing/                 # Parse raw data into structured statements
│   ├── analysis/                # Ratio computation, trend analysis, quality checks
│   ├── models/                  # Financial models, data structures, enums
│   └── reporting/               # Report generation, formatting, insights
├── skills/
│   └── financial-statement-analysis/
│       └── SKILL.md             # The skill/workflow definition
├── docs/                        # Documentation and reports
├── kilo.json                    # Kilo agent config
├── AGENTS.md                    # This file
├── pyproject.toml               # Project metadata + dependencies
└── main.py                      # Entry point
```

## Anti-Patterns

- `.py` files at root (except `main.py`) → belongs in `src/`
- Analyzing a single statement in isolation → always cross-reference all three
- Using net income as a proxy for cash flow → accrual accounting can mask problems
- Single-year analysis → minimum 3-5 years for trend analysis
- Ignoring footnotes → material information lives there
- Hardcoded financial line-item names → use configurable mapping dictionaries

## Repository Architecture — Dual Remote

```
Private (private remote)          Public (public remote)
  master branch                     public branch
  [full codebase + private data]    [whitelisted subset only]

  git push private master           git push public public
       │                                  │
       │  /sync                           │
       │  checkout public                 │
       │  merge master                    │
       │  safety check vs whitelist.txt   │
       │  push public public              │
       └──────────────────────────────────┘
```

**Whitelist:** `whitelist.txt` defines what appears on the public mirror.
**Private (never public):** `data/cache/`, `data/filings/` — API cache and downloaded XBRL data.
**Git:**
- `git push private master` — push development
- `git push public public` — push curated public mirror
- `/sync` — merge master → public, safety check, push
- `/sync check` — verify no private files on public branch
- `/sync status` — show ahead/behind state
