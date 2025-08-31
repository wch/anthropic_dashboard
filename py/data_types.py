# pyright: strict
from typing import TypedDict


class UsageDataRow(TypedDict):
    date: str
    model: str
    service_tier: str
    workspace_id: str
    api_key_id: str
    input_tokens: int
    output_tokens: int
    cache_creation_1h: int
    cache_creation_5m: int
    web_search_requests: int


class WorkspaceData(TypedDict):
    id: str
    name: str
    display_color: str
    created_at: str


class ApiKeyData(TypedDict):
    id: str
    name: str
    workspace_id: str
    partial_key_hint: str
    created_at: str


class CostDataRow(TypedDict):
    date: str
    description: str
    amount: float
    currency: str
    model: str
    workspace_id: str
    api_key_id: str
    service_tier: str
    cost_type: str
    token_type: str
