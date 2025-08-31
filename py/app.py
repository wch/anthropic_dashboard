from shiny import App, Inputs, Outputs, Session, ui, render, reactive
from shinyreact import page_bare, render_object
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"

# Global cache for API responses
_api_cache = {}


def cache_key(*args, **kwargs):
    """Generate cache key from function arguments"""
    key_parts = list(args) + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return "|".join(str(p) for p in key_parts)


def cached_api_call(cache_duration_seconds=300):
    """Decorator to cache API responses for specified duration (default 5 minutes)"""

    def decorator(func):
        def wrapper(*args, **kwargs):
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

        return wrapper

    return decorator


# Check API key availability and warn user
if not ANTHROPIC_API_KEY:
    print("⚠️  Warning: ANTHROPIC_ADMIN_KEY not found in environment variables.")
    print("   Dashboard will show demo data instead of live API data.")
    print("   Add your Anthropic Admin API key to .env file to see real data.")
else:
    print("✓ Anthropic API key found. Dashboard will fetch live data.")


@cached_api_call(cache_duration_seconds=120)  # Cache usage reports for 2 minutes
def fetch_anthropic_usage_report(
    starting_at,
    ending_at=None,
    bucket_width="1d",
    limit=31,
    workspace_id=None,
    api_key_id=None,
):
    """Fetch usage report from Anthropic API"""
    if not ANTHROPIC_API_KEY:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/usage_report/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    params = {
        "starting_at": starting_at,
        "bucket_width": bucket_width,
        "limit": limit,
        "group_by[]": ["model", "service_tier", "workspace_id", "api_key_id"],
    }

    if ending_at:
        params["ending_at"] = ending_at

    if workspace_id and workspace_id != "all":
        params["workspace_id"] = workspace_id

    if api_key_id and api_key_id != "all":
        params["api_key_id"] = api_key_id

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching usage report: {e}")
        return None


@cached_api_call(cache_duration_seconds=120)  # Cache cost reports for 2 minutes
def fetch_anthropic_cost_report(
    starting_at, ending_at=None, limit=31, workspace_id=None, api_key_id=None
):
    """Fetch cost report from Anthropic API"""
    if not ANTHROPIC_API_KEY:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/cost_report"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    params = {
        "starting_at": starting_at,
        "limit": limit,
        "group_by[]": ["description", "workspace_id", "api_key_id", "model"],
    }

    if ending_at:
        params["ending_at"] = ending_at

    if workspace_id and workspace_id != "all":
        params["workspace_id"] = workspace_id

    if api_key_id and api_key_id != "all":
        params["api_key_id"] = api_key_id

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cost report: {e}")
        return None


@cached_api_call(cache_duration_seconds=600)  # Cache workspaces for 10 minutes
def fetch_workspaces(*, limit=1000):
    """Fetch workspace metadata from Anthropic API, sorted by creation time (oldest first)"""
    if not ANTHROPIC_API_KEY:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/workspaces?limit={limit}"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
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
def fetch_api_keys(workspace_id=None, *, limit=1000):
    """Fetch API key metadata from Anthropic API, sorted by creation time (oldest first)"""
    if not ANTHROPIC_API_KEY:
        return None

    url = f"{ANTHROPIC_API_BASE}/v1/organizations/api_keys?limit={limit}"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    params = {}
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


def generate_demo_usage_data():
    """Generate demo usage data when API is unavailable"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    rows = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    service_tiers = ["standard", "batch"]
    workspaces = ["ws_123abc", "ws_456def", "ws_789ghi"]
    api_keys = [
        "sk-ant-api03-123",
        "sk-ant-api03-456",
        "sk-ant-api03-789",
        "sk-ant-api03-000",
    ]

    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for model in models:
            for tier in service_tiers:
                for workspace in workspaces:
                    # Each workspace has some API keys
                    workspace_api_keys = (
                        api_keys[:2]
                        if workspace == "ws_123abc"
                        else api_keys[1:3] if workspace == "ws_456def" else api_keys[2:]
                    )
                    for api_key in workspace_api_keys:
                        input_tokens = np.random.randint(1000, 10000)
                        output_tokens = np.random.randint(500, 3000)
                        rows.append(
                            {
                                "date": current_date,
                                "model": model,
                                "service_tier": tier,
                                "workspace_id": workspace,
                                "api_key_id": api_key,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "cache_creation_1h": np.random.randint(0, 100),
                                "cache_creation_5m": np.random.randint(0, 50),
                                "web_search_requests": np.random.randint(0, 10),
                            }
                        )

    return pd.DataFrame(rows)


def generate_demo_workspace_data():
    """Generate demo workspace metadata with timestamps, sorted by creation time (oldest first)"""
    from datetime import datetime, timedelta

    base_time = datetime.now()
    workspaces = [
        {
            "id": "ws_123abc",
            "name": "Development Team",
            "display_color": "#6C5BB9",
            "created_at": (base_time - timedelta(days=1)).isoformat() + "Z",
        },
        {
            "id": "ws_456def",
            "name": "Production Environment",
            "display_color": "#2E7D32",
            "created_at": (base_time - timedelta(days=7)).isoformat() + "Z",
        },
        {
            "id": "ws_789ghi",
            "name": "Research & Analytics",
            "display_color": "#F57C00",
            "created_at": (base_time - timedelta(days=3)).isoformat() + "Z",
        },
        {
            "id": "ws_oldformat",
            "name": "",
            "display_color": "#9E9E9E",
            "created_at": (base_time - timedelta(days=30)).isoformat() + "Z",
        },
        {
            "id": "default",
            "name": "Default",
            "display_color": "#757575",
            "created_at": (base_time - timedelta(days=365)).isoformat() + "Z",
        },
    ]

    # Sort by created_at (oldest first)
    return sorted(workspaces, key=lambda x: x["created_at"], reverse=False)


def generate_demo_api_key_data():
    """Generate demo API key metadata with timestamps, sorted by creation time (oldest first)"""
    from datetime import datetime, timedelta

    base_time = datetime.now()
    api_keys = [
        {
            "id": "sk-ant-api03-123",
            "name": "Development Key",
            "workspace_id": "ws_123abc",
            "partial_key_hint": "sk-ant-api03-123...abc",
            "created_at": (base_time - timedelta(hours=2)).isoformat() + "Z",
        },
        {
            "id": "sk-ant-api03-456",
            "name": "Production Key",
            "workspace_id": "ws_456def",
            "partial_key_hint": "sk-ant-api03-456...def",
            "created_at": (base_time - timedelta(days=2)).isoformat() + "Z",
        },
        {
            "id": "sk-ant-api03-789",
            "name": "Analytics Key",
            "workspace_id": "ws_789ghi",
            "partial_key_hint": "sk-ant-api03-789...ghi",
            "created_at": (base_time - timedelta(days=5)).isoformat() + "Z",
        },
        {
            "id": "sk-ant-api03-000",
            "name": "Backup Key",
            "workspace_id": "ws_123abc",
            "partial_key_hint": "sk-ant-api03-000...xyz",
            "created_at": (base_time - timedelta(days=1)).isoformat() + "Z",
        },
        {
            "id": "sk-ant-api03-legacy",
            "name": "",
            "workspace_id": "ws_oldformat",
            "partial_key_hint": "sk-ant-api03-legacy...old",
            "created_at": (base_time - timedelta(days=45)).isoformat() + "Z",
        },
        {
            "id": "sk-ant-api03-default",
            "name": "Default API Key",
            "workspace_id": "default",
            "partial_key_hint": "sk-ant-api03-default...xyz",
            "created_at": (base_time - timedelta(days=400)).isoformat() + "Z",
        },
    ]

    # Sort by created_at (oldest first)
    return sorted(api_keys, key=lambda x: x["created_at"], reverse=False)


def generate_demo_cost_data():
    """Generate demo cost data when API is unavailable"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    rows = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    descriptions = ["Input tokens", "Output tokens", "Cache creation"]
    workspaces = ["ws_123abc", "ws_456def", "ws_789ghi"]
    api_keys = [
        "sk-ant-api03-123",
        "sk-ant-api03-456",
        "sk-ant-api03-789",
        "sk-ant-api03-000",
    ]

    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for model in models:
            for desc in descriptions:
                for workspace in workspaces:
                    # Each workspace has some API keys
                    workspace_api_keys = (
                        api_keys[:2]
                        if workspace == "ws_123abc"
                        else api_keys[1:3] if workspace == "ws_456def" else api_keys[2:]
                    )
                    for api_key in workspace_api_keys:
                        amount = np.random.uniform(0.50, 15.00)
                        rows.append(
                            {
                                "date": current_date,
                                "description": desc,
                                "amount": amount,
                                "currency": "USD",
                                "model": model,
                                "workspace_id": workspace,
                                "api_key_id": api_key,
                                "service_tier": "standard",
                                "cost_type": "tokens",
                                "token_type": "input" if "Input" in desc else "output",
                            }
                        )

    return pd.DataFrame(rows)


def process_usage_data(usage_response):
    """Process usage response into pandas DataFrame"""
    if not usage_response or not usage_response.get("data"):
        return pd.DataFrame()

    rows = []
    try:
        for time_bucket in usage_response["data"]:
            date = time_bucket["starting_at"][:10]  # Extract date part

            for result in time_bucket["results"]:
                rows.append(
                    {
                        "date": date,
                        "model": result.get("model", "unknown"),
                        "service_tier": result.get("service_tier", "standard"),
                        "workspace_id": result.get("workspace_id", "unknown"),
                        "api_key_id": result.get("api_key_id", "unknown"),
                        "input_tokens": result.get("uncached_input_tokens", 0)
                        + result.get("cache_read_input_tokens", 0),
                        "output_tokens": result.get("output_tokens", 0),
                        "cache_creation_1h": result.get("cache_creation", {}).get(
                            "ephemeral_1h_input_tokens", 0
                        ),
                        "cache_creation_5m": result.get("cache_creation", {}).get(
                            "ephemeral_5m_input_tokens", 0
                        ),
                        "web_search_requests": result.get("server_tool_use", {}).get(
                            "web_search_requests", 0
                        ),
                    }
                )
    except (KeyError, TypeError) as e:
        print(f"Error processing usage data: {e}")
        return pd.DataFrame()

    return pd.DataFrame(rows)


def process_cost_data(cost_response):
    """Process cost response into pandas DataFrame"""
    if not cost_response or not cost_response.get("data"):
        return pd.DataFrame()

    rows = []
    try:
        for time_bucket in cost_response["data"]:
            date = time_bucket["starting_at"][:10]  # Extract date part

            for result in time_bucket["results"]:
                rows.append(
                    {
                        "date": date,
                        "description": result.get("description", "Unknown"),
                        "amount": float(result.get("amount", 0)),
                        "currency": result.get("currency", "USD"),
                        "model": result.get("model", "unknown"),
                        "workspace_id": result.get("workspace_id", "unknown"),
                        "api_key_id": result.get("api_key_id", "unknown"),
                        "service_tier": result.get("service_tier", "standard"),
                        "cost_type": result.get("cost_type", "tokens"),
                        "token_type": result.get("token_type", "unknown"),
                    }
                )
    except (KeyError, TypeError, ValueError) as e:
        print(f"Error processing cost data: {e}")
        return pd.DataFrame()

    return pd.DataFrame(rows)


# Generate default date range (last 7 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
default_start = start_date.strftime("%Y-%m-%dT00:00:00Z")
default_end = end_date.strftime("%Y-%m-%dT23:59:59Z")

app_ui = page_bare(
    ui.head_content(
        ui.tags.script(src="main.js", type="module"),
        ui.tags.link(href="main.css", rel="stylesheet"),
    ),
    ui.div(id="root"),
    title="Anthropic API Dashboard",
)


def server(input: Inputs, output: Outputs, session: Session):

    # === REACTIVE DATA FETCHING ===

    @reactive.calc
    def raw_usage_data():
        """Fetch raw usage data from API or demo source"""
        try:
            start_date = (
                input.date_start()
                if hasattr(input, "date_start") and input.date_start() is not None
                else default_start
            )
            end_date = (
                input.date_end()
                if hasattr(input, "date_end") and input.date_end() is not None
                else default_end
            )
            granularity = (
                input.filter_granularity()
                if hasattr(input, "filter_granularity")
                and input.filter_granularity() is not None
                else "1d"
            )
        except:
            # If input access fails, use default values
            start_date = default_start
            end_date = default_end
            granularity = "1d"

        print(
            f"Raw usage data - start: {start_date}, end: {end_date}, granularity: {granularity}, has_key: {bool(ANTHROPIC_API_KEY)}"
        )

        if not ANTHROPIC_API_KEY:
            # Return demo data when API key is not available
            print("Using demo usage data (no API key)")
            return generate_demo_usage_data()

        try:
            # Calculate appropriate limit based on granularity and date range
            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            days_diff = (end_dt - start_dt).days + 1

            # Calculate limit based on granularity
            if granularity == "1h":
                api_limit = min(days_diff * 24, 1000)  # Max 1000 for safety
            elif granularity == "1d":
                api_limit = min(days_diff, 365)  # Max 1 year
            elif granularity == "7d":
                api_limit = min((days_diff // 7) + 1, 52)  # Max 1 year in weeks
            elif granularity == "30d":
                api_limit = min((days_diff // 30) + 1, 12)  # Max 1 year in months
            else:
                api_limit = 31  # Default fallback

            print(
                f"Using API limit: {api_limit} for granularity: {granularity}, days: {days_diff}"
            )

            usage_response = fetch_anthropic_usage_report(
                start_date, end_date, bucket_width=granularity, limit=api_limit
            )
            df = process_usage_data(usage_response)

            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No usage data returned from API, using demo data")
                return generate_demo_usage_data()

            print(f"Returning real usage data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in raw_usage_data: {e}, using demo data")
            return generate_demo_usage_data()

    @reactive.calc
    def usage_data():
        """Apply filters to raw usage data"""
        df = raw_usage_data()
        if df.empty:
            return df

        try:
            workspace_filter = (
                input.filter_workspace_id()
                if hasattr(input, "filter_workspace_id")
                and input.filter_workspace_id() is not None
                else "all"
            )
            api_key_filter = (
                input.filter_api_key_id()
                if hasattr(input, "filter_api_key_id")
                and input.filter_api_key_id() is not None
                else "all"
            )
            model_filter = (
                input.filter_model()
                if hasattr(input, "filter_model") and input.filter_model() is not None
                else "all"
            )
        except:
            workspace_filter = "all"
            api_key_filter = "all"
            model_filter = "all"

        print(
            f"Applying filters - workspace: {workspace_filter}, api_key: {api_key_filter}, model: {model_filter}"
        )

        # Apply filters
        filtered_df = df.copy()

        if workspace_filter != "all":
            filtered_df = filtered_df[filtered_df["workspace_id"] == workspace_filter]

        if api_key_filter != "all":
            filtered_df = filtered_df[filtered_df["api_key_id"] == api_key_filter]

        if model_filter != "all":
            filtered_df = filtered_df[filtered_df["model"] == model_filter]

        print(f"Filtered usage data: {len(filtered_df)} rows (from {len(df)} original)")
        return filtered_df

    @reactive.calc
    def raw_cost_data():
        """Fetch raw cost data from API or demo source"""
        try:
            start_date = (
                input.date_start()
                if hasattr(input, "date_start") and input.date_start() is not None
                else default_start
            )
            end_date = (
                input.date_end()
                if hasattr(input, "date_end") and input.date_end() is not None
                else default_end
            )
        except:
            # If input access fails, use default dates
            start_date = default_start
            end_date = default_end

        print(
            f"Raw cost data - start: {start_date}, end: {end_date}, has_key: {bool(ANTHROPIC_API_KEY)}"
        )

        if not ANTHROPIC_API_KEY:
            # Return demo data when API key is not available
            print("Using demo cost data (no API key)")
            return generate_demo_cost_data()

        try:
            # Calculate appropriate limit for cost data based on date range
            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            days_diff = (end_dt - start_dt).days + 1

            # For cost data, use a reasonable limit based on date range
            cost_limit = min(
                days_diff * 10, 1000
            )  # Assume up to 10 cost entries per day, max 1000

            print(f"Using cost API limit: {cost_limit} for {days_diff} days")

            cost_response = fetch_anthropic_cost_report(
                start_date, end_date, limit=cost_limit
            )
            df = process_cost_data(cost_response)

            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No cost data returned from API, using demo data")
                return generate_demo_cost_data()

            print(f"Returning real cost data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in raw_cost_data: {e}, using demo data")
            return generate_demo_cost_data()

    @reactive.calc
    def cost_data():
        """Apply filters to raw cost data"""
        df = raw_cost_data()
        if df.empty:
            return df

        try:
            workspace_filter = (
                input.filter_workspace_id()
                if hasattr(input, "filter_workspace_id")
                and input.filter_workspace_id() is not None
                else "all"
            )
            api_key_filter = (
                input.filter_api_key_id()
                if hasattr(input, "filter_api_key_id")
                and input.filter_api_key_id() is not None
                else "all"
            )
            model_filter = (
                input.filter_model()
                if hasattr(input, "filter_model") and input.filter_model() is not None
                else "all"
            )
        except:
            workspace_filter = "all"
            api_key_filter = "all"
            model_filter = "all"

        print(
            f"Applying cost filters - workspace: {workspace_filter}, api_key: {api_key_filter}, model: {model_filter}"
        )

        # Apply filters
        filtered_df = df.copy()

        if workspace_filter != "all":
            filtered_df = filtered_df[filtered_df["workspace_id"] == workspace_filter]

        if api_key_filter != "all":
            filtered_df = filtered_df[filtered_df["api_key_id"] == api_key_filter]

        if model_filter != "all":
            filtered_df = filtered_df[filtered_df["model"] == model_filter]

        print(f"Filtered cost data: {len(filtered_df)} rows (from {len(df)} original)")
        return filtered_df

    # === CACHED METADATA ===

    @reactive.calc
    def workspaces_metadata():
        """Cache workspace metadata from API"""
        if not ANTHROPIC_API_KEY:
            return generate_demo_workspace_data()

        try:
            workspaces_response = fetch_workspaces()
            if workspaces_response and workspaces_response.get("data"):
                return workspaces_response["data"]
        except Exception as e:
            print(f"Error in workspaces_metadata: {e}")

        return generate_demo_workspace_data()

    @reactive.calc
    def api_keys_metadata():
        """Cache API keys metadata from API (filtered by workspace if needed)"""
        try:
            workspace_filter = (
                input.filter_workspace_id()
                if hasattr(input, "filter_workspace_id")
                and input.filter_workspace_id() is not None
                else "all"
            )
        except:
            workspace_filter = "all"

        if not ANTHROPIC_API_KEY:
            demo_keys = generate_demo_api_key_data()
            if workspace_filter != "all":
                return [
                    k for k in demo_keys if k.get("workspace_id") == workspace_filter
                ]
            return demo_keys

        try:
            api_keys_response = fetch_api_keys(
                workspace_filter if workspace_filter != "all" else None
            )
            if api_keys_response and api_keys_response.get("data"):
                return api_keys_response["data"]
        except Exception as e:
            print(f"Error in api_keys_metadata: {e}")

        # Fallback to demo data filtered by workspace
        demo_keys = generate_demo_api_key_data()
        if workspace_filter != "all":
            return [k for k in demo_keys if k.get("workspace_id") == workspace_filter]
        return demo_keys

    # === FILTER OPTIONS ===

    @render_object()
    def available_workspaces():
        """Get available workspaces with names and IDs, sorted by creation time"""
        df = raw_usage_data()
        if df.empty:
            return []

        workspace_ids = df["workspace_id"].unique().tolist()
        workspace_ids = [w for w in workspace_ids if w and w != "unknown"]

        # Use cached metadata instead of making fresh API calls
        workspaces = workspaces_metadata()
        workspace_data = []

        for ws in workspaces:
            if ws["id"] in workspace_ids:
                name = ws.get("name", "").strip()
                if not name:
                    # Generate readable name for empty names
                    name = f"Workspace ({ws['id'][-6:]}...)"
                    print(
                        f"Warning: Empty name for workspace {ws['id']}, using fallback: {name}"
                    )
                workspace_data.append({"id": ws["id"], "name": name})

        print(f"Returning workspace data from cache: {workspace_data}")
        return workspace_data

    @render_object()
    def available_api_keys():
        """Get available API keys with names and IDs, filtered by selected workspace, sorted by creation time"""
        df = raw_usage_data()
        if df.empty:
            return []

        try:
            workspace_filter = (
                input.filter_workspace_id()
                if hasattr(input, "filter_workspace_id")
                and input.filter_workspace_id() is not None
                else "all"
            )
        except:
            workspace_filter = "all"

        # Filter by workspace if one is selected
        if workspace_filter != "all":
            df = df[df["workspace_id"] == workspace_filter]

        api_key_ids = df["api_key_id"].unique().tolist()
        api_key_ids = [k for k in api_key_ids if k and k != "unknown"]

        # Use cached metadata instead of making fresh API calls
        api_keys = api_keys_metadata()
        api_key_data = []

        for key in api_keys:
            if key["id"] in api_key_ids:
                name = key.get("name", "").strip()
                if not name:
                    # Generate readable name for empty names
                    key_hint = key.get("partial_key_hint", key["id"])
                    name = f"API Key ({key_hint[-6:]}...)"
                    print(
                        f"Warning: Empty name for API key {key['id']}, using fallback: {name}"
                    )
                api_key_data.append({"id": key["id"], "name": name})

        print(f"Returning API key data from cache: {api_key_data}")
        return api_key_data

    @render_object()
    def available_models():
        """Get available models from the data"""
        df = raw_usage_data()
        if df.empty:
            return []

        models = df["model"].unique().tolist()
        # Sort models, handling potential None values
        models = [m for m in models if m and m != "unknown"]
        models.sort()
        return models

    # === API STATUS ===

    @render_object()
    def api_status():
        """API connection status and info"""
        if not ANTHROPIC_API_KEY:
            return {
                "status": "demo",
                "message": "ANTHROPIC_ADMIN_KEY not found. Add your API key to .env file for live data.",
                "last_update": datetime.now().isoformat(),
            }

        # Check API status based on whether we have usage data (no extra API call needed)
        try:
            df = raw_usage_data()
            if not df.empty and len(df) > 0:
                return {
                    "status": "connected",
                    "message": "Connected to Anthropic API. Showing live data.",
                    "last_update": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "demo",
                    "message": "Using demo data. API may be rate-limited or returning empty results.",
                    "last_update": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"API connection failed: {str(e)}",
                "last_update": datetime.now().isoformat(),
            }

    # === KPI STATS ===

    @render.text
    def total_tokens():
        df = usage_data()
        if df.empty:
            return "0"
        total = df["input_tokens"].sum() + df["output_tokens"].sum()
        return str(int(total))

    @render.text
    def total_cost():
        df = cost_data()
        if df.empty:
            return "$0.00"
        total = df["amount"].sum()
        return f"${total:.2f}"

    @render.text
    def active_models():
        df = usage_data()
        if df.empty:
            return "0"
        return str(df["model"].nunique())

    @render.text
    def api_calls():
        df = usage_data()
        if df.empty:
            return "0"
        # Estimate API calls (this is approximate)
        return str(len(df))

    # === CHART DATA ===

    @render_object()
    def token_usage_chart_data():
        """Daily token usage over time"""
        df = usage_data()
        print(
            f"Token usage chart data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty token usage data")
            return {"date": [], "input_tokens": [], "output_tokens": []}

        daily_usage = (
            df.groupby("date")
            .agg({"input_tokens": "sum", "output_tokens": "sum"})
            .reset_index()
        )

        result = daily_usage.to_dict(orient="list")
        print(f"Token usage result: {result}")
        return result

    @render_object()
    def cost_by_model_chart_data():
        """Cost breakdown by model"""
        df = cost_data()
        print(
            f"Cost by model chart data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty cost by model data")
            return {"model": [], "cost": []}

        model_costs = df.groupby("model")["amount"].sum().reset_index()
        model_costs.columns = ["model", "cost"]

        result = model_costs.to_dict(orient="list")
        print(f"Cost by model result: {result}")
        return result

    @render_object()
    def service_tier_chart_data():
        """Usage by service tier"""
        df = usage_data()
        print(
            f"Service tier chart data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty service tier data")
            return {"service_tier": [], "tokens": []}

        tier_usage = (
            df.groupby("service_tier")
            .agg({"input_tokens": "sum", "output_tokens": "sum"})
            .reset_index()
        )

        tier_usage["total_tokens"] = (
            tier_usage["input_tokens"] + tier_usage["output_tokens"]
        )
        result = tier_usage[["service_tier", "total_tokens"]].copy()
        result.columns = ["service_tier", "tokens"]

        chart_result = result.to_dict(orient="list")
        print(f"Service tier result: {chart_result}")
        return chart_result

    # === DATA TABLE ===

    @render_object()
    def usage_table_data():
        """Detailed usage table data"""
        df = usage_data()
        if df.empty:
            return {"date": [], "model": [], "input_tokens": [], "output_tokens": []}

        # Group by date and model for cleaner display
        table_data = (
            df.groupby(["date", "model"])
            .agg(
                {"input_tokens": "sum", "output_tokens": "sum", "service_tier": "first"}
            )
            .reset_index()
        )

        return table_data.to_dict(orient="list")

    @render_object()
    def cost_table_data():
        """Detailed cost table data"""
        df = cost_data()
        if df.empty:
            return {"date": [], "description": [], "amount": [], "model": []}

        # Group by date and description
        table_data = (
            df.groupby(["date", "description", "model"])
            .agg({"amount": "sum"})
            .reset_index()
        )

        return table_data.to_dict(orient="list")

    # === LEGACY SUPPORT (for existing components) ===

    @render.text
    def processed_text():
        text = input.user_text() if input.user_text() is not None else ""
        if text == "":
            return ""
        return "".join(reversed(text.upper()))

    @render.text
    def text_length():
        text = input.user_text() if input.user_text() is not None else ""
        return len(text)

    @render.text
    @reactive.event(input.button_trigger)
    def button_response():
        now = datetime.now()
        return f"Refreshed at: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    @render.plot()
    def plot1():
        """Token usage visualization"""
        df = usage_data()

        fig, ax = plt.subplots(figsize=(10, 6))

        if df.empty:
            ax.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
        else:
            daily_usage = df.groupby("date").agg(
                {"input_tokens": "sum", "output_tokens": "sum"}
            )

            dates = pd.to_datetime(daily_usage.index)
            ax.plot(
                dates, daily_usage["input_tokens"], label="Input Tokens", marker="o"
            )
            ax.plot(
                dates, daily_usage["output_tokens"], label="Output Tokens", marker="s"
            )

            ax.set_xlabel("Date")
            ax.set_ylabel("Token Count")
            ax.set_title("Token Usage Over Time")
            ax.legend()
            ax.grid(True, alpha=0.3)

        return fig


app = App(app_ui, server, static_assets=str(Path(__file__).parent / "www"))
