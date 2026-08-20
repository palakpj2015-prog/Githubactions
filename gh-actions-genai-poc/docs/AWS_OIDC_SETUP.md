# AWS OIDC Setup for GitHub Actions

One-time setup to let GitHub Actions assume an IAM role in your **personal AWS account** without storing long-lived access keys.

Replace placeholders:
- `<AWS_ACCOUNT_ID>` — your 12-digit account ID
- `<GITHUB_USER>` — your GitHub username
- `<REPO_NAME>` — e.g. `gh-actions-genai-poc`

## Step 1 — Create OIDC identity provider

In IAM → Identity providers → Add provider:

| Field | Value |
|-------|-------|
| Provider type | OpenID Connect |
| Provider URL | `https://token.actions.githubusercontent.com` |
| Audience | `sts.amazonaws.com` |

Or via CLI:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faad879272427c64739a8fe0c
```

## Step 2 — Create IAM policy

Save as `github-actions-poc-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAuth",
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages"
      ],
      "Resource": "arn:aws:ecr:us-east-1:<AWS_ACCOUNT_ID>:repository/genai-poc-app"
    },
    {
      "Sid": "TerraformPlanRead",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DeleteRepository",
        "ecr:TagResource",
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:ListBucket",
        "s3:GetBucketTagging",
        "s3:PutBucketTagging",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:ecr:us-east-1:<AWS_ACCOUNT_ID>:repository/genai-poc-app",
        "arn:aws:s3:::genai-poc-artifacts-<AWS_ACCOUNT_ID>",
        "arn:aws:s3:::genai-poc-artifacts-<AWS_ACCOUNT_ID>/*"
      ]
    },
    {
      "Sid": "ReadCallerIdentity",
      "Effect": "Allow",
      "Action": "sts:GetCallerIdentity",
      "Resource": "*"
    }
  ]
}
```

Create the policy:

```bash
aws iam create-policy \
  --policy-name GitHubActionsGenAIPocPolicy \
  --policy-document file://github-actions-poc-policy.json
```

Note the policy ARN (e.g. `arn:aws:iam::<AWS_ACCOUNT_ID>:policy/GitHubActionsGenAIPocPolicy`).

## Step 3 — Create IAM role with trust policy

Save as `github-oidc-trust.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<GITHUB_USER>/<REPO_NAME>:*"
        }
      }
    }
  ]
}
```

Create role and attach policy:

```bash
aws iam create-role \
  --role-name GitHubActionsGenAIPocRole \
  --assume-role-policy-document file://github-oidc-trust.json

aws iam attach-role-policy \
  --role-name GitHubActionsGenAIPocRole \
  --policy-arn arn:aws:iam::<AWS_ACCOUNT_ID>:policy/GitHubActionsGenAIPocPolicy
```

## Step 4 — Add GitHub Secret

In your GitHub repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|--------|-------|
| `AWS_ROLE_ARN` | `arn:aws:iam::<AWS_ACCOUNT_ID>:role/GitHubActionsGenAIPocRole` |
| `OPENAI_API_KEY` | Your OpenAI API key |

## Step 5 — Verify

1. Push to `main`
2. Check the **Configure AWS credentials (OIDC)** step in Actions
3. Confirm Docker image appears in ECR: `genai-poc-app`

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | Check trust policy `sub` matches `repo:<user>/<repo>:*` |
| `AccessDenied` on ECR push | Verify ECR repo exists (`terraform apply`) and policy resource ARN is correct |
| OIDC provider already exists | Skip Step 1; use existing provider ARN in trust policy |

## Alternative: access keys (not recommended)

If you skip OIDC, store `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as secrets and replace the `configure-aws-credentials` step with:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

Remove `permissions: id-token: write` if using access keys.
