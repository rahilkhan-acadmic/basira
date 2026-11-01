# AWS setup runbook

How the Basira AWS estate is organised, what was set up by hand, and how to deploy.

Last updated: 2026-11-01 (merged the 2026-10-27 bootstrap and first-deploy updates from the old
Cowork project doc `claude/aws-setup-runbook.md`).

## Current state (dev)

- `basira-dev` is CDK-bootstrapped (stack `CDKToolkit`, qualifier `hnb659fds`).
- Deployed on 2026-10-27: `Basira-Dev-Security` and `Basira-Dev-Auth` (KMS key, permissions boundary,
  placeholder secrets, Cognito pool with 4 groups), ~$3/month.
- Not deployed: Network, Data, Compute, Observability, Cicd (planned for M19).
- No long-lived AWS access keys exist. Deploys run from Simurgh CloudShell with temporary portal credentials.

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

- [ ] AWS account verification for `basira-dev` (support case open; CloudShell in basira-dev blocked until done)
- [x] 2026-10-27: `cdk bootstrap aws://656253649756/ap-south-1 --tags Project=basira` (stack `CDKToolkit`, default
      qualifier `hnb659fds`, default AdministratorAccess execution policy). Run from **Simurgh CloudShell** using
      temporary `BasiraAdmin` credentials for basira-dev from the access portal ("Access keys" → export lines).
- [x] IAM user `basira-deployer` with `BasiraDeployerPolicy` (assume `cdk-hnb659fds-*` only) attached
- [x] Decision: **no access key** for `basira-deployer`; deploys run from Simurgh CloudShell with temporary portal credentials until the Cicd stack exists (M19)
- [x] 2026-10-27: first deploy = **Security + Auth only** (`Basira-Dev-Security`, `Basira-Dev-Auth`: CREATE_COMPLETE).
      Network/Data/Compute/Observability/Cicd wait until M19. The `deploy-dev` GitHub workflow needs the Cicd stack, so it is unusable until then.
- GitHub OIDC provider: none existed on 2026-10-27; the Cicd stack creates it.
- [ ] Set real values for the placeholder secrets `basira/dev/*` when providers are chosen (currently random placeholder values)
- [ ] Backup budget in Simurgh filtered to linked account basira-dev (after first charges appear)
- [ ] Budget action on Actual 100% denying resource creation for `basira-deployer`

## Stacks (`infra/`)

All stacks are named `Basira-<Env>-<Stack>`; resources follow `basira-<env>-<component>` and carry
tags `Project=basira`, `Environment=<env>`, `ManagedBy=cdk`. Every IAM role outside the Security
stack gets the `Basira-<Env>-Boundary` permissions boundary.

| Stack | Contents | dev status |
|---|---|---|
| Security | KMS key (rotation on), permissions boundary, placeholder secrets `basira/<env>/...` | Deployed 2026-10-27 |
| Network | VPC 10.40.0.0/16 over 2 AZs; public / app (egress) / data (isolated) subnets; 1 NAT + Elastic IP (static egress IP for broker whitelisting); S3 gateway endpoint; app and data security groups | M19 |
| Data | S3 buckets `md`, `llm`, `knowledge` (KMS, versioned, TLS-only, IA after 90 days); RDS PostgreSQL 16 (private, encrypted, force SSL, PITR); ElastiCache Redis 7.1 (TLS + at-rest encryption) | M19 |
| Compute | ECS Fargate cluster, ECR repos `basira-<env>/app` and `basira-<env>/rasad-ui` (immutable tags, scan on push), Cloud Map namespace, log group, task execution and default task roles | M19 |
| Observability | CloudTrail (multi-region, log file validation), SNS alerts topic, RDS/Redis alarms | M19 |
| Auth | Cognito user pool for Rasad: admin-created users only, TOTP MFA required, groups Viewer / Operator / KnowledgeSteward / Admin | Deployed 2026-10-27 |
| Cicd | GitHub OIDC provider and `basira-<env>-github-deploy` role, trusted only for `repo:<owner>/basira:environment:<env>` | M19 |

## Working in basira-dev without its CloudShell

Until verification completes, use CloudShell in **Simurgh** (ap-south-1), paste the three `export` lines from
portal → basira-dev → BasiraAdmin → **Access keys**, then confirm `aws sts get-caller-identity` shows
`656253649756` before running anything. CloudShell ships with CDK preinstalled (`npm install -g` fails with
EACCES; that is harmless). Credentials expire with the session (≤ 4 h).

Deploying from Simurgh CloudShell (as done on 2026-10-27):

```bash
sudo curl -fsSL -o /etc/yum.repos.d/gh-cli.repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install -y gh
gh auth login --hostname github.com --git-protocol https --web   # device login, no token copied
cd ~ && gh repo clone rahilkhan-acadmic/basira && cd basira && gh auth logout --hostname github.com
python3 -m venv /tmp/cdkvenv && source /tmp/cdkvenv/bin/activate
pip install -q -r infra/requirements.txt && cd infra
export JSII_RUNTIME_PACKAGE_CACHE=disabled            # CloudShell home is mode 0777; jsii refuses its cache
export JSII_SILENCE_WARNING_DEPRECATED_NODE_VERSION=1  # CloudShell ships node 20
npx -y aws-cdk@2.1146.1 diff   -e <stacks> -c env=dev
npx -y aws-cdk@2.1146.1 deploy -e <stacks> -c env=dev --require-approval never
deactivate; cd ~; rm -rf basira /tmp/cdkvenv
```

Use `npx aws-cdk@2.1146.1`, not CloudShell's preinstalled `cdk`, so the CLI matches `aws-cdk-lib` in the repo.

## Deploy

```bash
pip install -r infra/requirements.txt && npm install -g aws-cdk@2.1146.1
cd infra
cdk diff   --all -c env=dev -c github_owner=rahilkhan-acadmic -c alert_email=<email>
cdk deploy --all -c env=dev -c github_owner=rahilkhan-acadmic -c alert_email=<email>
```

Until the Cicd stack exists (M19), deploy from Simurgh CloudShell as above (no long-lived keys).
After it is deployed, set GitHub Environment `dev` variables `AWS_DEPLOY_ROLE_ARN` (stack output)
and `ALERT_EMAIL`, and use the `deploy-dev` workflow.

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

The NAT Gateway is the largest item. Current choice: Security + Auth only (~$3) now, the rest at M19
(the spec allows docker-compose locally through M18). Alternatively, tear down Network/Data when idle in dev.
