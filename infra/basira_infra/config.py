"""Per-environment infrastructure settings (spec Section 16).

Only ``dev`` and ``paper`` are deployable from this app. ``live`` is deliberately absent:
it lives in a separate AWS account, deploys only from tagged releases with manual approval,
and is added at M21 behind the Section 2 gates.
"""

from __future__ import annotations

from dataclasses import dataclass

REGION = "ap-south-1"
PROJECT = "basira"


@dataclass(frozen=True)
class EnvConfig:
    name: str  # "dev" | "paper"
    account: str | None  # AWS account id; None = not created yet
    max_azs: int
    nat_gateways: int  # 1 NAT + Elastic IP = static egress IP for broker whitelisting
    rds_instance_class: str  # e.g. "t4g.micro" -> db.t4g.micro
    rds_allocated_storage_gb: int
    rds_multi_az: bool
    rds_backup_days: int
    redis_node_type: str
    redis_replicas: int
    container_insights: bool
    retain_data: bool  # False only in dev: stacks can be torn down cleanly
    log_retention_days: int

    @property
    def title(self) -> str:
        return self.name.capitalize()

    def resource_name(self, component: str) -> str:
        """Naming convention: basira-<env>-<component>."""
        return f"{PROJECT}-{self.name}-{component}"


ENVIRONMENTS: dict[str, EnvConfig] = {
    "dev": EnvConfig(
        name="dev",
        account="656253649756",
        max_azs=2,
        nat_gateways=1,
        rds_instance_class="t4g.micro",
        rds_allocated_storage_gb=20,
        rds_multi_az=False,
        rds_backup_days=3,
        redis_node_type="cache.t4g.micro",
        redis_replicas=0,
        container_insights=False,
        retain_data=False,
        log_retention_days=30,
    ),
    "paper": EnvConfig(
        name="paper",
        account=None,  # create the basira-paper account before M19/M20, then set its id here
        max_azs=2,
        nat_gateways=1,
        rds_instance_class="t4g.small",
        rds_allocated_storage_gb=50,
        rds_multi_az=False,
        rds_backup_days=14,
        redis_node_type="cache.t4g.small",
        redis_replicas=0,
        container_insights=True,
        retain_data=True,
        log_retention_days=90,
    ),
}


def get_env_config(name: str) -> EnvConfig:
    if name == "live":
        raise ValueError(
            "The live environment cannot be deployed from this app. It requires a separate "
            "AWS account, a tagged release, manual approval and the Section 2 gates (M21)."
        )
    if name not in ENVIRONMENTS:
        raise ValueError(f"Unknown environment {name!r}; expected one of {sorted(ENVIRONMENTS)}")
    return ENVIRONMENTS[name]
