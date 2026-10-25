"""GitHub Actions -> AWS via OIDC: no long-lived keys in GitHub (Section 16 CI/CD)."""

from __future__ import annotations

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from constructs import Construct

from basira_infra.config import EnvConfig

GITHUB_OIDC_URL = "https://token.actions.githubusercontent.com"


class CicdStack(Stack):
    def __init__(
        self,
        scope: Construct,
        cid: str,
        *,
        cfg: EnvConfig,
        github_owner: str,
        github_repo: str,
        repositories: dict[str, ecr.IRepository],
        existing_oidc_provider_arn: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]

        if existing_oidc_provider_arn:
            provider: iam.IOpenIdConnectProvider = (
                iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
                    self, "GithubOidc", existing_oidc_provider_arn
                )
            )
        else:
            provider = iam.OpenIdConnectProvider(
                self, "GithubOidc", url=GITHUB_OIDC_URL, client_ids=["sts.amazonaws.com"]
            )

        # Only workflow jobs running in this repo's GitHub Environment named after cfg.name
        # (e.g. "dev") can assume the role. The Environment can require manual approval.
        self.deploy_role = iam.Role(
            self,
            "GithubDeployRole",
            role_name=cfg.resource_name("github-deploy"),
            max_session_duration=Duration.hours(1),
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                        "token.actions.githubusercontent.com:sub": f"repo:{github_owner}/{github_repo}:environment:{cfg.name}",
                    }
                },
            ),
            description=f"GitHub Actions deploys for {github_owner}/{github_repo} ({cfg.name})",
        )
        # Deploy through CDK's bootstrap roles only.
        self.deploy_role.add_to_policy(
            iam.PolicyStatement(
                sid="AssumeCdkBootstrapRoles",
                actions=["sts:AssumeRole"],
                resources=[f"arn:aws:iam::{self.account}:role/cdk-hnb659fds-*"],
            )
        )
        # Push service images.
        self.deploy_role.add_to_policy(
            iam.PolicyStatement(actions=["ecr:GetAuthorizationToken"], resources=["*"])
        )
        for repo in repositories.values():
            repo.grant_pull_push(self.deploy_role)

        CfnOutput(
            self,
            "GithubDeployRoleArn",
            value=self.deploy_role.role_arn,
            description="Set as GitHub Environment variable AWS_DEPLOY_ROLE_ARN",
        )
