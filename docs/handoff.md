# Basira handoff (read this first in a new session)

Last updated: 2026-10-25

## Where things live

| What | Where |
|---|---|
| Code (source of truth) | GitHub `rahilkhan-acadmic/basira`, branch `main` |
| This handoff | `docs/handoff.md` (canonical); project doc `claude/handoff.md` is a mirror |
| AWS estate, manual steps, deploy, cost | `docs/aws-setup.md` (mirror: project doc `claude/aws-setup-runbook.md`) |
| What is not built yet | `docs/limitations.md` |

## Current state

- Milestone M0 (repo scaffold) plus the AWS foundation CDK app for `dev` (`infra/`) are written.
- `main`: dummy README commit, then `4c17a90` (M0 scaffold and AWS foundation) and `64aa33b`
  (GitHub owner for the OIDC deploy role), merged with unrelated histories (`6574745`).
- Nothing is deployed to AWS yet.

## Open items

AWS:
- [ ] Account verification for `basira-dev` (support case open; CloudShell blocked until done)
- [ ] `cdk bootstrap aws://656253649756/ap-south-1 --tags Project=basira`
- [ ] IAM user `basira-deployer` with `BasiraDeployerPolicy` and an access key
- [ ] Decide deploy scope: Security + Auth only (~$3/mo) now, rest at M19, or full dev (~$75–90/mo)
- [ ] After the first deploy: GitHub Environment `dev` variables `AWS_DEPLOY_ROLE_ARN`, `ALERT_EMAIL`; backup budget; budget action

Repo housekeeping:
- [x] Add `docs/handoff.md`

Build:
- [ ] Next milestone after M0 (spec Section 20; see `docs/limitations.md`)

## How to work in a new session

- Code changes: Claude Code on the web with this repo selected (it can push). Cowork sessions in the
  Basira project can read the repo via the GitHub connector but cannot push.
- Claude Code web sessions may not see the project's docs; keep durable notes here in `docs/`.
- The owner's work laptop is not used for this project; all git work happens in Claude sessions.
- At the end of a session, update this file and mirror it to the project doc `claude/handoff.md`.

## Decisions log

- 2026-10-25: Repo restored from bundle and pushed to `main` via Claude Code web after the Cowork
  session was blocked (git proxy repo allowlist; GitHub connector lacked write).
- 2026-10-25: The repo is the single source of truth for handoff notes and runbooks; project docs are mirrors.
