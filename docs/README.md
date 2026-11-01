# Basira documentation

All Basira documents live in this folder of the GitHub repo `rahilkhan-acadmic/basira`. This is the
single source of truth: Claude chat, Cowork and Claude Code sessions cannot read each other's
artifacts, project docs or files, but all of them can read this repo.

| Document | What it is |
|---|---|
| [handoff.md](handoff.md) | Current state, open items, decisions log. Read first in every session. |
| [spec.md](spec.md) | Project specification (v10). Build order is Section 20; Section 2 (safety) wins any conflict. |
| [aws-setup.md](aws-setup.md) | AWS estate, manual steps, deploy and cost runbook. |
| [limitations.md](limitations.md) | What is not built yet (spec Section 20.1, item 10). |
| [research/](research/) | Background research notes that fed the spec. |

## Rules

- **Edit here, nowhere else.** Do not create or update docs as claude.ai artifacts, Claude Docs or
  Cowork project docs. If a document is drafted elsewhere, import it into this folder (as
  Markdown) in the same session and stop editing the original.
- **Spec changes:** edit `spec.md`, bump the version line at the top, and record the change in the
  decisions log in `handoff.md`.
- **How each surface works with the repo:**
  - Claude Code (web or CLI): reads and pushes directly.
  - Cowork and Claude chat: read through the GitHub connector. They cannot push, so hand changes to
    a Claude Code session or paste them into a commit.
- Old copies outside the repo (spec artifact, Cowork project docs `claude/handoff.md`,
  `claude/aws-setup-runbook.md`) are superseded. Delete them, or replace their content with a
  pointer to this folder, so no one edits a stale copy.
