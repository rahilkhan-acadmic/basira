# Basira (بصيرة)

AI-assisted investment and trading desk for NSE delivery shares and stock options, across swing,
positional and investment horizons. No intraday trading. Paper first: live trading needs every
gate in spec Section 2.

| Name | Role |
|---|---|
| **Basira** | The product |
| **Shura** | Agent council, orchestrator and agent runtime (`agents/`) |
| **Mizan** | Deterministic Risk Engine with final veto (`control/`) |
| **Rasad** | Monitoring and analytics UI and Dashboard API (`ui/`, `api/`) |

## Status

Start here: [docs/handoff.md](docs/handoff.md). All docs, including the spec: [docs/](docs/README.md)

Milestone **M0 (repo scaffold)** plus the **AWS foundation** for `dev` (`infra/`).
See `docs/aws-setup.md` for the AWS runbook and `docs/limitations.md` for what is not built yet.

## Safety defaults

- Default mode is `paper` (`core/modes.py`). Mode strings are exactly
  `replay`, `paper`, `live_calibration`, `live`.
- The CDK app refuses to build a `live` environment.
- No secrets in the repo: Secrets Manager only; pre-commit runs gitleaks and AWS-key detection.

## Local development

Requires Python 3.12+, Docker, Node 22 (for CDK).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" -r infra/requirements.txt
pre-commit install
docker compose up -d          # PostgreSQL 16 + pgvector, Redis 7
ruff check . && mypy core && pytest
```

## Infrastructure

```bash
npm install -g aws-cdk@2.1146.1
cd infra && cdk synth -c env=dev -c github_owner=rahilkhan-acadmic
```

Deploying costs money; see the cost table in `docs/aws-setup.md` and get the Owner's approval first.

## Layout

Follows spec Section 21: `config/`, `prompts/`, `core/`, `marketdata/`, `pricing/`, `screens/`,
`books/`, `tools/`, `agents/`, `control/`, `execution/`, `accounting/`, `memory/`, `knowledge/`,
`evaluation/`, `replay/`, `api/`, `ui/`, `infra/`, `scripts/`, `tests/`.
