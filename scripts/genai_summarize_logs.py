import json
import os
import urllib.error
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")


def read_file(path, max_chars=16000):
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
            "temperature": 0.1
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
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to connect to local Ollama service: {exc}"
        ) from exc

    output = result.get("response", "").strip()

    if not output:
        raise RuntimeError("Local AI returned an empty response.")

    return output


def main():
    context = read_file("poc-context.txt")
    test_logs = read_file("workflow-logs.txt")
    terraform_logs = read_file("terraform-plan.log")

    prompt = f"""
You are an AI-powered DevOps failure diagnosis assistant
running inside a GitHub Actions CI/CD pipeline.

Your job is NOT simply to repeat the GitHub Actions errors.

You must analyze the available pipeline evidence and identify:

1. What failed
2. The most likely root cause
3. Evidence supporting the diagnosis
4. Impact of the problem
5. The recommended remediation
6. The exact file or configuration that should be changed
7. Verification steps after the fix

IMPORTANT RULES:

- Use ONLY the supplied pipeline context and logs.
- Do not invent AWS resources, errors, files, or configuration.
- If evidence is insufficient, explicitly say so.
- Clearly distinguish confirmed facts from likely causes.
- Do not claim that a deployment occurred unless the logs prove it.
- Do not suggest automatically modifying production resources.
- Recommendations must be safe and practical.
- Prefer specific fixes over generic advice.
- Keep the response concise enough for a CI/CD artifact.
- This is a proof-of-concept, so prioritize useful actionable analysis.

PIPELINE CONTEXT
================
{context}

TEST LOG
========
{test_logs}

TERRAFORM LOG
=============
{terraform_logs}


Generate Markdown using EXACTLY these sections:

# AI Failure Diagnosis & Remediation

## Overall Assessment

Give a short assessment of the pipeline.

State whether it appears:

- Successful
- Failed
- Partially successful
- Blocked/skipped

## Failure Detection

Identify the failed, blocked, or skipped stages.

If everything succeeded, explicitly say that no pipeline failure was detected.

## Root Cause

Identify the most likely root cause.

If the evidence does not prove a root cause, say:

"Root cause could not be conclusively determined from the available logs."

Do not invent one.

## Evidence

List the specific evidence from the supplied context or logs
that supports your diagnosis.

## Impact

Explain what the problem could prevent or affect.

Keep this practical and concise.

## Recommended Fix

Give the recommended remediation.

Where possible, identify:

- File name
- Configuration/resource
- What should change

Show a small code/configuration example when the logs provide
enough information to do so.

## Verification Steps

Provide concrete commands or checks that should be performed
after applying the fix.

## Preventive Recommendation

Give one or two practical recommendations that could reduce
the likelihood of the same problem happening again.

## AI Confidence

Classify confidence as:

- High
- Medium
- Low

Briefly explain why.

"""


    output = call_local_ai(prompt)

    Path("ai-log-summary.md").write_text(output)

    print("AI failure diagnosis generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()