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
- `main`: M0 scaffold and AWS foundation (`4c17a90`, `64aa33b`, restored from bundle in `6574745`), then
  docs-only commits: handoff, spec v10 and research import, AWS runbook update.
- AWS `dev`: CDK-bootstrapped; `Basira-Dev-Security` and `Basira-Dev-Auth` deployed 2026-10-27 (~$3/month).
  Network, Data, Compute, Observability and Cicd wait until M19.
- Claude Code sessions for this repo have AWS access: the environment holds an access key for
  `basira-deployer` (added on purpose by the Owner). Deploys need the Owner's approval each time; Simurgh
  CloudShell remains the fallback (details in `docs/aws-setup.md`).
- Checks (2026-10-31): `ruff check .` clean; `python -m pytest` 14 passed (needs `pip install -e ".[dev]" -r infra/requirements.txt`;
  bare `pytest` fails to import `core` because the repo root is not on `sys.path`).

## Open items

AWS (full list in `docs/aws-setup.md`):
- [ ] Account verification for `basira-dev` (support case open; CloudShell in basira-dev blocked until done)
- [x] 2026-10-27: `cdk bootstrap` (stack `CDKToolkit`, qualifier `hnb659fds`), run from Simurgh CloudShell
- [x] IAM user `basira-deployer` with `BasiraDeployerPolicy`; 2026-11-01: access key added for Claude Code sessions
- [ ] Rotate the `basira-deployer` key every 90 days; delete it when the Cicd OIDC role exists (M19)
- [x] Deploy scope decided and done: Security + Auth only (2026-10-27); the rest at M19
- [ ] Real values for placeholder secrets `basira/dev/*` when providers are chosen
- [ ] Backup budget in Simurgh for basira-dev (after first charges); budget action on Actual 100%
- [ ] At M19, after the Cicd stack: GitHub Environment `dev` variables `AWS_DEPLOY_ROLE_ARN`, `ALERT_EMAIL`

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
- 2026-11-01: `docs/aws-setup.md` brought up to date with the 2026-10-27 bootstrap and Security + Auth
  deploy from the old Cowork runbook. Decision recorded: no access key for `basira-deployer` until M19.
- 2026-11-01: The no-access-key decision is reversed. `basira-deployer` has a long-lived key stored in the
  Claude Code environment so sessions can deploy; each deploy still needs the Owner's approval.
