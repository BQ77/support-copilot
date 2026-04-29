"""
Tools the agent can call.

Wrapped in Anthropic's native tool-use schema, which is the same
primitive MCP exposes over a server protocol. mcp_server.py shows
how these would be exposed as a remote MCP server in production.
"""
from typing import Any
import time

# ============================================================
# Tool schema (what Claude sees)
# ============================================================

TOOLS = [
    {
        "name": "lookup_account",
        "description": (
            "Look up account info for a user by their email address. "
            "Use this when the user asks about THEIR OWN usage, plan, "
            "remaining quota, or account status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_email": {
                    "type": "string",
                    "description": "The user's email address",
                },
            },
            "required": ["user_email"],
        },
    },
    {
        "name": "create_support_ticket",
        "description": (
            "Create a support ticket when the issue clearly needs "
            "human follow-up (billing dispute, urgent outage, etc.). "
            "Returns a ticket ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                },
            },
            "required": ["subject", "body"],
        },
    },
]


# ============================================================
# Implementations (mocked - replace with real integrations)
# ============================================================

def lookup_account(user_email: str) -> dict[str, Any]:
    """Mock CRM account lookup. Replace with real call to your CRM."""
    return {
        "email": user_email,
        "plan": "Pro",
        "status": "active",
        "monthly_quota": 500000,
        "monthly_used": 142318,
        "monthly_remaining": 357682,
        "open_tickets": 0,
        "_note": "MOCK DATA - replace with real CRM lookup",
    }


def create_support_ticket(
    subject: str, body: str, priority: str = "normal"
) -> dict[str, Any]:
    """Mock ticket creation. Replace with Zendesk / Linear / GitHub Issues."""
    return {
        "ticket_id": f"TKT-{int(time.time()) % 100000}",
        "status": "created",
        "subject": subject,
        "priority": priority,
        "estimated_response_hours": 4 if priority in ["high", "urgent"] else 24,
        "_note": "MOCK - integrate with real ticketing in production",
    }


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Dispatch a tool call from Claude to its implementation."""
    if tool_name == "lookup_account":
        return lookup_account(**tool_input)
    if tool_name == "create_support_ticket":
        return create_support_ticket(**tool_input)
    return {"error": f"Unknown tool: {tool_name}"}
