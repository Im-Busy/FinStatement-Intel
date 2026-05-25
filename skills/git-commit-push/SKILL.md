# Git Commit & Push — Dual-Repo Aware

Commit and push changes safely, respecting the dual-remote architecture.

## Architecture

```
Private remote: private → master  (full codebase)
Public remote:  public  → public  (whitelisted subset)
```

## Pre-Flight
1. `git remote -v` — verify remotes exist
2. `git branch --show-current` — determine push target
3. `git status` + `git diff --stat` — review changes

## Staging Rules
- Stage: source, tests, docs, configs, agent files, command files, skills
- Never stage: `.vscode/`, `.env`, agent memory, cache data
- Verify: `git diff --cached --stat`

## Commit Format
```
<type>: <description>
```
Types: `feat`, `fix`, `infra`, `docs`, `chore`, `test`, `refactor`

## Push Routing
```
master → git push private master
public → git push public public
```

**CRITICAL**: Never push master to public remote. Never push public to private remote.

## Safety Rules
- Never `--force` push without explicit request
- Never skip hooks without explicit request
- Never push private branch to public remote
- Never commit secrets, credentials, or binary artifacts
