"""Data layer: S3 data lake, RDS PostgreSQL (+pgvector), ElastiCache Redis (Sections 15, 16)."""

from __future__ import annotations

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticache as elasticache
from aws_cdk import aws_kms as kms
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from constructs import Construct

from basira_infra.config import EnvConfig

# Buckets from Section 15 (S3 layout) and Section 18.16 (knowledge source items).
BUCKETS = {
    "MarketData": "md",  # md/ and eod/ Parquet
    "LlmTranscripts": "llm",  # llm/transcripts/... (encrypted, role-gated)
    "KnowledgeSources": "knowledge",  # source item full text + nightly schema snapshots
}


class DataStack(Stack):
    def __init__(
        self,
        scope: Construct,
        cid: str,
        *,
        cfg: EnvConfig,
        vpc: ec2.IVpc,
        data_sg: ec2.ISecurityGroup,
        key: kms.IKey,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]
        removal = RemovalPolicy.RETAIN if cfg.retain_data else RemovalPolicy.DESTROY

        # ---------- S3 ----------
        self.buckets: dict[str, s3.Bucket] = {}
        for cid_, short in BUCKETS.items():
            self.buckets[short] = s3.Bucket(
                self,
                f"{cid_}Bucket",
                bucket_name=f"{cfg.resource_name(short)}-{self.account}",
                encryption=s3.BucketEncryption.KMS,
                encryption_key=key,
                bucket_key_enabled=True,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                enforce_ssl=True,
                versioned=True,  # Section 16: S3 versioning on data and transcript buckets
                object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
                lifecycle_rules=[
                    s3.LifecycleRule(
                        id="tier-after-90-days",  # Section 15 retention
                        transitions=[
                            s3.Transition(
                                storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                                transition_after=Duration.days(90),
                            )
                        ],
                        noncurrent_version_expiration=Duration.days(90),
                    )
                ],
                removal_policy=removal,
                auto_delete_objects=not cfg.retain_data,
            )

        # ---------- RDS PostgreSQL 16 (pgvector is enabled by migrations: CREATE EXTENSION) ----------
        params = rds.ParameterGroup(
            self,
            "PgParams",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16),
            description="Basira PostgreSQL parameters",
            parameters={"rds.force_ssl": "1", "log_min_duration_statement": "1000"},
        )
        self.db = rds.DatabaseInstance(
            self,
            "Postgres",
            instance_identifier=cfg.resource_name("pg"),
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16),
            instance_type=ec2.InstanceType(cfg.rds_instance_class),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[data_sg],
            database_name="basira",
            credentials=rds.Credentials.from_generated_secret(
                "basira_admin",
                secret_name=f"basira/{cfg.name}/rds/master",
                encryption_key=key,
            ),
            parameter_group=params,
            allocated_storage=cfg.rds_allocated_storage_gb,
            max_allocated_storage=cfg.rds_allocated_storage_gb * 3,
            storage_type=rds.StorageType.GP3,
            storage_encrypted=True,
            storage_encryption_key=key,
            multi_az=cfg.rds_multi_az,
            publicly_accessible=False,
            backup_retention=Duration.days(cfg.rds_backup_days),  # point-in-time recovery
            preferred_backup_window="21:00-21:30",  # 02:30-03:00 IST
            preferred_maintenance_window="sat:22:00-sat:23:00",  # Sun 03:30 IST, market closed
            auto_minor_version_upgrade=True,
            deletion_protection=cfg.retain_data,
            removal_policy=RemovalPolicy.SNAPSHOT if cfg.retain_data else RemovalPolicy.DESTROY,
            cloudwatch_logs_exports=["postgresql"],
            enable_performance_insights=False,
        )

        # ---------- ElastiCache Redis 7 (event bus via Redis Streams + hot state) ----------
        subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        redis_subnets = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnets",
            cache_subnet_group_name=cfg.resource_name("redis-subnets"),
            description="Basira Redis subnets",
            subnet_ids=subnets.subnet_ids,
        )
        self.redis = elasticache.CfnReplicationGroup(
            self,
            "Redis",
            replication_group_id=cfg.resource_name("redis"),
            replication_group_description="Basira event bus (Redis Streams) and hot state",
            engine="redis",
            engine_version="7.1",
            cache_node_type=cfg.redis_node_type,
            num_node_groups=1,
            replicas_per_node_group=cfg.redis_replicas,
            automatic_failover_enabled=cfg.redis_replicas > 0,
            multi_az_enabled=cfg.redis_replicas > 0,
            cache_subnet_group_name=redis_subnets.cache_subnet_group_name,
            security_group_ids=[data_sg.security_group_id],
            at_rest_encryption_enabled=True,
            kms_key_id=key.key_id,
            transit_encryption_enabled=True,
            snapshot_retention_limit=1 if not cfg.retain_data else 7,
            snapshot_window="20:00-21:00",
            preferred_maintenance_window="sat:22:00-sat:23:00",
        )
        self.redis.add_resource_dependency(redis_subnets)
        self.redis.apply_removal_policy(removal)

        CfnOutput(self, "PostgresEndpoint", value=self.db.db_instance_endpoint_address)
        CfnOutput(self, "PostgresSecretName", value=f"basira/{cfg.name}/rds/master")
        CfnOutput(self, "RedisEndpoint", value=self.redis.attr_primary_end_point_address)
        for short, b in self.buckets.items():
            CfnOutput(self, f"Bucket{short.capitalize()}", value=b.bucket_name)
