# pyright: strict
# pyright: reportUnusedFunction=false

from typing import TypedDict
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
            if granularity == "1h":
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
            if granularity == "1h":
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
                amount_raw = result.get("amount", 0)
                try:
                    amount = float(amount_raw)
                except (ValueError, TypeError):
                    amount = 0.0

                row: CostDataRow = {
                    "date": date,
                    "description": str(result.get("description", "Unknown")),
                    "amount": amount,
                    "currency": str(result.get("currency", "USD")),
                    "model": str(result.get("model", "unknown")),
                    "workspace_id": str(result.get("workspace_id", "unknown")),
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
            return generate_demo_usage_data(granularity)

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
                ANTHROPIC_API_KEY,
                start_date,
                end_date,
                bucket_width=granularity,
                limit=api_limit,
            )
            df = process_usage_data(usage_response, granularity)

            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No usage data returned from API, using demo data")
                return generate_demo_usage_data(granularity)

            print(f"Returning real usage data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in raw_usage_data: {e}, using demo data")
            return generate_demo_usage_data(granularity)

    @reactive.calc
    def usage_data() -> pd.DataFrame:
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
    def raw_cost_data() -> pd.DataFrame:
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
            return generate_demo_cost_data(granularity)

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

            cost_response = fetch_anthropic_cost_report(
                ANTHROPIC_API_KEY,
                start_date,
                end_date,
                limit=cost_limit,
            )
            df = process_cost_data(cost_response, granularity)

            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No cost data returned from API, using demo data")
                return generate_demo_cost_data(granularity)

            print(f"Returning real cost data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in raw_cost_data: {e}, using demo data")
            return generate_demo_cost_data(granularity)

    @reactive.calc
    def cost_data() -> pd.DataFrame:
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
            workspaces_response = fetch_workspaces(api_key=ANTHROPIC_API_KEY)
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
                ANTHROPIC_API_KEY,
                workspace_filter if workspace_filter != "all" else None,
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

    @render_object
    def available_workspaces() -> list[UiWorkspaceData]:
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

    @render_object
    def available_api_keys() -> list[UiApiKeyData]:
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

    @render_object
    def available_models() -> list[str]:
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

    @render_object
    def api_status() -> UiApiStatus:
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
