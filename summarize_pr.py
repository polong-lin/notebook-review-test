import os
import requests
from ghapi.all import GhApi
import gzip
import base64

from typing import Tuple
import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel


def _get_pr_content(api: GhApi, pr_number: str) -> str:
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

    return pull_request_content


def _process_code_base(
    pull_request_content: str, model_id: str, task_prompt: str, post_prompt: str = ""
):
    model = GenerativeModel(
        model_id,
        system_instruction=[
            "You are an expert software engineer.",
        ],
        generation_config=GenerationConfig(
            max_output_tokens=8192,
        ),
    )
    prompt = [
        "The following is the content of a GitHub Pull Request for a repository focused on Generative AI with Google Cloud. This content includes the Pull Request title, Pull Request description, a list of all of the files changed with the file name, the code diff and the raw file content.",
        task_prompt,
        "Pull Request Content:",
        pull_request_content,
        post_prompt,
    ]

    print("---Prompt---\n", prompt)
    response = model.generate_content(prompt)
    print("---Gemini Response---\n", response)
    return response.text


def analyze_pr(api: GhApi, pr_number: str, model_id: str) -> Tuple:
    pull_request_content = _get_pr_content(api, pr_number)

    summarize_output = _process_code_base(
        pull_request_content,
        model_id,
        "Your task is to summarize the Pull Request in Markdown format.",
        post_prompt="Summary:",
    )

    analysis_output = _process_code_base(
        pull_request_content,
        model_id,
        task_prompt="Your task is to analyze each code file line by line, then output any bugs you find and improvements that can be made to the code quality for readability and maintainability.",
        post_prompt="Analysis:",
    )

    latest_commit = api.pulls.list_commits(pr_number)[-1]["sha"]

    # Create a comment on the PR
    comment_content = f"""# Pull Request Summary from Gemini ✨\n{summarize_output}\n\n# Code Analysis from Gemini ✨\n{analysis_output}\n Generated at Commit: `{latest_commit}`"""

    # Post the summary as a comment
    api.issues.create_comment(pr_number, comment_content)

    return summarize_output, analysis_output


def convert_to_sarif(model_id: str, analysis_content: str) -> str:
    model = GenerativeModel(
        model_id,
        system_instruction=[
            "You are an expert software engineer.",
        ],
    )

    generation_config = GenerationConfig(
        response_mime_type="application/json",
        max_output_tokens=8192,
    )

    sarif_schema = requests.get(
        "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/123e95847b13fbdd4cbe2120fa5e33355d4a042b/Schemata/sarif-schema-2.1.0.json"
    ).text

    prompt = [
        "The following is analysis of a GitHub Pull Request.",
        "Your task is to convert this into SARIF (Static Analysis Results Interchange Format) format.",
        "This is the SARIF schema:",
        sarif_schema,
        "Analysis Content:",
        analysis_content,
        "SARIF:"
        """{"$schema": "https://json-schema.org/draft/2020-12/schema#", "version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Gemini", "shortDescription": {"text": "A large language model capable of generating text, translating languages, writing different kinds of creative content, and answering your questions in an informative way."}, "fullDescription": {"text": "Gemini Pro is a large language model (LLM) developed by Google AI. It is trained on a massive dataset of text and code, and can be used for a wide variety of tasks, including text generation, translation, writing different kinds of creative content, and answering your questions in an informative way."}}}, "results":""",
    ]

    print("---Prompt---\n", prompt)
    response = model.generate_content(prompt, generation_config=generation_config)
    print("---Gemini Response---\n", response)

    return response.text


def upload_sarif(api: GhApi, pr_number: str, sarif_text: str):
    encoded_data = base64.b64encode(gzip.compress(sarif_text.encode("utf-8"))).decode(
        "utf-8"
    )

    commits = api.pulls.list_commits(pr_number)

    sarif_response = api.code_scanning.upload_sarif(
        commit_sha=commits[-1]["sha"],
        sarif=encoded_data,
        ref=f"refs/pull/{pr_number}/head",
    )

    return sarif_response


if __name__ == "__main__":
    vertexai.init()

    # Get GitHub token (store securely in Cloud Build secrets)
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

    # Get PR information from environment variables (set by Cloud Build)
    OWNER = os.environ["REPO_FULL_NAME"].split("/")[0]
    REPO = os.environ["REPO_NAME"]
    PR_NUMBER = os.environ["PR_NUMBER"]

    MODEL_ID = os.environ.get("MODEL_ID", "gemini-1.5-flash-preview-0514")

    USE_SARIF = False
    # Initialize GitHub API client
    API = GhApi(owner=OWNER, repo=REPO, token=GITHUB_TOKEN)

    summarize_output, analysis_output = analyze_pr(API, PR_NUMBER, MODEL_ID)

    if USE_SARIF:
        # Create line by line analysis in SARIF format
        # https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning
        sarif_text = convert_to_sarif(MODEL_ID, analysis_output)
        sarif_response = upload_sarif(API, PR_NUMBER, sarif_text)
