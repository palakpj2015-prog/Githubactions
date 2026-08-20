# GitHub Actions CI/CD with GenAI — POC

Personal-account proof of concept for **RTB C16: GitHub Actions CI/CD (Basic) with GenAI**.

Built for **personal GitHub + personal AWS** — no dependency on work repos or infrastructure.

## Stack

- **GitHub Actions** — hosted runners, modular jobs
- **AWS** — ECR (Docker), S3 + ECR via Terraform
- **Terraform** — IaC validate/plan in CI/CD
- **GenAI** — OpenAI API for release notes and log summaries
- **Security** — Semgrep (SAST), tfsec (Terraform)

## Project layout

```
gh-actions-genai-poc/
├── app/                    # Minimal Flask app + pytest
├── terraform/              # ECR repo + S3 artifacts bucket
├── scripts/                # GenAI helpers (OpenAI API)
├── .github/workflows/
│   ├── ci.yml              # PR/push: test, Semgrep, terraform validate
│   └── cd-genai.yml        # main: ECR push, terraform plan, AI artifacts
└── docs/AWS_OIDC_SETUP.md  # One-time AWS + GitHub OIDC guide
```

## Quick start

### 1. Local smoke test

```powershell
cd C:\Users\pjain5\Downloads\gh-actions-genai-poc
cd app
pip install -r requirements.txt
pytest -v
```

### 2. Bootstrap AWS (local)

```powershell
cd terraform
terraform init
terraform plan
terraform apply
```

This creates:
- ECR repository: `genai-poc-app`
- S3 bucket: `genai-poc-artifacts-<account-id>`

### 3. Configure GitHub OIDC + secrets

Follow [docs/AWS_OIDC_SETUP.md](docs/AWS_OIDC_SETUP.md), then add these **GitHub Secrets**:

| Secret | Required | Purpose |
|--------|----------|---------|
| `OPENAI_API_KEY` | Yes | GenAI release notes + log summary |
| `AWS_ROLE_ARN` | Yes | OIDC role for ECR + Terraform |
| `SLACK_WEBHOOK_URL` | No | Optional failure notifications |

Optional repo **variable**: set `SLACK_ENABLED` = `true` to enable Slack notify job.

### 4. Push to GitHub

```powershell
cd C:\Users\pjain5\Downloads\gh-actions-genai-poc
git init
git add .
git commit -m "Initial GenAI CI/CD POC scaffold"
git branch -M main
git remote add origin https://github.com/<your-user>/gh-actions-genai-poc.git
git push -u origin main
```

### 5. Run the pipeline

- Push to `main` triggers **CD - Docker ECR Terraform GenAI**
- Or run manually: Actions → CD workflow → Run workflow

Download artifacts from the run:
- `ai-release-notes.md`
- `ai-log-summary.md`

## Course milestones mapped

| Milestone | Implementation |
|-----------|----------------|
| M1 — Workflows & secrets | Modular jobs, triggers, GitHub Secrets, OIDC |
| M2 — Build & test | pytest + Docker build/push to ECR |
| M3 — IaC | Terraform fmt/validate/plan |
| M4 — Security & notify | Semgrep, tfsec, optional Slack |
| M5 — GenAI | OpenAI release notes + log summary artifacts |

## Demo script (5–10 min)

1. Walk through workflow YAML — no hard-coded credentials
2. Open a PR → CI runs tests + Semgrep + terraform validate
3. Merge to `main` → CD pushes Docker image to ECR, runs terraform plan
4. Download AI artifacts and review outputs (course requires human review)
5. Show ECR image in AWS Console

## Notes

- GenAI outputs are for **review** before publishing externally
- Terraform `apply` is intentionally run locally first; CI runs `plan` only
- ECR repository name in workflow (`genai-poc-app`) matches Terraform resource name
