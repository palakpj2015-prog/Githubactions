import json
import os
import urllib.error
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")


def read_file(path, max_chars=8000):
    file_path = Path(path)

    if not file_path.exists():
        return f"{path} was not found."

    content = file_path.read_text(errors="ignore")

    if len(content) > max_chars:
        content = content[:max_chars] + "\n[Log truncated]"

    return content


def call_local_ai(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 500
        }
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to connect to local Ollama service: {exc}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            "Ollama took longer than 5 minutes to generate the AI diagnosis."
        ) from exc

    output = result.get("response", "").strip()

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    return output


def main():
    context = read_file("poc-context.txt", 6000)
    test_logs = read_file("workflow-logs.txt", 7000)
    terraform_logs = read_file("terraform-plan.log", 7000)

    prompt = f"""
You are an AI-powered DevOps CI/CD failure diagnosis assistant.

Your job is to analyze the actual pipeline evidence and provide
a useful diagnosis and remediation recommendation.

IMPORTANT:
Do NOT simply repeat the error message.

You must reason about:

EXPECTED VALUE
versus
ACTUAL VALUE

when the logs provide both.

For example, if a test reports:

Expected: 500
Actual: 200

and the application endpoint is normally expected to return 200,
then the likely problem may be an INCORRECT TEST EXPECTATION,
not an application failure.

Do not automatically recommend changing working application code
just to make a test pass.

Use the surrounding test name, endpoint, expected value, actual
value, and application behavior to determine which side is more
likely incorrect.

For assertion failures:

- Identify the expected value.
- Identify the actual value.
- Explain the difference.
- Determine whether the test or application is more likely wrong.
- Recommend the smallest appropriate fix.
- Never change the expected value merely because the test failed.
- If the evidence is insufficient, explicitly say so.

IMPORTANT PIPELINE RULE:

The GenAI job runs with `if: always()` and therefore may run even
when earlier jobs fail.

Do not say that GenAI cannot run because a previous job failed.

Also distinguish:

FAILED
from
PARTIALLY SUCCESSFUL
from
BLOCKED/SKIPPED.

If a required job failed, the overall pipeline should normally be
described as FAILED even if the GenAI analysis itself succeeds.

Use ONLY the supplied context and logs.

Do not invent:

- errors
- files
- AWS resources
- deployments
- configuration
- commands not supported by the evidence

Do not claim Terraform apply or deployment occurred unless the
logs explicitly prove it.

PIPELINE CONTEXT
================
{context}

TEST LOG
========
{test_logs}

TERRAFORM LOG
=============
{terraform_logs}


Return Markdown using EXACTLY these sections:

# AI Failure Diagnosis & Remediation

## Overall Assessment

State:

- Overall pipeline state
- Failed jobs/stages
- Whether GenAI analysis completed

Explain the overall result briefly.

## Failure Detection

List the failed, skipped, and successful stages.

For test failures, identify the exact test when available.

## Root Cause

Explain the most likely root cause.

For assertion failures explicitly compare:

- Expected value
- Actual value

Then determine whether the test expectation or application behavior
is more likely incorrect.

If the evidence does not support a conclusion, say:

"Root cause could not be conclusively determined from the available logs."

## Evidence

List the exact evidence supporting the diagnosis.

Prefer concrete values, filenames, test names, resources,
or error messages from the logs.

## Impact

Explain what the failure prevents or affects.

Do not claim that unrelated stages were prevented if they actually
ran or if the logs do not prove that.

## Recommended Fix

Give the smallest and safest appropriate fix.

Include:

- File
- Function/resource/configuration
- Current problematic value
- Recommended value

If changing application code is not appropriate, say so.

If the correct fix is to change a test expectation, explicitly say:

"The test expectation should be corrected."

If the correct fix is to change application behavior, explicitly say:

"The application behavior should be corrected."

## Verification Steps

Give concrete commands to verify the recommended fix.

For Python test failures, prefer:

pytest app/ -v

For a specific test, you may also provide:

pytest app/test_main.py::test_health -v

For Terraform failures, use appropriate terraform commands
supported by the logs.

## Preventive Recommendation

Give one or two practical recommendations.

Examples:

- Keep tests aligned with the intended API contract.
- Add explicit API contract tests.
- Validate Terraform configuration during CI.
- Pin infrastructure configuration where appropriate.

Only recommend something relevant to the detected problem.

## AI Confidence

Choose:

High
Medium
Low

Explain why in one sentence.
"""

    output = call_local_ai(prompt)

    Path("ai-log-summary.md").write_text(output)

    print("AI failure diagnosis generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()