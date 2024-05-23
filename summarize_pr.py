import os
import requests
from ghapi.all import GhApi

import vertexai
from vertexai.generative_models import GenerativeModel


def summarize_pr(
    github_token: str, owner: str, repo: str, pr_number: str, model_id: str
):
    # Initialize GitHub API client
    api = GhApi(owner=owner, repo=repo, token=github_token)

    # Fetch PR details
    pr = api.pulls.get(pr_number)
    files = api.pulls.list_files(pr_number)

    pull_request_content = ""

    # Extract and print title and description
    pull_request_content += f" Title: {pr.title}\n"
    pull_request_content += f"Pull Request Description: {pr.body}\n"

    # Fetch and print code diff
    pull_request_content += "\n--- Files Changed ---\n"
    for file in files:
        pull_request_content += f"File name: {file.filename}\n\n"

        patch = getattr(file, "patch", None)
        if patch:
            if patch.startswith("Binary files"):
                pull_request_content += "Binary file - Skipping Code Diff\n\n"
                continue
            pull_request_content += f"Code Diff:\n{patch}\n\n"

        raw_url = getattr(file, "raw_url", None)
        if raw_url:
            response = requests.get(raw_url)
            if response.status_code == 200:
                pull_request_content += (
                    f"Raw File Content:\n```\n{response.text}\n```\n\n"
                )

    model = GenerativeModel(
        model_id,
        system_instruction=[
            "You are an expert software engineer.",
        ],
    )

    prompt = [
        "The following is the content of a GitHub Pull Request for a repository focused on Generative AI with Google Cloud. This content includes the Pull Request title, Pull Request description, a list of all of the files changed with the file name, the code diff and the raw file content. Your task is to output a summary of the Pull Request in Markdown format.",
        "Content:",
        pull_request_content,
        "Summary:",
    ]

    print("---Prompt---\n", prompt)
    response = model.generate_content(prompt)
    print("---Gemini Response---\n", response)

    # Post the summary as a comment
    api.issues.create_comment(
        pr_number, f"## Pull Request Summary from Gemini\n {response.text}"
    )


if __name__ == "__main__":
    vertexai.init()

    # Get GitHub token (store securely in Cloud Build secrets)
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

    # Get PR information from environment variables (set by Cloud Build)
    OWNER = os.environ["REPO_FULL_NAME"].split("/")[0]
    REPO = os.environ["REPO_NAME"]
    PR_NUMBER = os.environ["PR_NUMBER"]

    MODEL_ID = os.environ.get("MODEL_ID", "gemini-1.5-flash-preview-0514")

    print(GITHUB_TOKEN)
    summarize_pr(GITHUB_TOKEN, OWNER, REPO, PR_NUMBER, MODEL_ID)
