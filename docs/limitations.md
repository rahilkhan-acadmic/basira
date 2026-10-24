# Known limitations and deferred items

Required by spec Section 20.1 (item 10). Keep this current.

## Infrastructure (M0 / early M19)
- Only `dev` is deployable. `paper` needs its own AWS account (set `account` in
  `infra/basira_infra/config.py`). `live` is refused by the CDK app by design until M21.
- Dev runs single-AZ RDS and a single-node Redis without failover; acceptable for dev only.
- One NAT Gateway in one AZ: the static egress IP is a single point of failure in dev/paper.
- No interface VPC endpoints yet (cost); AWS API traffic goes through the NAT.
- No ALB, CloudFront, WAF or ECS services yet; they arrive with M16/M17 and service milestones.
- pgvector is available on RDS PostgreSQL 16 but is enabled by migrations (`CREATE EXTENSION vector`).
- EventBridge start/stop scheduling (Section 16) is not built yet; there are no services to schedule.
- `infra/cdk.context.json` pins the dev account's availability zones so synth needs no AWS access.

## Application
- Only M0 scaffold exists: `core/modes.py` (mode strings and the env/config part of the live gate).
- All hard limits in `config/limits.paper.yaml` are placeholders pending the Owner (Section 23 Q1).
