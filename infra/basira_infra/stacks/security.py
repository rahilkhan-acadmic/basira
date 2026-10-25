"""Security foundation: KMS key, permissions boundary, placeholder secrets (Section 16)."""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_secretsmanager as sm
from constructs import Construct

from basira_infra.config import EnvConfig

BOUNDARY_SUFFIX = "boundary"

# Secrets the services will need. Values are set by a human in the console, never in code
# (Safety Rule 11). Live broker credentials never exist in dev/paper accounts.
PLACEHOLDER_SECRETS = {
    "llm/anthropic": "Anthropic API key",
    "llm/xai": "xAI API key",
    "broker/market-data": "Broker market-data API credentials (no order permissions in paper)",
    "data-vendor": "Licensed data vendor credentials",
}


def boundary_name(cfg: EnvConfig) -> str:
    return f"Basira-{cfg.title}-Boundary"


class SecurityStack(Stack):
    def __init__(self, scope: Construct, cid: str, *, cfg: EnvConfig, **kwargs: object) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]

        self.key = kms.Key(
            self,
            "DataKey",
            alias=f"alias/{cfg.resource_name('data')}",
            description=f"Basira {cfg.name}: encryption at rest for data, secrets and logs",
            enable_key_rotation=True,
            pending_window=Duration.days(7 if not cfg.retain_data else 30),
            removal_policy=RemovalPolicy.RETAIN if cfg.retain_data else RemovalPolicy.DESTROY,
        )
        # Allow CloudWatch Logs in this region to use the key for log groups.
        self.key.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")],
                actions=[
                    "kms:Encrypt*",
                    "kms:Decrypt*",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:Describe*",
                ],
                resources=["*"],
                conditions={
                    "ArnLike": {
                        "kms:EncryptionContext:aws:logs:arn": f"arn:aws:logs:{self.region}:{self.account}:log-group:*"
                    }
                },
            )
        )

        # Maximum permissions any Basira workload role may ever have. Applied to every role in
        # the other stacks by an aspect in app.py.
        self.boundary = iam.ManagedPolicy(
            self,
            "PermissionsBoundary",
            managed_policy_name=boundary_name(cfg),
            description="Max permissions for Basira workload roles",
            statements=[
                iam.PolicyStatement(sid="AllowWorkloads", actions=["*"], resources=["*"]),
                iam.PolicyStatement(
                    sid="NoIamOrAccountChanges",
                    effect=iam.Effect.DENY,
                    actions=[
                        "iam:Create*",
                        "iam:Delete*",
                        "iam:Put*",
                        "iam:Attach*",
                        "iam:Detach*",
                        "iam:Update*",
                        "iam:Add*",
                        "iam:Remove*",
                        "iam:Set*",
                        "iam:Tag*",
                        "iam:Untag*",
                        "iam:Upload*",
                        "organizations:*",
                        "account:*",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="ProtectAuditTrail",
                    effect=iam.Effect.DENY,
                    actions=[
                        "cloudtrail:StopLogging",
                        "cloudtrail:DeleteTrail",
                        "cloudtrail:UpdateTrail",
                        "cloudtrail:PutEventSelectors",
                    ],
                    resources=["*"],
                ),
            ],
        )

        self.secrets: dict[str, sm.Secret] = {}
        for path, desc in PLACEHOLDER_SECRETS.items():
            sid = "Secret" + "".join(p.capitalize() for p in path.replace("-", "/").split("/"))
            self.secrets[path] = sm.Secret(
                self,
                sid,
                secret_name=f"basira/{cfg.name}/{path}",
                description=f"{desc} — set the value manually in the console",
                encryption_key=self.key,
                removal_policy=RemovalPolicy.RETAIN if cfg.retain_data else RemovalPolicy.DESTROY,
            )
