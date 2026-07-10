"""
LeetCode API client module.

Handles all communication with the LeetCode GraphQL API, including
fetching solved problems and retrieving submission details.
"""

import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console

from config import Config, LEETCODE_GRAPHQL_URL, LEETCODE_BASE_URL

console = Console()


# ──────────────────────────────────────────────────────────────
# GraphQL query templates
# ──────────────────────────────────────────────────────────────

# Fetch all solved problems with their metadata
QUERY_ALL_SOLVED = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      questionId: questionFrontendId
      title
      titleSlug
      difficulty
      topicTags {
        name
      }
      status
    }
  }
}
"""

# Fetch submission list for a specific problem
QUERY_SUBMISSIONS = """
query submissionList($questionSlug: String!, $offset: Int!, $limit: Int!) {
  questionSubmissionList(
    questionSlug: $questionSlug
    offset: $offset
    limit: $limit
    status: 10
  ) {
    lastKey
    hasNext
    submissions {
      id
      statusDisplay
      lang
      timestamp
    }
  }
}
"""

# Fetch the actual code of a submission
QUERY_SUBMISSION_DETAIL = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    code
    lang {
      name
      verboseName
    }
    statusDisplay
    timestamp
  }
}
"""


class LeetCodeAPI:
    """
    Client for the LeetCode GraphQL API.

    Provides methods to fetch solved problems, submission history,
    and solution source code with automatic retry and rate limiting.
    """

    # Delay between API requests to avoid rate limiting (seconds)
    REQUEST_DELAY: float = 0.5

    def __init__(self, config: Config) -> None:
        """
        Initialize the API client.

        Args:
            config: Application configuration with cookies and headers.
        """
        self._config = config
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create an HTTP session with retry logic.

        Returns:
            A configured requests.Session.
        """
        session = requests.Session()
        session.cookies.update(self._config.cookies)
        session.headers.update(self._config.headers)

        # Configure retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a GraphQL query against the LeetCode API.

        Args:
            query: The GraphQL query string.
            variables: Query variables.

        Returns:
            The 'data' field of the JSON response.

        Raises:
            requests.HTTPError: On non-2xx responses.
            ValueError: If the response contains GraphQL errors.
        """
        payload = {"query": query, "variables": variables}

        response = self._session.post(LEETCODE_GRAPHQL_URL, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if "errors" in result:
            raise ValueError(f"GraphQL errors: {result['errors']}")

        return result.get("data", {})

    def fetch_solved_problems(self) -> list[dict[str, Any]]:
        """
        Fetch all problems the user has solved (status == 'ac').

        Returns:
            List of problem dicts with keys: questionId, title,
            titleSlug, difficulty, topicTags, status.
        """
        all_problems: list[dict[str, Any]] = []
        skip = 0
        limit = 100  # LeetCode paginates at 100

        console.log("[cyan]Fetching solved problems from LeetCode...[/cyan]")

        while True:
            data = self._graphql(
                QUERY_ALL_SOLVED,
                {
                    "categorySlug": "",
                    "limit": limit,
                    "skip": skip,
                    "filters": {"status": "AC"},
                },
            )

            question_list = data.get("problemsetQuestionList", {})
            questions = question_list.get("questions", [])
            total = question_list.get("total", 0)

            if not questions:
                break

            all_problems.extend(questions)
            skip += limit

            console.log(
                f"  Fetched {len(all_problems)}/{total} problems..."
            )

            if skip >= total:
                break

            time.sleep(self.REQUEST_DELAY)

        console.log(
            f"[green]✓ Found {len(all_problems)} solved problems.[/green]"
        )
        return all_problems

    def fetch_latest_accepted_submission(
        self, title_slug: str
    ) -> Optional[dict[str, Any]]:
        """
        Fetch the most recent accepted submission for a problem.

        Args:
            title_slug: The problem's URL slug (e.g., "two-sum").

        Returns:
            A dict with keys {id, lang, timestamp} for the latest
            accepted submission, or None if not found.
        """
        try:
            data = self._graphql(
                QUERY_SUBMISSIONS,
                {
                    "questionSlug": title_slug,
                    "offset": 0,
                    "limit": 1,  # We only need the latest one
                },
            )

            submission_list = data.get("questionSubmissionList", {})
            submissions = submission_list.get("submissions", [])

            if not submissions:
                return None

            # Return the most recent accepted submission
            sub = submissions[0]
            return {
                "id": int(sub["id"]),
                "lang": sub["lang"],
                "timestamp": int(sub["timestamp"]),
            }
        except Exception as e:
            console.log(f"[yellow]⚠ Could not fetch submissions for '{title_slug}': {e}[/yellow]")
            return None

    def fetch_submission_code(self, submission_id: int) -> Optional[str]:
        """
        Fetch the source code of a specific submission.

        Args:
            submission_id: The numeric submission ID.

        Returns:
            The source code string, or None on failure.
        """
        try:
            data = self._graphql(
                QUERY_SUBMISSION_DETAIL,
                {"submissionId": submission_id},
            )

            detail = data.get("submissionDetails", {})
            return detail.get("code")
        except Exception as e:
            console.log(f"[yellow]⚠ Could not fetch code for submission {submission_id}: {e}[/yellow]")
            return None

    def throttle(self) -> None:
        """Sleep briefly to respect API rate limits."""
        time.sleep(self.REQUEST_DELAY)
