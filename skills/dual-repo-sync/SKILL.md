# Dual-Repo Sync Skill

Safely sync changes from the private development branch to the public mirror.

## When to Use
After committing changes to `master` that should be published publicly.

## Architecture

```
Private (master)          Public (public branch)
  [full codebase]           [whitelisted subset only]

  git push private master    git push public public
       │                           │
       │  /sync                     │
       │  checkout public           │
       │  merge master              │
       │  safety check              │
       │  push public public        │
       └───────────────────────────┘
```

## Private Files (Never Public)
- `data/cache/` — SEC EDGAR API response cache
- `data/filings/` — Downloaded XBRL filing XML/facts data
- Any file NOT in `whitelist.txt`

## Commands
- `/sync` — Full sync workflow
- `/sync check` — Safety check only
- `/sync status` — Show sync state

## Sync Workflow
1. Verify working tree is clean
2. Verify `public` remote exists
3. Switch to `public` branch
4. Merge `master` → `public`
5. Validate no files outside `whitelist.txt` are tracked
6. Push to `public` remote
7. Switch back to `master`

## Emergency: Remove Leaked Files from Public
```bash
git push public --delete master  # if master was accidentally pushed
```

## Updating Private Files List
If new private data sources are added:
1. Add path to the private files list in `.kilo/agent/sync.md`
2. Ensure NOT in `whitelist.txt` (whitelist is additive — only what's listed goes public)
3. Add to `.gitignore` if the file should never be tracked on any branch
