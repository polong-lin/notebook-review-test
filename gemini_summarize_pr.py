import os
import json
from github import Github


def main():
    # Get GitHub token and repository details
    repo_name = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    bot_username = os.getenv("GITHUB_ACTOR")

    # Load event data
    with open(event_path, "r") as f:
        event_data = json.load(f)

    # Determine the PR number based on the event
    if "pull_request" in event_data:
        pr_number = event_data["pull_request"]["number"]
    elif (
        "issue" in event_data and "pull_request" in event_data["issue"]
    ):  # For comment events on PRs
        pr_number = event_data["issue"]["number"]
    else:
        raise ValueError("Unable to determine pull request number from event data.")

    # Create a GitHub client and access the repository
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Construct the comment content
    comment_body = f"""
**Pull Request Details:**

* **Title:** {pr.title}
* **Description:** {pr.body}
* **Author:** {pr.user.login}
    """

    # Check for existing comments by the bot
    for comment in pr.get_issue_comments():
        if comment.user.login == bot_username:
            # Update the existing comment
            comment.edit(comment_body)
            return

    # If no existing comment is found, create a new one
    pr.create_issue_comment(comment_body)


if __name__ == "__main__":
    main()
