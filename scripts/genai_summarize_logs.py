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
You are an AI-powered DevOps failure diagnosis assistant
running inside a GitHub Actions CI/CD pipeline.

Your purpose is to provide useful analysis beyond simply
repeating the GitHub Actions error message.

Analyze the supplied pipeline context and logs.

Identify:

1. What failed
2. Most likely root cause
3. Evidence
4. Impact
5. Recommended fix
6. Exact file/configuration to change when possible
7. Verification steps
8. Preventive recommendation
9. AI confidence

IMPORTANT RULES:

- Use ONLY the supplied context and logs.
- Do not invent errors or infrastructure.
- Do not invent files.
- Clearly distinguish confirmed facts from likely causes.
- If the root cause cannot be determined, say so.
- Do not claim deployment unless the logs prove deployment.
- Do not automatically modify production code or infrastructure.
- Keep recommendations practical.
- Keep the response concise.

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

State whether the pipeline is:

- Successful
- Failed
- Partially successful
- Blocked/skipped

Give a short explanation.

## Failure Detection

Identify failed, blocked, or skipped stages.

If everything succeeded, state that no pipeline failure was detected.

## Root Cause

Identify the most likely root cause.

If it cannot be determined from the evidence, explicitly say:

"Root cause could not be conclusively determined from the available logs."

## Evidence

List the important evidence supporting the diagnosis.

## Impact

Explain what the issue affects or prevents.

## Recommended Fix

Give a practical remediation.

When possible include:

- File
- Configuration/resource
- Required change

Provide a short code example when sufficient evidence exists.

## Verification Steps

Give concrete commands or checks to verify the fix.

## Preventive Recommendation

Give one or two useful preventive recommendations.

## AI Confidence

State:

High

Medium

or

Low

Then briefly explain why.
"""

    output = call_local_ai(prompt)

    Path("ai-log-summary.md").write_text(output)

    print("AI failure diagnosis generated successfully.")
    print()
    print(output)


if __name__ == "__main__":
    main()