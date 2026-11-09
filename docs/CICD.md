# GitHub Actions CI/CD

The workflow is defined in `.github/workflows/ci-cd.yml`.

## When it runs

| Event | Build & Test | Deploy to AWS |
|---|---:|---:|
| Pull request to `main` | Yes | No |
| Push to `main` | Yes | Yes |
| Manual run from `main` | Yes | Yes |

## Build & Test job

The CI job checks:

- Every frontend JavaScript file and inline HTML script with Node's syntax checker (`scripts/validate_frontend.py`).
- Every Lambda Python file with `compileall`.
- Imports for the patient, billing, disease and doctor Lambda handlers.
- The OTP auth Lambda with a small local smoke test.
- Terraform formatting and validation (`terraform init -backend=false`, then `terraform validate`).
- Build outputs: a production frontend with the real API URL inserted, five Lambda ZIP packages, and the shared Python dependency layer.

The complete build is uploaded as a workflow artifact named `hospital-build-<commit-sha>`.

## Deploy job

After all tests pass on `main`, the deploy job:

1. Downloads the tested build artifact.
2. Connects to AWS with GitHub Secrets.
3. Publishes a new Lambda dependency layer version.
4. Updates all five Lambda functions: patient, billing, disease, doctor and auth.
5. Syncs the built frontend to the S3 website bucket.
6. Optionally refreshes the EC2 Nginx copy when an SSH key is configured.
7. Runs live smoke tests against the S3 login page and the auth API.

## Required GitHub Secrets

Add these under **GitHub repository → Settings → Secrets and variables → Actions → Secrets**:

| Secret | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS access key used by the deploy job |
| `AWS_SECRET_ACCESS_KEY` | Matching AWS secret key |

Use a dedicated IAM user for GitHub Actions where possible. Do not commit AWS keys to the repository.

## Optional configuration

Repository variables can be added under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Default |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `PROJECT_NAME` | `hospital` |
| `API_BASE_URL` | Current production API URL |
| `FRONTEND_BUCKET` | `hospital-management-frontend-bucket` |
| `EC2_HOST` | `67.202.28.176` |
| `EC2_USER` | `ubuntu` |

Optional secret:

| Secret | Purpose |
|---|---|
| `EC2_SSH_KEY` | Full PEM private key for refreshing the EC2 Nginx copy |

Without `EC2_SSH_KEY`, the workflow still deploys Lambda and S3 successfully and simply skips the EC2 refresh step.

## Terraform note

The workflow validates Terraform but does **not** run `terraform apply`. The current Terraform state is not stored in GitHub, so an Actions runner cannot safely apply infrastructure changes against the existing AWS account yet. Application code deployment (Lambda + frontend) is automated; infrastructure changes should be applied from a machine or pipeline that has access to the real Terraform state/backend.

## Status

- 2026-11-09: AWS deployment secrets configured in GitHub. Pushes to `main` now run the full pipeline, including deployment.
