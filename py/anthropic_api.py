# pyright: strict
from __future__ import annotations

import requests
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, TypedDict, Literal
from functools import wraps

# API Configuration
ANTHROPIC_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


# Global cache for API responses
_api_cache: dict[str, tuple[Any, datetime]] = {}


def cache_key(*args: Any, **kwargs: Any) -> str:
    """Generate cache key from function arguments"""
    key_parts = list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return "|".join(str(p) for p in key_parts)


F = TypeVar("F", bound=Callable[..., Any])


# TypedDict definitions based on Anthropic API documentation


# Common types
class CacheCreation(TypedDict):
    ephemeral_1h_input_tokens: int
    ephemeral_5m_input_tokens: int


class ServerToolUse(TypedDict):
    web_search_requests: int


class CreatedBy(TypedDict):
    id: str
    type: str


# Usage Report types
class MessagesUsageReportItem(TypedDict):
    uncached_input_tokens: int
    cache_creation: CacheCreation
    cache_read_input_tokens: int
    output_tokens: int
    server_tool_use: ServerToolUse
    api_key_id: Optional[str]
    workspace_id: Optional[str]
    model: Optional[str]
    service_tier: Optional[Literal["standard", "batch", "priority"]]
    context_window: Optional[Literal["0-200k", "200k-1M"]]


class MessagesUsageReportTimeBucket(TypedDict):
    starting_at: str
    ending_at: str
    results: list[MessagesUsageReportItem]


class UsageReportResponse(TypedDict):
    data: list[MessagesUsageReportTimeBucket]
    has_more: bool
    next_page: Optional[str]


# Cost Report types
class CostReportItem(TypedDict):
    currency: str
    amount: str
    workspace_id: Optional[str]
    description: Optional[str]
    cost_type: Optional[Literal["tokens", "web_search", "code_execution"]]
    context_window: Optional[Literal["0-200k", "200k-1M"]]
    model: Optional[str]
    service_tier: Optional[Literal["standard", "batch"]]
    token_type: Optional[
        Literal[
            "uncached_input_tokens",
            "output_tokens",
            "cache_read_input_tokens",
            "cache_creation.ephemeral_1h_input_tokens",
            "cache_creation.ephemeral_5m_input_tokens",
        ]
    ]


class CostReportTimeBucket(TypedDict):
    starting_at: str
    ending_at: str
    results: list[CostReportItem]


class CostReportResponse(TypedDict):
    data: list[CostReportTimeBucket]
    has_more: bool
    next_page: Optional[str]


# Workspace types
class Workspace(TypedDict):
    archived_at: Optional[str]
    created_at: str
    display_color: str
    id: str
    name: str
    type: Literal["workspace"]


class WorkspacesResponse(TypedDict):
    data: list[Workspace]
    first_id: Optional[str]
    has_more: bool
    last_id: Optional[str]


# API Key types
class ApiKey(TypedDict):
    created_at: str
    created_by: CreatedBy
    id: str
    name: str
    partial_key_hint: Optional[str]
    status: Literal["active", "inactive", "archived"]
    type: Literal["api_key"]
    workspace_id: Optional[str]


class ApiKeysResponse(TypedDict):
    data: list[ApiKey]
    first_id: Optional[str]
    has_more: bool
    last_id: Optional[str]


def cached_api_call(cache_duration_seconds: int = 300) -> Callable[[F], F]:
    """Decorator to cache API responses for specified duration (default 5 minutes)"""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            current_time = datetime.now()

            # Check if we have a valid cached response
            if key in _api_cache:
                cached_data, cached_time = _api_cache[key]
                if (current_time - cached_time).seconds < cache_duration_seconds:
                    print(
                        f"Using cached {func.__name__} (age: {(current_time - cached_time).seconds}s)"
                    )
                    return cached_data

            # Make fresh API call and cache result
            result = func(*args, **kwargs)
            _api_cache[key] = (result, current_time)
            return result

        return wrapper  # type: ignore

    return decorator


@cached_api_call(cache_duration_seconds=120)  # Cache usage reports for 2 minutes
def fetch_anthropic_usage_report(
    api_key: str,
    starting_at: str,
    ending_at: Optional[str] = None,
    bucket_width: str = "1d",
    limit: int = 31,
    workspace_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
) -> UsageReportResponse | None:
    """Fetch usage report from Anthropic API

    Limit constraints based on bucket_width:
    - "1d": Default 7 days, maximum 31 days
    - "1h": Default 24 hours, maximum 168 hours (7 days)
    - "1m": Default 60 minutes, maximum 1440 minutes (24 hours)
    """
    if not api_key:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/usage_report/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    # Apply bucket_width-specific limit constraints
    if bucket_width == "1h":
        api_limit = min(limit, 168)  # Max 168 hours (7 days)
    elif bucket_width == "1m":
        api_limit = min(limit, 1440)  # Max 1440 minutes (24 hours)
    elif bucket_width == "1d":
        api_limit = min(limit, 31)  # Max 31 days
    else:
        api_limit = min(limit, 31)  # Default fallback

    params = {
        "starting_at": starting_at,
        "bucket_width": bucket_width,
        "limit": api_limit,
        "group_by[]": ["model", "service_tier", "workspace_id", "api_key_id"],
    }

    # Only add ending_at if it's significantly after starting_at
    # API requires ending_at to be after starting_at (not just same day)
    if ending_at:
        from datetime import datetime, timedelta

        try:
            start_dt = datetime.fromisoformat(starting_at.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(ending_at.replace("Z", "+00:00"))
            # Only add ending_at if it's at least 1 day after starting_at
            if (end_dt - start_dt).total_seconds() > 86400:  # 24 hours
                params["ending_at"] = ending_at
        except:
            # If date parsing fails, don't add ending_at
            pass

    # Add filtering parameters using the correct array format
    if workspace_id and workspace_id != "all":
        params["workspace_ids[]"] = [workspace_id]

    if api_key_id and api_key_id != "all":
        params["api_key_ids[]"] = [api_key_id]

    try:
        print(f"Calling usage report API with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching usage report: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_body = e.response.json()
                print(f"Error details: {error_body}")
            except:
                print(f"Error response body: {e.response.text[:500]}")
        return None


@cached_api_call(cache_duration_seconds=120)  # Cache cost reports for 2 minutes
def fetch_anthropic_cost_report(
    api_key: str,
    starting_at: str,
    ending_at: Optional[str] = None,
    limit: int = 31,
    workspace_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
) -> CostReportResponse | None:
    """Fetch cost report from Anthropic API

    Note: Cost reports only support group_by=["workspace_id", "description"]
    and bucket_width is always "1d" (daily). API key and model filtering
    is not supported by the cost report API.
    """
    if not api_key:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/cost_report"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    # Ensure limit doesn't exceed API maximum of 31
    api_limit = min(limit, 31)

    params = {
        "starting_at": starting_at,
        "limit": api_limit,
        "bucket_width": "1d",  # Cost reports only support daily granularity
        "group_by[]": ["description", "workspace_id"],  # Only these are supported
    }

    # Only add ending_at if it's significantly after starting_at
    # API requires ending_at to be after starting_at (not just same day)
    if ending_at:
        from datetime import datetime

        try:
            start_dt = datetime.fromisoformat(starting_at.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(ending_at.replace("Z", "+00:00"))
            # Only add ending_at if it's at least 1 day after starting_at
            if (end_dt - start_dt).total_seconds() > 86400:  # 24 hours
                params["ending_at"] = ending_at
        except:
            # If date parsing fails, don't add ending_at
            pass

    # Note: workspace_id and api_key_id filtering in the URL parameters
    # is not supported by the cost report API. Filtering must be done
    # client-side after receiving the data.

    try:
        print(f"Calling cost report API with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cost report: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_body = e.response.json()
                print(f"Error details: {error_body}")
            except:
                print(f"Error response body: {e.response.text[:500]}")
        return None


@cached_api_call(cache_duration_seconds=600)  # Cache workspaces for 10 minutes
def fetch_workspaces(api_key: str, *, limit: int = 1000) -> WorkspacesResponse | None:
    """Fetch workspace metadata from Anthropic API, sorted by creation time (oldest first)"""
    if not api_key:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/workspaces?limit={limit}"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Sort workspaces by created_at (oldest first)
        if "data" in data and data["data"]:
            data["data"] = sorted(
                data["data"], key=lambda x: x.get("created_at", ""), reverse=False
            )

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching workspaces: {e}")
        return None


@cached_api_call(cache_duration_seconds=600)  # Cache API keys for 10 minutes
def fetch_api_keys(
    api_key: str, workspace_id: Optional[str] = None, *, limit: int = 1000
) -> ApiKeysResponse | None:
    """Fetch API key metadata from Anthropic API, sorted by creation time (oldest first)"""
    if not api_key:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/api_keys?limit={limit}"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    params: dict[str, str] = {}
    if workspace_id and workspace_id != "all":
        params["workspace_id"] = workspace_id

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Sort API keys by created_at (oldest first)
        if "data" in data and data["data"]:
            data["data"] = sorted(
                data["data"], key=lambda x: x.get("created_at", ""), reverse=False
            )

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching API keys: {e}")
        return None
