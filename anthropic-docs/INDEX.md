# Anthropic API Documentation Index

This directory contains documentation for the Anthropic Admin API endpoints. Use this index for quick reference and to find relevant documentation.

## Quick Reference

### Core Reports & Usage
- **[get-messages-usage-report.md](get-messages-usage-report.md)** - `GET /v1/organizations/usage_report/messages`
  - Get detailed usage statistics for Messages API
  - Supports grouping by model, service_tier, workspace_id, api_key_id
  - Configure bucket_width for time granularity (1h, 1d, 7d, 30d)
  - Essential for dashboard filtering and charts

- **[get-cost-report.md](get-cost-report.md)** - `GET /v1/organizations/cost_report`
  - Get cost breakdown and billing information
  - Group by description, workspace_id, api_key_id, model
  - Used for cost analysis and budget tracking

### Organization Management
- **[get-me.md](get-me.md)** - `GET /v1/organizations/me`
  - Get current organization information
  - Organization metadata and settings

### Workspace Management
- **[list-workspaces.md](list-workspaces.md)** - `GET /v1/organizations/workspaces`
  - List all workspaces in the organization
  - Used for workspace filter dropdown

- **[get-workspace.md](get-workspace.md)** - `GET /v1/organizations/workspaces/{workspace_id}`
  - Get details about a specific workspace
  - Workspace metadata and configuration

- **[list-workspace-members.md](list-workspace-members.md)** - `GET /v1/organizations/workspaces/{workspace_id}/members`
  - List members of a specific workspace
  - User access and permissions per workspace

- **[get-workspace-member.md](get-workspace-member.md)** - `GET /v1/organizations/workspaces/{workspace_id}/members/{user_id}`
  - Get details about a specific workspace member
  - Individual member permissions and role

### API Key Management
- **[list-api-keys.md](list-api-keys.md)** - `GET /v1/organizations/api_keys`
  - List all API keys in the organization
  - Used for API key filter dropdown
  - Can be filtered by workspace_id

- **[get-api-key.md](get-api-key.md)** - `GET /v1/organizations/api_keys/{api_key_id}`
  - Get details about a specific API key
  - API key metadata, permissions, and usage limits

### User Management
- **[list-users.md](list-users.md)** - `GET /v1/organizations/users`
  - List all users in the organization
  - Organization-wide user directory

- **[get-user.md](get-user.md)** - `GET /v1/organizations/users/{user_id}`
  - Get details about a specific user
  - User profile and organization role

## Project Files
- **[README.md](README.md)** - shadcn/ui integration example documentation
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive Shiny-React development guide

## API Usage Patterns for Dashboard

### For Filter Controls:
1. **Workspace Filter**: Use `list-workspaces.md` to populate workspace dropdown
2. **API Key Filter**: Use `list-api-keys.md` filtered by selected workspace
3. **Model Filter**: Extract from usage data (models are returned in usage reports)

### For Data Fetching:
1. **Usage Charts**: Use `get-messages-usage-report.md` with:
   - `group_by[]`: `["model", "service_tier", "workspace_id", "api_key_id"]`
   - `bucket_width`: User-selected granularity ("1h", "1d", "7d", "30d")
   - Filter parameters: `workspace_id`, `api_key_id` when not "all"

2. **Cost Analysis**: Use `get-cost-report.md` with:
   - `group_by[]`: `["description", "workspace_id", "api_key_id", "model"]`
   - Same filtering parameters as usage report

### Authentication
All endpoints require:
- Header: `x-api-key: {ANTHROPIC_ADMIN_KEY}`
- Header: `anthropic-version: 2023-06-01`
- Header: `content-type: application/json`

### Common Query Parameters
- `starting_at`: ISO timestamp for date range start
- `ending_at`: ISO timestamp for date range end (optional)
- `limit`: Maximum number of results (default varies by endpoint)
- `workspace_id`: Filter by specific workspace
- `api_key_id`: Filter by specific API key

## Implementation Notes

### Dashboard Integration
- The filtering system uses these endpoints to populate dropdowns dynamically
- Usage and cost reports support the same filtering parameters
- Granularity control maps to the `bucket_width` parameter in usage reports
- All date ranges use ISO 8601 format with timezone (e.g., "2024-01-01T00:00:00Z")

### Error Handling
- API calls may fail due to permissions or network issues
- Dashboard falls back to demo data when API is unavailable
- Always check for valid API key before making requests

### Data Processing
- Usage data returns column-major format for React consumption
- Cost amounts are in USD with decimal precision
- Timestamps are UTC and need local conversion for display
- Models names may need cleaning (remove "claude-" prefix for display)

## Quick Lookup by Use Case

**Building workspace filter**: → `list-workspaces.md`
**Building API key filter**: → `list-api-keys.md`
**Getting usage stats**: → `get-messages-usage-report.md`
**Getting cost data**: → `get-cost-report.md`
**User management**: → `list-users.md`, `get-user.md`
**Workspace details**: → `get-workspace.md`, `list-workspace-members.md`
**Organization info**: → `get-me.md`