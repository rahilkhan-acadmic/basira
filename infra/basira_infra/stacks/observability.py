"""Audit trail, alert topic and baseline alarms (Sections 2.12, 16)."""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudtrail as cloudtrail
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_kms as kms
from aws_cdk import aws_rds as rds
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subs
from constructs import Construct

from basira_infra.config import EnvConfig


class ObservabilityStack(Stack):
    def __init__(
        self,
        scope: Construct,
        cid: str,
        *,
        cfg: EnvConfig,
        key: kms.IKey,
        db: rds.IDatabaseInstance,
        redis_id: str,
        alert_email: str | None,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]

        self.alerts = sns.Topic(
            self,
            "Alerts",
            topic_name=cfg.resource_name("alerts"),
            display_name=f"Basira {cfg.name} alerts",
            enforce_ssl=True,
        )
        if alert_email:
            self.alerts.add_subscription(subs.EmailSubscription(alert_email))

        # Account-wide management-event trail with integrity validation. The SCP on the Basira OU
        # and the permissions boundary both deny stopping or deleting it.
        trail_bucket = s3.Bucket(
            self,
            "TrailBucket",
            bucket_name=f"{cfg.resource_name('audit-trail')}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            removal_policy=RemovalPolicy.RETAIN,
        )
        cloudtrail.Trail(
            self,
            "Trail",
            trail_name=cfg.resource_name("trail"),
            bucket=trail_bucket,
            is_multi_region_trail=True,
            include_global_service_events=True,
            enable_file_validation=True,
        )

        action = cw_actions.SnsAction(self.alerts)
        alarms = [
            cw.Alarm(
                self,
                "DbCpuHigh",
                alarm_name=cfg.resource_name("pg-cpu-high"),
                metric=db.metric_cpu_utilization(period=Duration.minutes(5)),
                threshold=80,
                evaluation_periods=3,
            ),
            cw.Alarm(
                self,
                "DbStorageLow",
                alarm_name=cfg.resource_name("pg-storage-low"),
                metric=db.metric_free_storage_space(period=Duration.minutes(5)),
                threshold=2 * 1024**3,
                evaluation_periods=1,
                comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
            ),
            cw.Alarm(
                self,
                "RedisMemoryHigh",
                alarm_name=cfg.resource_name("redis-memory-high"),
                metric=cw.Metric(
                    namespace="AWS/ElastiCache",
                    metric_name="DatabaseMemoryUsagePercentage",
                    dimensions_map={"ReplicationGroupId": redis_id},
                    period=Duration.minutes(5),
                ),
                threshold=80,
                evaluation_periods=3,
            ),
        ]
        for a in alarms:
            a.add_alarm_action(action)
