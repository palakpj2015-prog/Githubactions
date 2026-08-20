from pathlib import Path


def main():
    context_file = Path("poc-context.txt")

    if context_file.exists():
        context = context_file.read_text()
    else:
        context = "Pipeline context was not available."

    lines = context.splitlines()

    values = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()

    repository = values.get("Repository", "Unknown")
    commit = values.get("Commit", "Unknown")
    branch = values.get("Branch", "Unknown")
    test_result = values.get("Test result", "unknown")
    terraform_result = values.get("Terraform result", "unknown")
    docker_result = values.get("Docker result", "unknown")

    status = "SUCCESS"

    if "failure" in {
        test_result.lower(),
        terraform_result.lower(),
        docker_result.lower(),
    }:
        status = "FAILED"

    notes = f"""# AI Release Notes

## Pipeline Status

**{status}**

## Repository

`{repository}`

## Branch

`{branch}`

## Commit

`{commit}`

## Pipeline Results

| Stage | Result |
|---|---|
| Application Tests | {test_result} |
| Terraform Plan | {terraform_result} |
| Docker / ECR | {docker_result} |

## Summary

This release was automatically analyzed from the GitHub Actions
pipeline context and execution results.

The pipeline completed with an overall status of **{status}**.

## Deployment Artifact

The Docker image is tagged using the Git commit SHA, providing
traceability between the source code and the ECR image.

"""

    Path("ai-release-notes.md").write_text(notes)

    print("AI release notes generated successfully.")


if __name__ == "__main__":
    main()
    