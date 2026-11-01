# Basira handoff (read this first in a new session)

Last updated: 2026-11-01

## Where things live

| What | Where |
|---|---|
| Code (source of truth) | GitHub `rahilkhan-acadmic/basira`, branch `main` |
| Index of all docs and the rules for editing them | `docs/README.md` |
| This handoff | `docs/handoff.md` |
| Project specification (v10) | `docs/spec.md` |
| AWS estate, manual steps, deploy, cost | `docs/aws-setup.md` |
| Research notes | `docs/research/` |
| What is not built yet | `docs/limitations.md` |

## Current state

- Milestone M0 (repo scaffold) plus the AWS foundation CDK app for `dev` (`infra/`) are written.
- `main`: dummy README commit, then `4c17a90` (M0 scaffold and AWS foundation) and `64aa33b`
  (GitHub owner for the OIDC deploy role), merged with unrelated histories (`6574745`).
- Nothing is deployed to AWS yet.
- Checks (2026-10-31): `ruff check .` clean; `python -m pytest` 14 passed (needs `pip install -e ".[dev]" -r infra/requirements.txt`;
  bare `pytest` fails to import `core` because the repo root is not on `sys.path`).

## Open items

AWS:
- [ ] Account verification for `basira-dev` (support case open; CloudShell blocked until done)
- [ ] `cdk bootstrap aws://656253649756/ap-south-1 --tags Project=basira`
- [ ] IAM user `basira-deployer` with `BasiraDeployerPolicy` and an access key
- [ ] Decide deploy scope: Security + Auth only (~$3/mo) now, rest at M19, or full dev (~$75–90/mo)
- [ ] After the first deploy: GitHub Environment `dev` variables `AWS_DEPLOY_ROLE_ARN`, `ALERT_EMAIL`; backup budget; budget action

Repo housekeeping:
- [x] Add `docs/handoff.md`
- [x] Import the spec (v10) and research notes into `docs/`; add `docs/README.md`
- [x] claude.ai artifacts marked outdated (title prefix "OUTDATED – " plus a banner linking here):
  spec v10, order-book research doc, repo bundle. Kept, not deleted, by the Owner's choice.
- [ ] Owner: mark the Cowork project docs `claude/handoff.md` and `claude/aws-setup-runbook.md` as
  outdated (Claude Code cannot reach project docs)
- [ ] Add `pythonpath = ["."]` to `[tool.pytest.ini_options]` so bare `pytest` works

Build:
- [ ] M1 Core framework (spec Section 20; see `docs/limitations.md`)

## How to work in a new session

- Code changes: Claude Code on the web with this repo selected (it can push). Cowork sessions in the
  Basira project can read the repo via the GitHub connector but cannot push.
- Claude sessions on different surfaces cannot see each other's artifacts or project docs; every
  durable document lives in `docs/` (rules in `docs/README.md`).
- The owner's work laptop is not used for this project; all git work happens in Claude sessions.
- At the end of a session, update this file. There are no mirrors to keep in sync.

## Decisions log

- 2026-10-25: Repo restored from bundle and pushed to `main` via Claude Code web after the Cowork
  session was blocked (git proxy repo allowlist; GitHub connector lacked write).
- 2026-10-25: The repo is the single source of truth for handoff notes and runbooks; project docs are mirrors.
- 2026-10-31: Claude Code web session verified git pull/push, synced branch `claude/nice-bohr-awer2d` with `main`
  (`fbd3f9f`). `claude/handoff.md` is a project doc, not in the repo; refresh it from this file.
- 2026-11-01: All docs consolidated in the repo. Spec v10 imported from its claude.ai artifact into
  `docs/spec.md`; research note imported into `docs/research/`. Project docs and artifacts are no longer mirrors.
- 2026-11-01: Branch merged to `main`. Old claude.ai copies renamed "OUTDATED – …" with a banner
  pointing to the repo (artifacts have no folders); kept for now.
