"""Compute foundation: ECS Fargate cluster, ECR repositories, base task roles (Section 16).

Services themselves (Market Data Gateway, Mizan, Shura orchestrator, Rasad API, ...) are added
at the milestone that builds them. This stack gives them a cluster, image registry, namespace,
log group and roles to run with.
"""

from __future__ import annotations

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_servicediscovery as sd
from constructs import Construct

from basira_infra.config import EnvConfig

# One image for all Python services (different entrypoints) + the Rasad UI build image.
REPOSITORIES = ["app", "rasad-ui"]


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        cid: str,
        *,
        cfg: EnvConfig,
        vpc: ec2.IVpc,
        key: kms.IKey,
        buckets: dict[str, s3.IBucket],
        **kwargs: object,
    ) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]
        removal = RemovalPolicy.RETAIN if cfg.retain_data else RemovalPolicy.DESTROY

        self.repositories: dict[str, ecr.Repository] = {}
        for name in REPOSITORIES:
            self.repositories[name] = ecr.Repository(
                self,
                f"Repo{''.join(p.capitalize() for p in name.split('-'))}",
                repository_name=f"basira-{cfg.name}/{name}",
                image_scan_on_push=True,
                image_tag_mutability=ecr.TagMutability.IMMUTABLE,
                encryption=ecr.RepositoryEncryption.KMS,
                encryption_key=key,
                lifecycle_rules=[ecr.LifecycleRule(max_image_count=30)],
                removal_policy=removal,
                empty_on_delete=not cfg.retain_data,
            )

        self.cluster = ecs.Cluster(
            self,
            "Cluster",
            cluster_name=cfg.resource_name("cluster"),
            vpc=vpc,
            enable_fargate_capacity_providers=True,
            container_insights_v2=(
                ecs.ContainerInsights.ENABLED
                if cfg.container_insights
                else ecs.ContainerInsights.DISABLED
            ),
        )

        self.namespace = sd.PrivateDnsNamespace(
            self,
            "Namespace",
            name=f"{cfg.name}.basira.internal",
            vpc=vpc,
            description="Service discovery for Basira services",
        )

        self.log_group = logs.LogGroup(
            self,
            "ServiceLogs",
            log_group_name=f"/basira/{cfg.name}/services",
            retention=logs.RetentionDays(cfg.log_retention_days)
            if cfg.log_retention_days in {r.value for r in logs.RetentionDays}
            else logs.RetentionDays.ONE_MONTH,
            encryption_key=key,
            removal_policy=removal,
        )

        # Pulls images, writes logs, reads secrets at container start.
        self.execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            role_name=cfg.resource_name("task-execution"),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )
        key.grant_decrypt(self.execution_role)
        self.execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:basira/{cfg.name}/*"
                ],
            )
        )

        # Default runtime role for services; per-service roles narrow this at their milestone.
        self.task_role = iam.Role(
            self,
            "TaskRole",
            role_name=cfg.resource_name("task-default"),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Default Basira service role (data buckets, metrics)",
        )
        for b in buckets.values():
            b.grant_read_write(self.task_role)
        self.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": "Basira"}},
            )
        )

        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name)
        for name, repo in self.repositories.items():
            CfnOutput(
                self,
                f"Ecr{''.join(p.capitalize() for p in name.split('-'))}",
                value=repo.repository_uri,
            )
