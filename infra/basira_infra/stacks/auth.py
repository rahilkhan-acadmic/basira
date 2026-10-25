"""Cognito user pool for Rasad (Sections 16, 17.3). Admin-created users only, MFA required."""

from __future__ import annotations

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct

from basira_infra.config import EnvConfig

# Application roles from Section 17.3 (Owner maps to the Admin group).
RASAD_GROUPS = {
    "Viewer": "Read dashboards",
    "Operator": "Viewer + kill switch trigger, alert ack, playbook lesson decisions",
    "KnowledgeSteward": "Viewer + knowledge review queue decisions",
    "Admin": "Owner: approvals, limits, live gates, kill switch reset, users",
}


class AuthStack(Stack):
    def __init__(self, scope: Construct, cid: str, *, cfg: EnvConfig, **kwargs: object) -> None:
        super().__init__(scope, cid, **kwargs)  # type: ignore[arg-type]

        self.user_pool = cognito.UserPool(
            self,
            "RasadUsers",
            user_pool_name=cfg.resource_name("rasad-users"),
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            mfa=cognito.Mfa.REQUIRED,
            mfa_second_factor=cognito.MfaSecondFactor(otp=True, sms=False),
            password_policy=cognito.PasswordPolicy(
                min_length=14,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
                temp_password_validity=Duration.days(3),
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN if cfg.retain_data else RemovalPolicy.DESTROY,
        )
        for name, desc in RASAD_GROUPS.items():
            cognito.CfnUserPoolGroup(
                self,
                f"Group{name}",
                user_pool_id=self.user_pool.user_pool_id,
                group_name=name,
                description=desc,
            )

        # SPA client: authorization code + PKCE, no client secret. Callback URLs are updated when
        # the Rasad UI is hosted (M17).
        self.client = self.user_pool.add_client(
            "RasadWeb",
            user_pool_client_name=cfg.resource_name("rasad-web"),
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=["http://localhost:5173/auth/callback"],
                logout_urls=["http://localhost:5173/"],
            ),
            prevent_user_existence_errors=True,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.hours(12),
        )
        self.user_pool.add_domain(
            "Domain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{cfg.resource_name('rasad')}-{self.account}"
            ),
        )

        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.client.user_pool_client_id)
