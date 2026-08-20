import os
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-5.6-luna"


def read_file(path, max_chars=12000):
    file_path = Path(path)

    if not file_path.exists():
        return f"{path} was not found."

    content = file_path.read_text(errors="ignore")

    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Log truncated]"

    return content


def main():
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)

    context = read_file("poc-context.txt")
    test_logs = read_file("workflow-logs.txt")
    terraform_logs = read_file("terraform-plan.log")

    prompt = f"""
You are a DevOps AI assistant integrated into GitHub Actions.

Analyze the CI/CD pipeline logs below and produce a concise,
human-readable pipeline analysis.

PIPELINE CONTEXT:
{context}

TEST LOG:
{test_logs}

TERRAFORM LOG:
{terraform_logs}

Generate Markdown with exactly these sections:

# AI Pipeline Log Summary

## Pipeline Status
Explain whether the pipeline stages appear successful or failed.

## Test Analysis
Summarize the application test results.

## Terraform Analysis
Summarize the Terraform validation and plan results.

## Issues Detected
List important errors, warnings, or potential problems.
If there are none, explicitly state that no significant issues were detected.

## Recommendations
Provide practical recommendations only when appropriate.

Rules:
- Base the analysis only on the supplied context and logs.
- Do not invent information.
- Keep the summary concise.
- Highlight actionable problems.
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )

    output = response.output_text.strip()

    Path("ai-log-summary.md").write_text(output)

    print("AI log summary generated successfully.")


if __name__ == "__main__":
    main()