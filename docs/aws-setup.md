# AWS setup runbook

How the Basira AWS estate is organised, what was set up by hand, and how to deploy.

## Organisation

```
Root (r-zt6m)                         Organization o-c23i8bhbc6
├── Simurgh (345736954421)            management account (also hosts another product)
└── Basira (OU)                       SCP: BasiraGuardrails
    ├── NonProd (OU)
    │   ├── basira-dev   (656253649756)   email rahilkhan.subscription+basira-dev@gmail.com
    │   └── basira-paper (create before M19/M20)
    └── Prod (OU)
        └── basira-live  (create only at M21, live gate)
```

## Done by hand (console)

| Item | Where | Notes |
|---|---|---|
| Organization, OUs, `basira-dev` account | Simurgh → Organizations | Account email uses Gmail plus-addressing |
| Centralised root access management | Simurgh → IAM → Root access management | Member-account root cannot be recovered by "forgot password" |
| IAM Identity Center, `simurgh-org` | Simurgh, ap-south-1, single-Region organization instance | Portal: `https://<id>.awsapps.com/start` |
| User `rahil`, group `basira-admins`, permission set `BasiraAdmin` (AdministratorAccess, 4 h) | Identity Center | Group assigned to `basira-dev` |
| SCP `BasiraGuardrails` | Organizations → Policies, attached to the **Basira** OU | Regions ap-south-1 + us-east-1 only; no leaving org; audit trail protected; root denied |
| Budget `basira-dev-monthly` | basira-dev → Billing → Budgets | Actual 50%, 100%; Forecast 80%, 100%; email only |
| Default console region Mumbai | basira-dev → Unified Settings | |

### Pending

- [ ] AWS account verification for `basira-dev` (support case open; CloudShell blocked until done)
- [ ] `cdk bootstrap aws://656253649756/ap-south-1 --tags Project=basira` (CloudShell in basira-dev as BasiraAdmin)
- [ ] IAM user `basira-deployer` with `BasiraDeployerPolicy` (assume `cdk-hnb659fds-*` only) + access key
- [ ] Backup budget in Simurgh filtered to linked account basira-dev (after first charges appear)
- [ ] Budget action on Actual 100% denying resource creation for `basira-deployer` (after first deploy)

## Stacks (`infra/`)

All stacks are named `Basira-<Env>-<Stack>`; resources follow `basira-<env>-<component>` and carry
tags `Project=basira`, `Environment=<env>`, `ManagedBy=cdk`. Every IAM role outside the Security
stack gets the `Basira-<Env>-Boundary` permissions boundary.

| Stack | Contents |
|---|---|
| Security | KMS key (rotation on), permissions boundary, placeholder secrets `basira/<env>/...` |
| Network | VPC 10.40.0.0/16 over 2 AZs; public / app (egress) / data (isolated) subnets; 1 NAT + Elastic IP (static egress IP for broker whitelisting); S3 gateway endpoint; app and data security groups |
| Data | S3 buckets `md`, `llm`, `knowledge` (KMS, versioned, TLS-only, IA after 90 days); RDS PostgreSQL 16 (private, encrypted, force SSL, PITR); ElastiCache Redis 7.1 (TLS + at-rest encryption) |
| Compute | ECS Fargate cluster, ECR repos `basira-<env>/app` and `basira-<env>/rasad-ui` (immutable tags, scan on push), Cloud Map namespace, log group, task execution and default task roles |
| Observability | CloudTrail (multi-region, log file validation), SNS alerts topic, RDS/Redis alarms |
| Auth | Cognito user pool for Rasad: admin-created users only, TOTP MFA required, groups Viewer / Operator / KnowledgeSteward / Admin |
| Cicd | GitHub OIDC provider and `basira-<env>-github-deploy` role, trusted only for `repo:<owner>/basira:environment:<env>` |

## Deploy

```bash
pip install -r infra/requirements.txt && npm install -g aws-cdk@2.1146.1
cd infra
cdk diff   --all -c env=dev -c github_owner=<github-user> -c alert_email=<email>
cdk deploy --all -c env=dev -c github_owner=<github-user> -c alert_email=<email>
```

First deploy is run with the `basira-deployer` key. Afterwards, set GitHub Environment `dev`
variables `AWS_DEPLOY_ROLE_ARN` (stack output) and `ALERT_EMAIL`, and use the `deploy-dev` workflow.

To deploy only the near-free pieces first: `cdk deploy Basira-Dev-Security Basira-Dev-Auth ...`.

## Approximate dev cost (always on, ap-south-1)

Estimates only; confirm with the AWS Pricing Calculator.

| Item | ~USD / month |
|---|---|
| NAT Gateway (hourly) + data processing | 40–45 |
| Public IPv4 (Elastic IP) | 4 |
| RDS db.t4g.micro single-AZ + 20 GB gp3 | 15–20 |
| ElastiCache cache.t4g.micro | 12–15 |
| KMS key + 5 secrets | 3 |
| S3, CloudWatch logs, CloudTrail, ECR | 1–5 |
| Cognito, ECS cluster without tasks | 0 |
| **Total** | **≈ 75–90** |

The NAT Gateway is the largest item. Options: deploy Security + Auth now (~$3) and the rest at M19
(the spec allows docker-compose locally through M18), or tear down Network/Data when idle in dev.
