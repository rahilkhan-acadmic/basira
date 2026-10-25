"""Infrastructure guardrail tests (spec Sections 2, 16, 20.2)."""

from __future__ import annotations

import pytest
from aws_cdk import App
from aws_cdk.assertions import Match, Template
from basira_infra.app_builder import build
from basira_infra.config import get_env_config


@pytest.fixture(scope="module")
def templates() -> dict[str, Template]:
    app = App(context={"github_owner": "example-owner", "alert_email": "ops@example.com"})
    stacks = build(app, "dev")
    return {k: Template.from_stack(s) for k, s in stacks.items()}


def test_live_environment_cannot_be_built() -> None:
    with pytest.raises(ValueError, match="live"):
        get_env_config("live")


def test_single_nat_with_static_eip(templates: dict[str, Template]) -> None:
    t = templates["network"]
    t.resource_count_is("AWS::EC2::NatGateway", 1)
    t.resource_count_is("AWS::EC2::EIP", 1)


def test_database_private_encrypted_ssl(templates: dict[str, Template]) -> None:
    t = templates["data"]
    t.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "PubliclyAccessible": False,
            "StorageEncrypted": True,
            "Engine": "postgres",
        },
    )
    t.has_resource_properties(
        "AWS::RDS::DBParameterGroup", {"Parameters": Match.object_like({"rds.force_ssl": "1"})}
    )


def test_redis_encrypted(templates: dict[str, Template]) -> None:
    templates["data"].has_resource_properties(
        "AWS::ElastiCache::ReplicationGroup",
        {"AtRestEncryptionEnabled": True, "TransitEncryptionEnabled": True},
    )


@pytest.mark.parametrize("stack", ["data", "observability"])
def test_buckets_block_public_access(templates: dict[str, Template], stack: str) -> None:
    buckets = templates[stack].find_resources("AWS::S3::Bucket")
    assert buckets
    for b in buckets.values():
        cfg = b["Properties"]["PublicAccessBlockConfiguration"]
        assert all(
            cfg[k]
            for k in (
                "BlockPublicAcls",
                "BlockPublicPolicy",
                "IgnorePublicAcls",
                "RestrictPublicBuckets",
            )
        )


def test_every_role_outside_security_has_boundary(templates: dict[str, Template]) -> None:
    for name, t in templates.items():
        if name == "security":
            continue
        for logical_id, role in t.find_resources("AWS::IAM::Role").items():
            assert "PermissionsBoundary" in role["Properties"], f"{name}/{logical_id}"


def test_github_role_scoped_to_repo_environment(templates: dict[str, Template]) -> None:
    roles = templates["cicd"].find_resources("AWS::IAM::Role")
    docs = [r["Properties"]["AssumeRolePolicyDocument"] for r in roles.values()]
    subs = [
        s["Condition"]["StringEquals"]["token.actions.githubusercontent.com:sub"]
        for d in docs
        for s in d["Statement"]
        if "Condition" in s
    ]
    assert subs == ["repo:example-owner/basira:environment:dev"]


def test_cognito_no_self_signup_and_mfa(templates: dict[str, Template]) -> None:
    templates["auth"].has_resource_properties(
        "AWS::Cognito::UserPool",
        {
            "MfaConfiguration": "ON",
            "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True},
        },
    )


def test_trail_has_file_validation(templates: dict[str, Template]) -> None:
    templates["observability"].has_resource_properties(
        "AWS::CloudTrail::Trail", {"EnableLogFileValidation": True, "IsMultiRegionTrail": True}
    )
