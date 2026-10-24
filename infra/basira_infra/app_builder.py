"""Builds all stacks for one environment. Kept separate from app.py so tests can call it."""

from __future__ import annotations

import jsii
from aws_cdk import App, Aspects, CfnResource, Environment, IAspect, Stack, Tags
from aws_cdk import aws_iam as iam
from constructs import IConstruct

from basira_infra.config import REGION, EnvConfig, get_env_config
from basira_infra.stacks.auth import AuthStack
from basira_infra.stacks.cicd import CicdStack
from basira_infra.stacks.compute import ComputeStack
from basira_infra.stacks.data import DataStack
from basira_infra.stacks.network import NetworkStack
from basira_infra.stacks.observability import ObservabilityStack
from basira_infra.stacks.security import SecurityStack, boundary_name


@jsii.implements(IAspect)
class ApplyBoundary:
    """Attach the Basira permissions boundary to every IAM role in a stack."""

    def __init__(self, boundary_arn: str) -> None:
        self.boundary_arn = boundary_arn

    def visit(self, node: IConstruct) -> None:
        if isinstance(node, iam.CfnRole):
            node.permissions_boundary = self.boundary_arn
        elif isinstance(node, CfnResource) and node.cfn_resource_type == "AWS::IAM::Role":
            # Roles of CDK custom-resource providers are plain CfnResources.
            node.add_property_override("PermissionsBoundary", self.boundary_arn)


def build(app: App, env_name: str) -> dict[str, Stack]:
    cfg: EnvConfig = get_env_config(env_name)
    if cfg.account is None:
        raise ValueError(
            f"No AWS account id configured for {env_name!r} (infra/basira_infra/config.py)"
        )

    env = Environment(account=cfg.account, region=REGION)
    prefix = f"Basira-{cfg.title}"
    alert_email = app.node.try_get_context("alert_email")
    github_owner = app.node.try_get_context("github_owner")
    github_repo = app.node.try_get_context("github_repo") or "basira"
    oidc_arn = app.node.try_get_context("github_oidc_provider_arn")

    security = SecurityStack(
        app,
        f"{prefix}-Security",
        cfg=cfg,
        env=env,
        description="Basira: KMS key, permissions boundary, secrets",
    )
    network = NetworkStack(
        app,
        f"{prefix}-Network",
        cfg=cfg,
        env=env,
        description="Basira: VPC, NAT + static egress IP",
    )
    data = DataStack(
        app,
        f"{prefix}-Data",
        cfg=cfg,
        env=env,
        vpc=network.vpc,
        data_sg=network.data_sg,
        key=security.key,
        description="Basira: S3 data lake, RDS PostgreSQL, ElastiCache Redis",
    )
    compute = ComputeStack(
        app,
        f"{prefix}-Compute",
        cfg=cfg,
        env=env,
        vpc=network.vpc,
        key=security.key,
        buckets=dict(data.buckets),
        description="Basira: ECS cluster, ECR, base task roles",
    )
    observability = ObservabilityStack(
        app,
        f"{prefix}-Observability",
        cfg=cfg,
        env=env,
        key=security.key,
        db=data.db,
        redis_id=cfg.resource_name("redis"),
        alert_email=alert_email,
        description="Basira: CloudTrail, alerts topic, alarms",
    )
    observability.add_stack_dependency(data)
    auth = AuthStack(
        app, f"{prefix}-Auth", cfg=cfg, env=env, description="Basira: Cognito user pool for Rasad"
    )

    stacks: dict[str, Stack] = {
        "security": security,
        "network": network,
        "data": data,
        "compute": compute,
        "observability": observability,
        "auth": auth,
    }
    if github_owner:
        stacks["cicd"] = CicdStack(
            app,
            f"{prefix}-Cicd",
            cfg=cfg,
            env=env,
            github_owner=github_owner,
            github_repo=github_repo,
            repositories=dict(compute.repositories),
            existing_oidc_provider_arn=oidc_arn,
            description="Basira: GitHub Actions OIDC deploy role",
        )

    boundary_arn = f"arn:aws:iam::{cfg.account}:policy/{boundary_name(cfg)}"
    for key, stack in stacks.items():
        Tags.of(stack).add("Project", "basira")
        Tags.of(stack).add("Environment", cfg.name)
        Tags.of(stack).add("ManagedBy", "cdk")
        if key != "security":
            stack.add_stack_dependency(security)
            Aspects.of(stack).add(ApplyBoundary(boundary_arn))
    return stacks
