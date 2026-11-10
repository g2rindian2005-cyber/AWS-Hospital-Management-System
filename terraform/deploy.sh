#!/usr/bin/env bash
# One-command deploy: init, then apply with no prompts.
# The dependency layer zip and any missing secrets are handled by the
# Terraform code itself (see build_layer.py and variables.tf defaults).
set -e
cd "$(dirname "$0")"
terraform init
terraform apply -auto-approve
