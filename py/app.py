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

# Check API key availability and warn user
if not ANTHROPIC_API_KEY:
    print("⚠️  Warning: ANTHROPIC_ADMIN_KEY not found in environment variables.")
    print("   Dashboard will show demo data instead of live API data.")
    print("   Add your Anthropic Admin API key to .env file to see real data.")
else:
    print("✓ Anthropic API key found. Dashboard will fetch live data.")

def fetch_anthropic_usage_report(starting_at, ending_at=None, bucket_width="1d", limit=31):
    """Fetch usage report from Anthropic API"""
    if not ANTHROPIC_API_KEY:
        return None
    
    url = f"{ANTHROPIC_API_BASE}/v1/organizations/usage_report/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json"
    }
    
    params = {
        "starting_at": starting_at,
        "bucket_width": bucket_width,
        "limit": limit,
        "group_by[]": ["model", "service_tier"]
    }
    
    if ending_at:
        params["ending_at"] = ending_at
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching usage report: {e}")
        return None

def fetch_anthropic_cost_report(starting_at, ending_at=None, limit=31):
    """Fetch cost report from Anthropic API"""
    if not ANTHROPIC_API_KEY:
        return None
    
    url = f"{ANTHROPIC_API_BASE}/v1/organizations/cost_report"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json"
    }
    
    params = {
        "starting_at": starting_at,
        "limit": limit,
        "group_by[]": ["description", "workspace_id"]
    }
    
    if ending_at:
        params["ending_at"] = ending_at
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cost report: {e}")
        return None

def generate_demo_usage_data():
    """Generate demo usage data when API is unavailable"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    rows = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    service_tiers = ["standard", "batch"]
    
    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for model in models:
            for tier in service_tiers:
                input_tokens = np.random.randint(1000, 10000)
                output_tokens = np.random.randint(500, 3000)
                rows.append({
                    "date": current_date,
                    "model": model,
                    "service_tier": tier,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_creation_1h": np.random.randint(0, 100),
                    "cache_creation_5m": np.random.randint(0, 50),
                    "web_search_requests": np.random.randint(0, 10)
                })
    
    return pd.DataFrame(rows)

def generate_demo_cost_data():
    """Generate demo cost data when API is unavailable"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    rows = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    descriptions = ["Input tokens", "Output tokens", "Cache creation"]
    
    for i in range(7):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for model in models:
            for desc in descriptions:
                amount = np.random.uniform(0.50, 15.00)
                rows.append({
                    "date": current_date,
                    "description": desc,
                    "amount": amount,
                    "currency": "USD",
                    "model": model,
                    "service_tier": "standard",
                    "cost_type": "tokens",
                    "token_type": "input" if "Input" in desc else "output"
                })
    
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
                rows.append({
                    "date": date,
                    "model": result.get("model", "unknown"),
                    "service_tier": result.get("service_tier", "standard"),
                    "input_tokens": result.get("uncached_input_tokens", 0) + result.get("cache_read_input_tokens", 0),
                    "output_tokens": result.get("output_tokens", 0),
                    "cache_creation_1h": result.get("cache_creation", {}).get("ephemeral_1h_input_tokens", 0),
                    "cache_creation_5m": result.get("cache_creation", {}).get("ephemeral_5m_input_tokens", 0),
                    "web_search_requests": result.get("server_tool_use", {}).get("web_search_requests", 0)
                })
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
                rows.append({
                    "date": date,
                    "description": result.get("description", "Unknown"),
                    "amount": float(result.get("amount", 0)),
                    "currency": result.get("currency", "USD"),
                    "model": result.get("model", "unknown"),
                    "service_tier": result.get("service_tier", "standard"),
                    "cost_type": result.get("cost_type", "tokens"),
                    "token_type": result.get("token_type", "unknown")
                })
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
    def usage_data():
        """Fetch and process usage data with fallback to demo data"""
        try:
            start_date = input.date_start() if hasattr(input, 'date_start') and input.date_start() is not None else default_start
            end_date = input.date_end() if hasattr(input, 'date_end') and input.date_end() is not None else default_end
        except:
            # If input access fails, use default dates
            start_date = default_start
            end_date = default_end
        
        print(f"Usage data - start: {start_date}, end: {end_date}, has_key: {bool(ANTHROPIC_API_KEY)}")
        
        if not ANTHROPIC_API_KEY:
            # Return demo data when API key is not available
            print("Using demo usage data (no API key)")
            return generate_demo_usage_data()
        
        try:
            usage_response = fetch_anthropic_usage_report(start_date, end_date)
            df = process_usage_data(usage_response)
            
            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No usage data returned from API, using demo data")
                return generate_demo_usage_data()
            
            print(f"Returning real usage data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in usage_data: {e}, using demo data")
            return generate_demo_usage_data()
    
    @reactive.calc 
    def cost_data():
        """Fetch and process cost data with fallback to demo data"""
        try:
            start_date = input.date_start() if hasattr(input, 'date_start') and input.date_start() is not None else default_start
            end_date = input.date_end() if hasattr(input, 'date_end') and input.date_end() is not None else default_end
        except:
            # If input access fails, use default dates
            start_date = default_start
            end_date = default_end
        
        print(f"Cost data - start: {start_date}, end: {end_date}, has_key: {bool(ANTHROPIC_API_KEY)}")
        
        if not ANTHROPIC_API_KEY:
            # Return demo data when API key is not available
            print("Using demo cost data (no API key)")
            return generate_demo_cost_data()
        
        try:
            cost_response = fetch_anthropic_cost_report(start_date, end_date)
            df = process_cost_data(cost_response)
            
            # If API call succeeded but returned empty data, use demo data
            if df.empty:
                print("No cost data returned from API, using demo data")
                return generate_demo_cost_data()
            
            print(f"Returning real cost data with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error in cost_data: {e}, using demo data")
            return generate_demo_cost_data()
    
    # === API STATUS ===
    
    @render_object()
    def api_status():
        """API connection status and info"""
        if not ANTHROPIC_API_KEY:
            return {
                "status": "demo",
                "message": "ANTHROPIC_ADMIN_KEY not found. Add your API key to .env file for live data.",
                "last_update": datetime.now().isoformat()
            }
        
        # Test API connection with a simple request
        try:
            test_response = fetch_anthropic_usage_report(
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z"),
                datetime.now().strftime("%Y-%m-%dT23:59:59Z"),
                limit=1
            )
            
            if test_response is not None:
                return {
                    "status": "connected",
                    "message": "Connected to Anthropic API. Showing live data.",
                    "last_update": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "API key found but unable to fetch data. Check API key permissions.",
                    "last_update": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"API connection failed: {str(e)}",
                "last_update": datetime.now().isoformat()
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
        print(f"Token usage chart data - df shape: {df.shape if not df.empty else 'empty'}")
        if df.empty:
            print("Returning empty token usage data")
            return {"date": [], "input_tokens": [], "output_tokens": []}
        
        daily_usage = df.groupby("date").agg({
            "input_tokens": "sum",
            "output_tokens": "sum"
        }).reset_index()
        
        result = daily_usage.to_dict(orient="list")
        print(f"Token usage result: {result}")
        return result
    
    @render_object()
    def cost_by_model_chart_data():
        """Cost breakdown by model"""
        df = cost_data()
        print(f"Cost by model chart data - df shape: {df.shape if not df.empty else 'empty'}")
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
        print(f"Service tier chart data - df shape: {df.shape if not df.empty else 'empty'}")
        if df.empty:
            print("Returning empty service tier data")
            return {"service_tier": [], "tokens": []}
        
        tier_usage = df.groupby("service_tier").agg({
            "input_tokens": "sum",
            "output_tokens": "sum"
        }).reset_index()
        
        tier_usage["total_tokens"] = tier_usage["input_tokens"] + tier_usage["output_tokens"]
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
        table_data = df.groupby(["date", "model"]).agg({
            "input_tokens": "sum",
            "output_tokens": "sum",
            "service_tier": "first"
        }).reset_index()
        
        return table_data.to_dict(orient="list")
    
    @render_object()
    def cost_table_data():
        """Detailed cost table data"""
        df = cost_data()
        if df.empty:
            return {"date": [], "description": [], "amount": [], "model": []}
        
        # Group by date and description
        table_data = df.groupby(["date", "description", "model"]).agg({
            "amount": "sum"
        }).reset_index()
        
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
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax.transAxes)
        else:
            daily_usage = df.groupby("date").agg({
                "input_tokens": "sum",
                "output_tokens": "sum"
            })
            
            dates = pd.to_datetime(daily_usage.index)
            ax.plot(dates, daily_usage["input_tokens"], label="Input Tokens", marker='o')
            ax.plot(dates, daily_usage["output_tokens"], label="Output Tokens", marker='s')
            
            ax.set_xlabel("Date")
            ax.set_ylabel("Token Count")
            ax.set_title("Token Usage Over Time")
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        return fig

app = App(app_ui, server, static_assets=str(Path(__file__).parent / "www"))