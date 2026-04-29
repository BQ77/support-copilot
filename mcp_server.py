"""
MCP server scaffold for Support Copilot.

Exposes tools the LangGraph agent can call to take actions beyond
pure Q&A: account lookups, support ticket creation, etc.

STATUS: Scaffolded with two tool stubs. Wiring into agent.py is
the next milestone (see roadmap in README).
"""
from typing import Any


def lookup_account(user_email: str) -> dict[str, Any]:
    """Look up account info for a user by email. Returns mock data."""
    return {
        "email": user_email,
        "plan": "Pro",
        "status": "active",
        "open_tickets": 0,
        "created_at": "2024-08-15",
        "_note": "MOCK DATA - replace with real lookup",
    }


def create_support_ticket(subject: str, body: str, priority: str = "normal") -> dict[str, Any]:
    """Create a support ticket. Stub."""
    return {
        "ticket_id": "TKT-12345",
        "status": "created",
        "subject": subject,
        "priority": priority,
        "_note": "MOCK - integrate with Zendesk/Linear/GH Issues via MCP",
    }


# ============================================================
# MCP wiring (TODO - next milestone)
# ============================================================
# from mcp.server import Server
#
# server = Server("support-copilot")
#
# @server.tool()
# def lookup_account_tool(user_email: str) -> dict:
#     return lookup_account(user_email)
#
# @server.tool()
# def create_ticket_tool(subject: str, body: str, priority: str) -> dict:
#     return create_support_ticket(subject, body, priority)
#
# if __name__ == "__main__":
#     server.run()
