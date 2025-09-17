# pyright: strict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from data_types import UsageDataRow, WorkspaceData, ApiKeyData, CostDataRow


def generate_demo_usage_data(granularity: str = "1d") -> pd.DataFrame:
    """Generate demo usage data when API is unavailable"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    rows: list[UsageDataRow] = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    service_tiers = ["standard", "batch"]
    workspaces = ["ws_123abc", "ws_456def", "ws_789ghi", "default"]
    api_keys = [
        "sk-ant-api03-123",
        "sk-ant-api03-456",
        "sk-ant-api03-789",
        "sk-ant-api03-000",
        "apikey_01FGG6VMYwTs852ZvwBm957Q",
        "apikey_01H7Wwfkf1pCo13i3f2tn933",
        "apikey_01M2Ub8nT2eTXCsbxvaFjVPa",
    ]

    # Generate time points based on granularity
    time_points = []
    if granularity == "1h":
        # Generate hourly data points for the last 3 days
        current_time = end_date - timedelta(days=3)
        while current_time <= end_date:
            time_points.append(current_time.strftime("%Y-%m-%d %H:00"))
            current_time += timedelta(hours=1)
    else:
        # Generate daily data points (default behavior)
        for i in range(30):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            time_points.append(current_date)

    for time_point in time_points:
        for model in models:
            for tier in service_tiers:
                for workspace in workspaces:
                    # Each workspace has some API keys
                    workspace_api_keys = (
                        api_keys[:2]
                        if workspace == "ws_123abc"
                        else (
                            api_keys[1:3]
                            if workspace == "ws_456def"
                            else (
                                api_keys[2:4]
                                if workspace == "ws_789ghi"
                                else api_keys[4:]
                            )
                        )  # default workspace gets the null workspace_id keys
                    )
                    for api_key in workspace_api_keys:
                        # Adjust token amounts based on granularity
                        if granularity == "1h":
                            # Hourly data should be smaller amounts
                            input_tokens = np.random.randint(100, 1000)
                            output_tokens = np.random.randint(50, 500)
                        else:
                            # Daily data - larger amounts
                            input_tokens = np.random.randint(1000, 10000)
                            output_tokens = np.random.randint(500, 3000)

                        row: UsageDataRow = {
                            "date": time_point,
                            "model": model,
                            "service_tier": tier,
                            "workspace_id": workspace,
                            "api_key_id": api_key,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cache_creation_1h": int(np.random.randint(0, 100)),
                            "cache_creation_5m": int(np.random.randint(0, 50)),
                            "web_search_requests": int(np.random.randint(0, 10)),
                        }
                        rows.append(row)

    return pd.DataFrame(rows)


def generate_demo_workspace_data() -> list[WorkspaceData]:
    """Generate demo workspace metadata with timestamps, sorted by creation time (oldest first)"""
    from datetime import datetime, timedelta

    base_time = datetime.now()
    workspaces: list[WorkspaceData] = [
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


def generate_demo_api_key_data() -> list[ApiKeyData]:
    """Generate demo API key metadata with timestamps, sorted by creation time (oldest first)"""
    from datetime import datetime, timedelta

    base_time = datetime.now()
    api_keys: list[ApiKeyData] = [
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
            "name": "Test Key",
            "workspace_id": "ws_oldformat",
            "partial_key_hint": "sk-ant-api03-legacy...old",
            "created_at": (base_time - timedelta(days=45)).isoformat() + "Z",
        },
        # API keys with null workspace_id (matching the user's example)
        {
            "id": "apikey_01FGG6VMYwTs852ZvwBm957Q",
            "name": "Application Key",
            "workspace_id": None,
            "partial_key_hint": "sk-ant-api03-vsc...1AAA",
            "created_at": (base_time - timedelta(days=120)).isoformat() + "Z",
        },
        {
            "id": "apikey_01H7Wwfkf1pCo13i3f2tn933",
            "name": "Personal Assistant Key",
            "workspace_id": None,
            "partial_key_hint": "sk-ant-api03-Xaa...yQAA",
            "created_at": (base_time - timedelta(days=90)).isoformat() + "Z",
        },
        {
            "id": "apikey_01M2Ub8nT2eTXCsbxvaFjVPa",
            "name": "Mobile App Integration",
            "workspace_id": None,
            "partial_key_hint": "sk-ant-api03-hCc...IwAA",
            "created_at": (base_time - timedelta(days=80)).isoformat() + "Z",
        },
    ]

    # Sort by created_at (oldest first)
    return sorted(api_keys, key=lambda x: x["created_at"], reverse=False)


def generate_demo_cost_data(granularity: str = "1d") -> pd.DataFrame:
    """Generate demo cost data when API is unavailable

    Note: Cost reports are always daily granularity according to Anthropic API,
    so we ignore the granularity parameter and always generate daily data.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    rows: list[CostDataRow] = []
    models = ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
    descriptions = ["Input tokens", "Output tokens", "Cache creation"]
    workspaces = ["ws_123abc", "ws_456def", "ws_789ghi", "default"]
    api_keys = [
        "sk-ant-api03-123",
        "sk-ant-api03-456",
        "sk-ant-api03-789",
        "sk-ant-api03-000",
        "apikey_01FGG6VMYwTs852ZvwBm957Q",
        "apikey_01H7Wwfkf1pCo13i3f2tn933",
        "apikey_01M2Ub8nT2eTXCsbxvaFjVPa",
    ]

    # Cost reports are always daily - ignore granularity parameter
    time_points = []
    for i in range(30):
        current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        time_points.append(current_date)

    for time_point in time_points:
        for model in models:
            for desc in descriptions:
                for workspace in workspaces:
                    # Each workspace has some API keys
                    workspace_api_keys = (
                        api_keys[:2]
                        if workspace == "ws_123abc"
                        else (
                            api_keys[1:3]
                            if workspace == "ws_456def"
                            else (
                                api_keys[2:4]
                                if workspace == "ws_789ghi"
                                else api_keys[4:]
                            )
                        )  # default workspace gets the null workspace_id keys
                    )
                    for api_key in workspace_api_keys:
                        # Cost reports are always daily amounts
                        amount = np.random.uniform(0.50, 7.50)

                        row: CostDataRow = {
                            "date": time_point,
                            "description": desc,
                            "amount": float(amount),
                            "currency": "USD",
                            "model": model,
                            "workspace_id": workspace,
                            "api_key_id": api_key,
                            "service_tier": "standard",
                            "cost_type": "tokens",
                            "token_type": "input" if "Input" in desc else "output",
                        }
                        rows.append(row)

    return pd.DataFrame(rows)
