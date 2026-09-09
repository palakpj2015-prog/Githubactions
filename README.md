# GitHub Actions CI/CD with GenAI — POC

Personal-account proof of concept for **RTB C16: GitHub Actions CI/CD (Basic) with GenAI**.

The POC demonstrates a complete CI/CD workflow using GitHub Actions, AWS, Docker, Amazon ECR, Terraform, security scanning, and a **free local GenAI model**.

The GenAI component uses **Ollama + Qwen2.5 0.5B** instead of a paid external AI API.

---

## Architecture

```text
Developer
    |
    | git push
    v
GitHub
    |
    +----------------------+
    |                      |
    v                      v
   CI                     CD
    |                      |
    |                      +--> Terraform Plan
    |                      |
    |                      +--> Docker Build
    |                      |
    |                      +--> Amazon ECR
    |                      |
    |                      +--> Ollama + Qwen2.5
    |                               |
    |                               v
    |                       AI Failure Diagnosis
    |                               |
    |                               +--> Root Cause
    |                               +--> Evidence
    |                               +--> Impact
    |                               +--> Recommended Fix
    |                               +--> Verification Steps
    |
    +--> pytest
    +--> Semgrep
    +--> Terraform validate
    +--> tfsec