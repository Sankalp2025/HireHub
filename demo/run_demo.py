#!/usr/bin/env python3
"""Run HireHub's real auth and resume-to-job analysis flow from the terminal."""

from __future__ import annotations

import argparse
import os
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 90
DEMO_EMAIL = os.getenv("HIREHUB_DEMO_EMAIL", "jordan.lee.demo@example.com")
# Fictional, deterministic local credential for repeatable register-or-login behavior.
DEMO_PASSWORD = os.getenv("HIREHUB_DEMO_PASSWORD", "HireHubDemo2026!")
DEMO_NAME = "Jordan Lee (Fictional Demo)"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class DemoError(RuntimeError):
    """Raised when the demo cannot safely continue."""


def _as_decimal(value: Any, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise DemoError(f"{label} must be numeric; received {value!r}") from exc
    if not number.is_finite():
        raise DemoError(f"{label} must be finite; received {value!r}")
    return number


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DemoError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DemoError(f"{label} must be a list")
    return value


def _response_json(response: httpx.Response, action: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise DemoError(f"{action} returned non-JSON data (HTTP {response.status_code})") from exc
    return _require_mapping(payload, f"{action} response")


def _error_message(response: httpx.Response, action: str) -> str:
    payload = _response_json(response, action)
    error = payload.get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    return f"HTTP {response.status_code}"


def wait_for_api(client: httpx.Client, timeout_seconds: int) -> None:
    """Wait until the API responds and confirms that PostgreSQL is connected."""
    deadline = time.monotonic() + timeout_seconds
    last_problem = "API has not responded yet"

    while time.monotonic() < deadline:
        try:
            response = client.get("/api/v1/health")
            if response.status_code == 200:
                payload = _response_json(response, "Health check")
                data = payload.get("data")
                db_status = data.get("db") if isinstance(data, dict) else None
                if db_status == "connected":
                    return
                last_problem = f"health reported database={db_status}"
            else:
                last_problem = f"health returned HTTP {response.status_code}"
        except (httpx.HTTPError, DemoError) as exc:
            last_problem = str(exc)
        time.sleep(1.5)

    raise DemoError(
        f"HireHub was not ready after {timeout_seconds}s. Last check: {last_problem}"
    )


def _login(client: httpx.Client) -> httpx.Response:
    return client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )


def authenticate(client: httpx.Client) -> str:
    """Reuse the fictional local account, creating it only on the first run."""
    login_response = _login(client)
    if login_response.status_code == 401:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "full_name": DEMO_NAME,
            },
        )
        if register_response.status_code not in {201, 400}:
            raise DemoError(
                "Registration failed: "
                + _error_message(register_response, "Registration")
            )
        login_response = _login(client)

    if login_response.status_code != 200:
        raise DemoError("Login failed: " + _error_message(login_response, "Login"))

    payload = _response_json(login_response, "Login")
    data = _require_mapping(payload.get("data"), "Login data")
    access_token = data.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise DemoError("Login response did not include an access token")
    return access_token


def submit_analysis(client: httpx.Client, access_token: str) -> dict[str, Any]:
    resume_text = (FIXTURES_DIR / "resume.txt").read_text(encoding="utf-8").strip()
    jd_text = (FIXTURES_DIR / "job_description.txt").read_text(encoding="utf-8").strip()
    response = client.post(
        "/api/v1/analyses",
        json={"resume_text": resume_text, "jd_text": jd_text},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if response.status_code != 201:
        raise DemoError("Analysis failed: " + _error_message(response, "Analysis"))
    return _response_json(response, "Analysis")


def validate_analysis_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the public response contract and the fixture's useful score range."""
    if payload.get("error") is not None:
        raise DemoError("Analysis response unexpectedly included an error")
    data = _require_mapping(payload.get("data"), "Analysis data")

    required_fields = {
        "id",
        "match_score",
        "missing_skills",
        "suggestions",
        "keyword_overlap",
        "analyzed_at",
    }
    missing_fields = sorted(required_fields - data.keys())
    if missing_fields:
        raise DemoError("Analysis data is missing: " + ", ".join(missing_fields))

    score = _as_decimal(data["match_score"], "Final score")
    if not Decimal("0") <= score <= Decimal("100"):
        raise DemoError(f"Final score {score} is outside the API's 0-100 range")

    overlap = _require_mapping(data["keyword_overlap"], "Keyword overlap")
    for field in (
        "matched",
        "missing",
        "keyword_score",
        "cosine_similarity_score",
        "score_weights",
        "matched_by_category",
        "category_breakdown",
    ):
        if field not in overlap:
            raise DemoError(f"Keyword overlap is missing {field}")

    matched = _require_list(overlap["matched"], "Matched terms")
    missing = _require_list(overlap["missing"], "Missing terms")
    suggestions = _require_list(data["suggestions"], "Suggestions")
    if not matched or not missing or not suggestions:
        raise DemoError("Demo requires matched terms, missing terms, and suggestions")

    keyword_score = _as_decimal(overlap["keyword_score"], "Keyword score")
    cosine_score = _as_decimal(overlap["cosine_similarity_score"], "Cosine score")
    weights = _require_mapping(overlap["score_weights"], "Score weights")
    keyword_weight = _as_decimal(weights.get("keyword_score"), "Keyword weight")
    cosine_weight = _as_decimal(weights.get("cosine_similarity_score"), "Cosine weight")

    for label, component in (
        ("Keyword score", keyword_score),
        ("Cosine score", cosine_score),
    ):
        if not Decimal("0") <= component <= Decimal("100"):
            raise DemoError(f"{label} is outside 0-100")
    if abs(keyword_weight + cosine_weight - Decimal("1")) > Decimal("0.001"):
        raise DemoError("Score weights must add up to 1")

    expected_score = keyword_score * keyword_weight + cosine_score * cosine_weight
    if abs(score - expected_score) > Decimal("0.02"):
        raise DemoError(
            f"Final score {score} does not match weighted components {expected_score:.2f}"
        )

    categories = _require_mapping(overlap["category_breakdown"], "Category breakdown")
    if not categories:
        raise DemoError("Category breakdown must not be empty")
    for category, values in categories.items():
        category_data = _require_mapping(values, f"Category {category}")
        if not {"matched", "missing", "total", "score"} <= category_data.keys():
            raise DemoError(f"Category {category} has an incomplete breakdown")

    matched_by_category = _require_mapping(
        overlap["matched_by_category"], "Matched terms by category"
    )
    if not matched_by_category:
        raise DemoError("Matched terms by category must not be empty")

    return data


def _score_style(score: Decimal) -> str:
    if score >= Decimal("70"):
        return "bold green"
    if score >= Decimal("45"):
        return "bold yellow"
    return "bold red"


def _terms_panel(title: str, terms: list[str], style: str, limit: int = 14) -> Panel:
    visible_terms = terms[:limit]
    lines = [f"• {term}" for term in visible_terms]
    if len(terms) > limit:
        lines.append(f"… and {len(terms) - limit} more")
    body = Text("\n".join(lines), style=style)
    return Panel(body, title=title, border_style=style, expand=True)


def render_analysis(console: Console, data: dict[str, Any]) -> None:
    overlap = data["keyword_overlap"]
    weights = overlap["score_weights"]
    score = _as_decimal(data["match_score"], "Final score")
    keyword_score = _as_decimal(overlap["keyword_score"], "Keyword score")
    cosine_score = _as_decimal(overlap["cosine_similarity_score"], "Cosine score")
    keyword_weight = _as_decimal(weights["keyword_score"], "Keyword weight")
    cosine_weight = _as_decimal(weights["cosine_similarity_score"], "Cosine weight")

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]HIREHUB[/bold cyan]\n"
            "[white]Explainable resume–job alignment[/white]",
            border_style="cyan",
            padding=(1, 5),
        ),
        justify="center",
    )
    score_text = Text(f"{score:.2f} / 100", style=_score_style(score), justify="center")
    console.print(Panel(score_text, title="Final alignment score", border_style="cyan"))

    category_table = Table(title="Alignment by category", box=box.SIMPLE_HEAVY)
    category_table.add_column("Category", style="bold magenta")
    category_table.add_column("Matched", justify="right", style="green")
    category_table.add_column("Missing", justify="right", style="yellow")
    category_table.add_column("Total", justify="right")
    category_table.add_column("Coverage", justify="right", style="cyan")
    for category, values in sorted(overlap["category_breakdown"].items()):
        label = category.replace("_", " ").title()
        category_table.add_row(
            label,
            str(values["matched"]),
            str(values["missing"]),
            str(values["total"]),
            f"{_as_decimal(values['score'], f'{label} score'):.2f}%",
        )
    console.print(category_table)

    components = Table(title="Score basis and diagnostic", box=box.ROUNDED)
    components.add_column("Component", style="bold")
    components.add_column("Score", justify="right")
    components.add_column("Weight", justify="right")
    components.add_column("Role", style="cyan")
    components.add_row(
        "Category-weighted skill alignment",
        f"{keyword_score:.2f}",
        f"{keyword_weight:.0%}",
        "Authoritative score",
    )
    components.add_row(
        "TF-IDF lexical similarity",
        f"{cosine_score:.2f}",
        f"{cosine_weight:.0%}",
        "Diagnostic only",
    )
    console.print(components)

    matched_by_category = overlap["matched_by_category"]
    prioritized_matched = []
    for category in ("hard_skill", "domain_term"):
        for term in matched_by_category.get(category, []):
            if term not in prioritized_matched:
                prioritized_matched.append(term)
    if not prioritized_matched:
        prioritized_matched = overlap["matched"]

    missing_by_category = overlap.get("missing_by_category", {})
    prioritized_missing = []
    for category in ("hard_skill", "domain_term", "soft_skill"):
        for term in missing_by_category.get(category, []):
            if term not in prioritized_missing:
                prioritized_missing.append(term)
    if not prioritized_missing:
        prioritized_missing = data["missing_skills"]

    console.print(
        Columns(
            [
                _terms_panel("Matched skills", prioritized_matched, "green"),
                _terms_panel("Missing skills", prioritized_missing, "yellow"),
            ],
            equal=True,
            expand=True,
        )
    )

    suggestion_text = Text()
    for index, suggestion in enumerate(data["suggestions"], start=1):
        suggestion_text.append(f"{index}. ", style="bold cyan")
        suggestion_text.append(str(suggestion))
        suggestion_text.append("\n")
    console.print(
        Panel(
            suggestion_text,
            title="Actionable suggestions",
            border_style="blue",
        )
    )
    console.print(
        f"[dim]Analysis {data['id']} • Real FastAPI auth + PostgreSQL persistence[/dim]",
        justify="center",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("HIREHUB_API_URL", DEFAULT_BASE_URL),
        help="HireHub API base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Seconds to wait for API and database readiness",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    console = Console(force_terminal=True, width=100)

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=10) as client:
            with console.status("[cyan]Waiting for HireHub API and PostgreSQL..."):
                wait_for_api(client, args.wait_timeout)
            console.print("[green]✓[/green] API ready and database connected")

            with console.status("[cyan]Authenticating fictional demo account..."):
                access_token = authenticate(client)
            console.print("[green]✓[/green] Authenticated through the real JWT flow")

            with console.status("[cyan]Analyzing deterministic resume and job fixtures..."):
                payload = submit_analysis(client, access_token)
                data = validate_analysis_response(payload)
            console.print("[green]✓[/green] Response contract and score math validated")
            render_analysis(console, data)
    except (DemoError, httpx.HTTPError, OSError) as exc:
        console.print(
            Panel(str(exc), title="HireHub demo failed", border_style="red"),
            style="red",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
