#!/usr/bin/env python3
"""Basira CDK app. Usage: cdk synth -c env=dev [-c alert_email=...] [-c github_owner=...]"""

from aws_cdk import App
from basira_infra.app_builder import build

app = App()
build(app, app.node.try_get_context("env") or "dev")
app.synth()
