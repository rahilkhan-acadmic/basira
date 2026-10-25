"""VPC with a static egress IP (NAT Gateway + Elastic IP) for broker whitelisting (Section 16)."""

from __future__ import annotations

from aws_cdk import CfnOutput, Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from basira_infra.config import REGION, EnvConfig


class NetworkStack(Stack):
    def __init__(self, scope: Construct, cid: str, *, cfg: EnvConfig, **kwargs: object) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]

        eips = [
            ec2.CfnEIP(
                self,
                f"NatEip{i + 1}",
                domain="vpc",
                tags=[{"key": "Name", "value": cfg.resource_name(f"nat-eip-{i + 1}")}],
            )
            for i in range(cfg.nat_gateways)
        ]

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=cfg.resource_name("vpc"),
            ip_addresses=ec2.IpAddresses.cidr("10.40.0.0/16"),
            availability_zones=[f"{REGION}{z}" for z in "abc"[: cfg.max_azs]],
            nat_gateways=cfg.nat_gateways,
            nat_gateway_provider=ec2.NatProvider.gateway(
                eip_allocation_ids=[e.attr_allocation_id for e in eips]
            ),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="app", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=22
                ),
                ec2.SubnetConfiguration(
                    name="data", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24
                ),
            ],
            restrict_default_security_group=True,
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(service=ec2.GatewayVpcEndpointAwsService.S3),
            },
        )

        # Security groups shared across stacks. Rules are added where resources are created.
        self.app_sg = ec2.SecurityGroup(
            self,
            "AppSg",
            vpc=self.vpc,
            security_group_name=cfg.resource_name("app-sg"),
            description="Basira ECS services",
            allow_all_outbound=True,
        )
        self.data_sg = ec2.SecurityGroup(
            self,
            "DataSg",
            vpc=self.vpc,
            security_group_name=cfg.resource_name("data-sg"),
            description="Basira RDS and Redis; reachable only from app-sg",
            allow_all_outbound=False,
        )
        self.data_sg.add_ingress_rule(self.app_sg, ec2.Port.tcp(5432), "PostgreSQL from app")
        self.data_sg.add_ingress_rule(self.app_sg, ec2.Port.tcp(6379), "Redis from app")
        Tags.of(self.data_sg).add("Tier", "data")

        for i, eip in enumerate(eips):
            CfnOutput(
                self,
                f"StaticEgressIp{i + 1}",
                value=eip.ref,
                description="Give this IP to the broker for API whitelisting",
            )
