---
subagent: sync
description: Sync the private repo to the public mirror. Usage: `/sync`, `/sync check`, `/sync status`.
---

# /sync — Sync Private to Public Mirror

Safely merge the private `master` branch to the public `public` branch and push to the public remote.

**Aliases:** `/sync`

**Sub-commands:**
- `/sync` — Full sync: merge master → public, safety check, push
- `/sync check` — Verify no private files leaked to public branch
- `/sync status` — Show sync state (ahead/behind, diff log)
