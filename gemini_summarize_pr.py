import os
from github import Github


def main():
    # Get GitHub token and repository details from environment variables
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("GITHUB_EVENT_NUMBER")
    token = os.getenv("GITHUB_TOKEN")

    bot_username = os.getenv("GITHUB_ACTOR")

    # Create a GitHub client

    g = Github(token)
    repo = g.get_repo(repo)

    # Construct the comment content
    pr = repo.get_pull(int(pr_number))
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
