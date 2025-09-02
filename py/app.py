# pyright: strict
# pyright: reportUnusedFunction=false

from typing import TypedDict, Literal
from shiny import App, Inputs, Outputs, Session, ui, render, reactive
from shinyreact import page_bare, render_object
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from anthropic_api import (
    fetch_anthropic_usage_report,
    fetch_anthropic_cost_report,
    fetch_workspaces,
    fetch_api_keys,
    UsageReportResponse,
    CostReportResponse,
)
from demo_data import (
    generate_demo_usage_data,
    generate_demo_cost_data,
    generate_demo_workspace_data,
    generate_demo_api_key_data,
)
from data_types import CostDataRow


class UiWorkspaceData(TypedDict):
    id: str
    name: str


class UiApiKeyData(TypedDict):
    id: str
    name: str


class UiApiStatus(TypedDict):
    status: str
    message: str
    last_update: str


DataSource = Literal["api", "demo", "error"]


class DataWithSource(TypedDict):
    data: pd.DataFrame
    source: DataSource
    error_message: str | None


# Load environment variables
load_dotenv()

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_ADMIN_KEY")
ANTHROPIC_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


# Check API key availability and warn user
if not ANTHROPIC_API_KEY:
    print("⚠️  Warning: ANTHROPIC_ADMIN_KEY not found in environment variables.")
    print("   Dashboard will show demo data instead of live API data.")
    print("   Add your Anthropic Admin API key to .env file to see real data.")
else:
    print("✓ Anthropic API key found. Dashboard will fetch live data.")


def process_usage_data(
    usage_response: UsageReportResponse, granularity: str = "1d"
) -> pd.DataFrame:
    """Process usage response into pandas DataFrame"""
    if not usage_response or not usage_response.get("data"):
        return pd.DataFrame()

    rows = []
    try:
        for time_bucket in usage_response["data"]:
            # Preserve timestamp granularity based on the granularity setting
            starting_at = time_bucket["starting_at"]
            if granularity == "1m":
                # For per-minute, preserve date, hour, and minute (YYYY-MM-DD HH:MM:00)
                datetime_key = starting_at[:16] + ":00"
            elif granularity == "1h":
                # For hourly, preserve date and hour (YYYY-MM-DD HH:00)
                datetime_key = starting_at[:13] + ":00"
            elif granularity in ["1d", "7d", "30d"]:
                # For daily and longer periods, use date only
                datetime_key = starting_at[:10]
            else:
                # Fallback to date only
                datetime_key = starting_at[:10]

            for result in time_bucket["results"]:
                rows.append(
                    {
                        "date": datetime_key,
                        "model": result.get("model", "unknown"),
                        "service_tier": result.get("service_tier", "standard"),
                        "workspace_id": result.get("workspace_id") or "default",
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


def process_cost_data(
    cost_response: CostReportResponse, granularity: str = "1d"
) -> pd.DataFrame:
    """Process cost response into pandas DataFrame"""
    if not cost_response or not cost_response.get("data"):
        return pd.DataFrame()

    rows: list[CostDataRow] = []
    try:
        for time_bucket in cost_response["data"]:
            # Preserve timestamp granularity based on the granularity setting
            starting_at = time_bucket["starting_at"]
            if granularity == "1m":
                # For per-minute, preserve date, hour, and minute (YYYY-MM-DD HH:MM:00)
                datetime_key = starting_at[:16] + ":00"
            elif granularity == "1h":
                # For hourly, preserve date and hour (YYYY-MM-DD HH:00)
                datetime_key = starting_at[:13] + ":00"
            elif granularity in ["1d", "7d", "30d"]:
                # For daily and longer periods, use date only
                datetime_key = starting_at[:10]
            else:
                # Fallback to date only
                datetime_key = starting_at[:10]

            date = datetime_key

            for result in time_bucket["results"]:
                # Extract values with proper type handling
                # API returns amount in cents, convert to dollars
                amount_raw = result.get("amount", 0)
                try:
                    amount_cents = float(amount_raw)
                    amount = amount_cents / 100.0  # Convert cents to dollars
                except (ValueError, TypeError):
                    amount = 0.0

                row: CostDataRow = {
                    "date": date,
                    "description": str(result.get("description", "Unknown")),
                    "amount": amount,
                    "currency": str(result.get("currency", "USD")),
                    "model": str(result.get("model", "unknown")),
                    "workspace_id": str(result.get("workspace_id") or "default"),
                    "api_key_id": str(result.get("api_key_id", "unknown")),
                    "service_tier": str(result.get("service_tier", "standard")),
                    "cost_type": str(result.get("cost_type", "tokens")),
                    "token_type": str(result.get("token_type", "unknown")),
                }
                rows.append(row)
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
    def raw_usage_data() -> DataWithSource:
        """Fetch raw usage data from API or demo source based on user preference"""
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
            # Check if user has enabled demo mode
            use_demo_mode = (
                input.use_demo_mode()
                if hasattr(input, "use_demo_mode") and input.use_demo_mode() is not None
                else False
            )
        except:
            # If input access fails, use default values
            start_date = default_start
            end_date = default_end
            granularity = "1d"
            use_demo_mode = False

        print(
            f"Raw usage data - start: {start_date}, end: {end_date}, granularity: {granularity}, has_key: {bool(ANTHROPIC_API_KEY)}, demo_mode: {use_demo_mode}"
        )

        # If user explicitly enabled demo mode, use demo data
        if use_demo_mode:
            print("Using demo usage data (user enabled demo mode)")
            return {
                "data": generate_demo_usage_data(granularity),
                "source": "demo",
                "error_message": None,
            }

        # If no API key available and user hasn't enabled demo mode, return error
        if not ANTHROPIC_API_KEY:
            print("No API key available and demo mode disabled")
            return {
                "data": pd.DataFrame(),
                "source": "error",
                "error_message": "ANTHROPIC_ADMIN_KEY not found in environment variables. Enable demo mode to see sample data.",
            }

        try:
            # Calculate appropriate limit based on granularity and date range
            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            days_diff = (end_dt - start_dt).days + 1

            # Calculate limit based on granularity and API constraints
            warning_message = None
            if granularity == "1h":
                # API max: 168 hours (7 days)
                requested_hours = days_diff * 24
                api_limit = min(requested_hours, 168)
                if requested_hours > 168:
                    warning_message = f"Date range truncated: Requested {requested_hours} hours of data, but API maximum is 168 hours (7 days). Showing last 7 days only."
                    print(f"Warning: {warning_message}")
            elif granularity == "1m":
                # API max: 1440 minutes (24 hours)
                requested_minutes = days_diff * 24 * 60
                api_limit = min(requested_minutes, 1440)
                if requested_minutes > 1440:
                    warning_message = f"Date range truncated: Requested {requested_minutes} minutes of data, but API maximum is 1440 minutes (24 hours). Showing last 24 hours only."
                    print(f"Warning: {warning_message}")
            elif granularity == "1d":
                # API max: 31 days
                api_limit = min(days_diff, 31)
                if days_diff > 31:
                    warning_message = f"Date range truncated: Requested {days_diff} days of data, but API maximum is 31 days. Showing last 31 days only."
                    print(f"Warning: {warning_message}")
            elif granularity == "7d":
                # For weekly, still constrained by daily limit of 31
                api_limit = min((days_diff // 7) + 1, 31)
            elif granularity == "30d":
                # For monthly, still constrained by daily limit of 31
                api_limit = min((days_diff // 30) + 1, 31)
            else:
                api_limit = 31  # Default fallback

            # Send warning message to UI if limit was exceeded
            if warning_message:
                session.send_custom_message(
                    "warning", {"message": warning_message, "type": "warning"}
                )

            print(
                f"Calling Anthropic API with limit: {api_limit} for granularity: {granularity}, days: {days_diff}"
            )

            usage_response = fetch_anthropic_usage_report(
                ANTHROPIC_API_KEY,
                start_date,
                end_date,
                bucket_width=granularity,
                limit=api_limit,
            )
            df = process_usage_data(usage_response, granularity)

            # If API call succeeded but returned empty data, return error (no automatic fallback)
            if df.empty:
                print("API returned empty usage data")
                return {
                    "data": pd.DataFrame(),
                    "source": "error",
                    "error_message": "API returned no usage data for the selected date range. Try adjusting the date range or enable demo mode.",
                }

            print(f"Successfully retrieved real usage data with {len(df)} rows")
            return {"data": df, "source": "api", "error_message": None}
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling Anthropic API for usage data: {error_msg}")
            return {
                "data": pd.DataFrame(),
                "source": "error",
                "error_message": f"API call failed: {error_msg}. Enable demo mode to see sample data.",
            }

    @reactive.calc
    def usage_data() -> pd.DataFrame:
        """Apply filters to raw usage data"""
        data_with_source = raw_usage_data()
        df = data_with_source["data"]
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
    def raw_cost_data() -> DataWithSource:
        """Fetch raw cost data from API or demo source based on user preference"""
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
            # Check if user has enabled demo mode
            use_demo_mode = (
                input.use_demo_mode()
                if hasattr(input, "use_demo_mode") and input.use_demo_mode() is not None
                else False
            )
        except:
            # If input access fails, use default dates
            start_date = default_start
            end_date = default_end
            use_demo_mode = False

        # Get granularity for cost data consistency
        try:
            granularity = (
                input.filter_granularity()
                if hasattr(input, "filter_granularity")
                and input.filter_granularity() is not None
                else "1d"
            )
        except:
            granularity = "1d"

        print(
            f"Raw cost data - start: {start_date}, end: {end_date}, granularity: {granularity}, has_key: {bool(ANTHROPIC_API_KEY)}, demo_mode: {use_demo_mode}"
        )

        # If user explicitly enabled demo mode, use demo data
        if use_demo_mode:
            print("Using demo cost data (user enabled demo mode)")
            return {
                "data": generate_demo_cost_data(granularity),
                "source": "demo",
                "error_message": None,
            }

        # If no API key available and user hasn't enabled demo mode, return error
        if not ANTHROPIC_API_KEY:
            print("No API key available and demo mode disabled")
            return {
                "data": pd.DataFrame(),
                "source": "error",
                "error_message": "ANTHROPIC_ADMIN_KEY not found in environment variables. Enable demo mode to see sample data.",
            }

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

            print(
                f"Calling Anthropic API for cost data with limit: {cost_limit} for {days_diff} days"
            )

            cost_response = fetch_anthropic_cost_report(
                ANTHROPIC_API_KEY,
                start_date,
                end_date,
                limit=cost_limit,
                # Note: workspace_id and api_key_id filtering not supported by cost API
                # Will filter client-side in cost_data() function
            )
            df = process_cost_data(cost_response, granularity)

            # If API call succeeded but returned empty data, return error (no automatic fallback)
            if df.empty:
                print("API returned empty cost data")
                return {
                    "data": pd.DataFrame(),
                    "source": "error",
                    "error_message": "API returned no cost data for the selected date range. Try adjusting the date range or enable demo mode.",
                }

            print(f"Successfully retrieved real cost data with {len(df)} rows")
            return {"data": df, "source": "api", "error_message": None}
        except Exception as e:
            error_msg = str(e)
            print(f"Error calling Anthropic API for cost data: {error_msg}")
            return {
                "data": pd.DataFrame(),
                "source": "error",
                "error_message": f"API call failed: {error_msg}. Enable demo mode to see sample data.",
            }

    @reactive.calc
    def cost_data() -> pd.DataFrame:
        """Apply filters to raw cost data"""
        data_with_source = raw_cost_data()
        df = data_with_source["data"]
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
        """Cache workspace metadata from API based on user preference"""
        try:
            use_demo_mode = (
                input.use_demo_mode()
                if hasattr(input, "use_demo_mode") and input.use_demo_mode() is not None
                else False
            )
        except:
            use_demo_mode = False

        # If user enabled demo mode, use demo data
        if use_demo_mode:
            return generate_demo_workspace_data()

        # If no API key and demo mode disabled, return empty list
        if not ANTHROPIC_API_KEY:
            return []

        try:
            workspaces_response = fetch_workspaces(api_key=ANTHROPIC_API_KEY)
            if workspaces_response and workspaces_response.get("data"):
                return workspaces_response["data"]
        except Exception as e:
            print(f"Error in workspaces_metadata: {e}")

        return []  # Return empty list on error, no automatic fallback

    @reactive.calc
    def api_keys_metadata():
        """Cache API keys metadata from API (filtered by workspace if needed) based on user preference"""
        try:
            workspace_filter = (
                input.filter_workspace_id()
                if hasattr(input, "filter_workspace_id")
                and input.filter_workspace_id() is not None
                else "all"
            )
            use_demo_mode = (
                input.use_demo_mode()
                if hasattr(input, "use_demo_mode") and input.use_demo_mode() is not None
                else False
            )
        except:
            workspace_filter = "all"
            use_demo_mode = False

        # If user enabled demo mode, use demo data
        if use_demo_mode:
            demo_keys = generate_demo_api_key_data()
            if workspace_filter != "all":
                if workspace_filter == "default":
                    # For "default" workspace, return keys with null workspace_id
                    return [k for k in demo_keys if k.get("workspace_id") is None]
                else:
                    return [
                        k
                        for k in demo_keys
                        if k.get("workspace_id") == workspace_filter
                    ]
            return demo_keys

        # If no API key and demo mode disabled, return empty list
        if not ANTHROPIC_API_KEY:
            return []

        try:
            # For "default" workspace, we need to get all keys and filter client-side
            # because the API doesn't support filtering by null workspace_id
            api_keys_response = fetch_api_keys(
                ANTHROPIC_API_KEY,
                None if workspace_filter in ["all", "default"] else workspace_filter,
            )
            if api_keys_response and api_keys_response.get("data"):
                api_keys = api_keys_response["data"]
                if workspace_filter == "default":
                    # Filter to only API keys with null workspace_id
                    return [k for k in api_keys if k.get("workspace_id") is None]
                return api_keys
        except Exception as e:
            print(f"Error in api_keys_metadata: {e}")

        return []  # Return empty list on error, no automatic fallback

    # === FILTER OPTIONS ===

    @render_object
    def available_workspaces() -> list[UiWorkspaceData]:
        """Get available workspaces with names and IDs, sorted by creation time"""
        data_with_source = raw_usage_data()
        df = data_with_source["data"]
        if df.empty:
            return []

        workspace_ids = df["workspace_id"].unique().tolist()
        workspace_ids = [w for w in workspace_ids if w and w != "unknown"]

        # Use cached metadata instead of making fresh API calls
        workspaces = workspaces_metadata()
        workspace_data = []

        # Check if we have a "default" workspace (for API keys with null workspace_id)
        has_default_workspace = "default" in workspace_ids
        if has_default_workspace:
            workspace_data.append({"id": "default", "name": "Default"})
            workspace_ids.remove(
                "default"
            )  # Remove from list to avoid processing again

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

    @render_object
    def available_api_keys() -> list[UiApiKeyData]:
        """Get available API keys with names and IDs, filtered by selected workspace, sorted by creation time"""
        data_with_source = raw_usage_data()
        df = data_with_source["data"]
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

    @render_object
    def available_models() -> list[str]:
        """Get available models from the data"""
        data_with_source = raw_usage_data()
        df = data_with_source["data"]
        if df.empty:
            return []

        models = df["model"].unique().tolist()
        # Sort models, handling potential None values
        models = [m for m in models if m and m != "unknown"]
        models.sort()
        return models

    # === API STATUS ===

    @render_object
    def api_status() -> UiApiStatus:
        """API connection status and info"""
        if not ANTHROPIC_API_KEY:
            return {
                "status": "demo",
                "message": "ANTHROPIC_ADMIN_KEY not found. Add your API key to .env file for live data.",
                "last_update": datetime.now().isoformat(),
            }

        # Check API status based on data source from usage and cost data
        try:
            usage_data_info = raw_usage_data()
            cost_data_info = raw_cost_data()

            usage_source = usage_data_info["source"]
            cost_source = cost_data_info["source"]

            # Determine overall status based on both data sources
            if usage_source == "api" and cost_source == "api":
                return {
                    "status": "connected",
                    "message": "Connected to Anthropic API. Showing live usage and cost data.",
                    "last_update": datetime.now().isoformat(),
                }
            elif usage_source == "api" or cost_source == "api":
                # Mixed - some API data available
                api_types = []
                demo_types = []
                error_msgs = []

                if usage_source == "api":
                    api_types.append("usage")
                else:
                    demo_types.append("usage")
                    if usage_data_info["error_message"]:
                        error_msgs.append(f"Usage: {usage_data_info['error_message']}")

                if cost_source == "api":
                    api_types.append("cost")
                else:
                    demo_types.append("cost")
                    if cost_data_info["error_message"]:
                        error_msgs.append(f"Cost: {cost_data_info['error_message']}")

                message = f"Partially connected. Live {' and '.join(api_types)} data, demo {' and '.join(demo_types)} data."
                if error_msgs:
                    message += f" Issues: {'; '.join(error_msgs)}"

                return {
                    "status": "partial",
                    "message": message,
                    "last_update": datetime.now().isoformat(),
                }
            elif usage_source == "error" or cost_source == "error":
                # API calls failed
                error_msgs = []
                if usage_data_info["error_message"]:
                    error_msgs.append(f"Usage: {usage_data_info['error_message']}")
                if cost_data_info["error_message"]:
                    error_msgs.append(f"Cost: {cost_data_info['error_message']}")

                return {
                    "status": "error",
                    "message": f"API connection failed. Using demo data. Errors: {'; '.join(error_msgs)}",
                    "last_update": datetime.now().isoformat(),
                }
            else:
                # Both are demo (fallback cases)
                return {
                    "status": "demo",
                    "message": "Using demo data. API may be rate-limited or returning empty results.",
                    "last_update": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to determine API status: {str(e)}",
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

    # === FILTER STATES (for sharing between components) ===

    @render.text
    def current_granularity():
        """Return current granularity setting for chart formatting"""
        try:
            return input.filter_granularity() or "1d"
        except:
            return "1d"

    @render_object
    def current_filters():
        """Return current filter state for components to show warnings"""
        try:
            return {
                "workspace_id": input.filter_workspace_id() or "all",
                "api_key_id": input.filter_api_key_id() or "all",
                "model": input.filter_model() or "all",
                "granularity": input.filter_granularity() or "1d",
            }
        except:
            return {
                "workspace_id": "all",
                "api_key_id": "all",
                "model": "all",
                "granularity": "1d",
            }

    # === CHART DATA ===

    @render_object
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

    @render_object
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

    @render_object
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

    @render_object
    def workspace_cost_chart_data():
        """Cost breakdown by workspace"""
        df = cost_data()
        print(
            f"Workspace cost chart data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty workspace cost data")
            return {"workspace": [], "cost": []}

        try:
            # Group by workspace_id to get costs per workspace
            workspace_costs = df.groupby("workspace_id")["amount"].sum().reset_index()
            workspace_costs.columns = ["workspace_id", "cost"]

            # Try to get workspace metadata to map IDs to names
            try:
                workspaces_meta = workspaces_metadata()
                workspace_lookup = {ws["id"]: ws for ws in workspaces_meta}
                print(f"Successfully loaded {len(workspaces_meta)} workspaces metadata")
            except Exception as meta_error:
                print(f"Warning: Could not load workspaces metadata: {meta_error}")
                workspace_lookup = {}

            # Map workspace IDs to names and add creation times for sorting
            def get_workspace_info(wid):
                if wid in workspace_lookup:
                    return {
                        "name": workspace_lookup[wid]["name"]
                        or f"Workspace {wid[-6:]}",
                        "created_at": workspace_lookup[wid]["created_at"],
                    }
                elif wid == "default":
                    return {"name": "Default", "created_at": "1970-01-01T00:00:00Z"}
                else:
                    return {
                        "name": f"Workspace {wid[-6:]}",
                        "created_at": "1970-01-01T00:00:00Z",
                    }

            workspace_costs["workspace_info"] = workspace_costs["workspace_id"].apply(
                get_workspace_info
            )
            workspace_costs["workspace"] = workspace_costs["workspace_info"].apply(
                lambda x: x["name"]
            )
            workspace_costs["created_at"] = workspace_costs["workspace_info"].apply(
                lambda x: x["created_at"]
            )

            # Sort by creation time (oldest first)
            workspace_costs = workspace_costs.sort_values("created_at")

            result = workspace_costs[["workspace", "cost"]].to_dict(orient="list")
            print(f"Workspace cost result: {result}")
            return result
        except Exception as e:
            print(f"Error in workspace_cost_chart_data: {e}")
            import traceback

            traceback.print_exc()
            return {"workspace": [], "cost": []}

    @render_object
    def workspace_cost_table_data():
        """Detailed workspace cost table with totals and token usage"""
        cost_df = cost_data()
        usage_df = usage_data()
        print(
            f"Workspace cost table data - cost_df shape: {cost_df.shape if not cost_df.empty else 'empty'}, usage_df shape: {usage_df.shape if not usage_df.empty else 'empty'}"
        )

        if cost_df.empty and usage_df.empty:
            print("Returning empty workspace cost table data - no cost or usage data")
            return {
                "workspace": [],
                "cost": [],
                "input_tokens": [],
                "output_tokens": [],
                "total_tokens": [],
                "creation_time": [],
                "total": 0,
            }

        try:
            # Get workspace metadata to map IDs to names and creation times
            try:
                workspaces_meta = workspaces_metadata()
                workspace_lookup = {ws["id"]: ws for ws in workspaces_meta}
                print(
                    f"Successfully loaded {len(workspaces_meta)} workspaces metadata for cost table"
                )
            except Exception as meta_error:
                print(
                    f"Warning: Could not load workspaces metadata for cost table: {meta_error}"
                )
                workspace_lookup = {}

            # Combine cost and usage data by workspace
            results = []

            # Get all workspace IDs from both datasets
            workspace_ids = set()
            if not cost_df.empty:
                workspace_ids.update(cost_df["workspace_id"].unique())
            if not usage_df.empty:
                workspace_ids.update(usage_df["workspace_id"].unique())

            for workspace_id in workspace_ids:
                # Get cost for this workspace
                workspace_cost = 0
                if not cost_df.empty:
                    workspace_cost_df = cost_df[cost_df["workspace_id"] == workspace_id]
                    workspace_cost = (
                        workspace_cost_df["amount"].sum()
                        if not workspace_cost_df.empty
                        else 0
                    )

                # Get token usage for this workspace
                input_tokens = 0
                output_tokens = 0
                if not usage_df.empty:
                    workspace_usage_df = usage_df[
                        usage_df["workspace_id"] == workspace_id
                    ]
                    if not workspace_usage_df.empty:
                        input_tokens = workspace_usage_df["input_tokens"].sum()
                        output_tokens = workspace_usage_df["output_tokens"].sum()

                total_tokens = input_tokens + output_tokens

                # Get workspace info
                if workspace_id in workspace_lookup:
                    workspace_name = (
                        workspace_lookup[workspace_id]["name"]
                        or f"Workspace {workspace_id[-6:]}"
                    )
                    created_at = workspace_lookup[workspace_id]["created_at"]
                elif workspace_id == "default":
                    workspace_name = "Default"
                    created_at = "1970-01-01T00:00:00Z"
                else:
                    workspace_name = f"Workspace {workspace_id[-6:]}"
                    created_at = "1970-01-01T00:00:00Z"

                results.append(
                    {
                        "workspace": workspace_name,
                        "cost": float(workspace_cost),
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                        "total_tokens": int(total_tokens),
                        "created_at": created_at,
                    }
                )

            # Sort by creation time (oldest first) - default sorting
            results.sort(key=lambda x: x["created_at"])

            # Calculate total cost
            total_cost = sum(r["cost"] for r in results)

            # Convert to column-major format
            result = {
                "workspace": [r["workspace"] for r in results],
                "cost": [r["cost"] for r in results],
                "input_tokens": [r["input_tokens"] for r in results],
                "output_tokens": [r["output_tokens"] for r in results],
                "total_tokens": [r["total_tokens"] for r in results],
                "creation_time": [r["created_at"] for r in results],
                "total": float(total_cost),
            }
            print(f"Workspace cost table result: {result}")
            return result
        except Exception as e:
            print(f"Error in workspace_cost_table_data: {e}")
            import traceback

            traceback.print_exc()
            return {
                "workspace": [],
                "cost": [],
                "input_tokens": [],
                "output_tokens": [],
                "total_tokens": [],
                "creation_time": [],
                "total": 0,
            }

    @render_object
    def api_key_usage_chart_data():
        """Token usage breakdown by API key"""
        df = usage_data()
        print(
            f"API key usage chart data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty API key usage data")
            return {"api_key": [], "tokens": []}

        try:
            # Group by api_key_id to get token usage per API key
            api_key_usage = (
                df.groupby("api_key_id")
                .agg({"input_tokens": "sum", "output_tokens": "sum"})
                .reset_index()
            )

            api_key_usage["total_tokens"] = (
                api_key_usage["input_tokens"] + api_key_usage["output_tokens"]
            )

            # Get API key metadata to map IDs to names
            api_keys_meta = api_keys_metadata()
            api_key_lookup = {key["id"]: key for key in api_keys_meta}

            # Map API key IDs to names and add creation times for sorting
            def get_api_key_info(kid):
                if kid in api_key_lookup:
                    return {
                        "name": api_key_lookup[kid]["name"] or f"API Key {kid[-6:]}",
                        "created_at": api_key_lookup[kid]["created_at"],
                    }
                else:
                    return {
                        "name": f"API Key {kid[-6:]}",
                        "created_at": "1970-01-01T00:00:00Z",
                    }

            api_key_usage["api_key_info"] = api_key_usage["api_key_id"].apply(
                get_api_key_info
            )
            api_key_usage["api_key"] = api_key_usage["api_key_info"].apply(
                lambda x: x["name"]
            )
            api_key_usage["created_at"] = api_key_usage["api_key_info"].apply(
                lambda x: x["created_at"]
            )

            # Sort by creation time (oldest first)
            api_key_usage = api_key_usage.sort_values("created_at")

            result = api_key_usage[["api_key", "total_tokens"]].copy()
            result.columns = ["api_key", "tokens"]
            chart_result = result.to_dict(orient="list")
            print(f"API key usage result: {chart_result}")
            return chart_result
        except Exception as e:
            print(f"Error in api_key_usage_chart_data: {e}")
            return {"api_key": [], "tokens": []}

    @render_object
    def api_key_usage_table_data():
        """Detailed API key usage table with workspace information"""
        df = usage_data()
        print(
            f"API key usage table data - df shape: {df.shape if not df.empty else 'empty'}"
        )
        if df.empty:
            print("Returning empty API key usage table data")
            return {
                "api_key": [],
                "workspace": [],
                "input_tokens": [],
                "output_tokens": [],
                "total_tokens": [],
                "creation_time": [],
            }

        try:
            # Group by api_key_id to get detailed token usage per API key
            api_key_usage = (
                df.groupby(["api_key_id", "workspace_id"])
                .agg({"input_tokens": "sum", "output_tokens": "sum"})
                .reset_index()
            )

            api_key_usage["total_tokens"] = (
                api_key_usage["input_tokens"] + api_key_usage["output_tokens"]
            )

            # Get API key metadata to map IDs to names and creation times
            try:
                api_keys_meta = api_keys_metadata()
                api_key_lookup = {key["id"]: key for key in api_keys_meta}
                print(
                    f"Successfully loaded {len(api_keys_meta)} API keys metadata for usage table"
                )
            except Exception as meta_error:
                print(
                    f"Warning: Could not load API keys metadata for usage table: {meta_error}"
                )
                api_key_lookup = {}

            # Get workspace metadata to map workspace IDs to names
            try:
                workspaces_meta = workspaces_metadata()
                workspace_lookup = {ws["id"]: ws for ws in workspaces_meta}
                print(
                    f"Successfully loaded {len(workspaces_meta)} workspaces metadata for usage table"
                )
            except Exception as meta_error:
                print(
                    f"Warning: Could not load workspaces metadata for usage table: {meta_error}"
                )
                workspace_lookup = {}

            # Map API key IDs to names and add creation times
            def get_api_key_info(kid):
                if kid in api_key_lookup:
                    return {
                        "name": api_key_lookup[kid]["name"] or f"API Key {kid[-6:]}",
                        "created_at": api_key_lookup[kid]["created_at"],
                    }
                else:
                    return {
                        "name": f"API Key {kid[-6:]}",
                        "created_at": "1970-01-01T00:00:00Z",
                    }

            # Map workspace IDs to names
            def get_workspace_name(wid):
                if wid in workspace_lookup:
                    return workspace_lookup[wid]["name"] or f"Workspace {wid[-6:]}"
                elif wid == "default":
                    return "Default"
                else:
                    return f"Workspace {wid[-6:]}"

            api_key_usage["api_key_info"] = api_key_usage["api_key_id"].apply(
                get_api_key_info
            )
            api_key_usage["api_key"] = api_key_usage["api_key_info"].apply(
                lambda x: x["name"]
            )
            api_key_usage["created_at"] = api_key_usage["api_key_info"].apply(
                lambda x: x["created_at"]
            )
            api_key_usage["workspace"] = api_key_usage["workspace_id"].apply(
                get_workspace_name
            )

            # Sort by creation time (oldest first) - default sorting
            api_key_usage = api_key_usage.sort_values("created_at")

            result = api_key_usage[
                [
                    "api_key",
                    "workspace",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "created_at",
                ]
            ].to_dict(orient="list")
            result["creation_time"] = result.pop("created_at")  # Rename for consistency
            print(f"API key usage table result: {result}")
            return result
        except Exception as e:
            print(f"Error in api_key_usage_table_data: {e}")
            import traceback

            traceback.print_exc()
            return {
                "api_key": [],
                "workspace": [],
                "input_tokens": [],
                "output_tokens": [],
                "total_tokens": [],
                "creation_time": [],
            }

    # === DATA TABLE ===

    @render_object
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

    @render_object
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
