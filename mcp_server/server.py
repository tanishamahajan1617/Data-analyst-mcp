from fastmcp import FastMCP

from mcp_server.tools.dataset import (
    register_dataset_tools,
)
from mcp_server.tools.analytics import (
    register_analytics_tools,
)
from mcp_server.tools.powerbi import (
    register_powerbi_tools,
)
from mcp_server.tools.workflow import (
    register_workflow_tools,
)
import os
mcp = FastMCP(
    "Data Analyst MCP"
)


@mcp.tool
def health_check() -> dict[str, str]:
    """Check whether the Data Analyst MCP server is running."""

    return {
        "status": "ok",
        "server": "Data Analyst MCP",
    }


register_dataset_tools(mcp)
register_analytics_tools(mcp)
register_powerbi_tools(mcp)
register_workflow_tools(mcp)


if __name__ == "__main__":
    transport = os.getenv(
        "MCP_TRANSPORT",
        "stdio",
    )

    if transport == "http":
        host = os.getenv(
            "MCP_HOST",
            "0.0.0.0",
        )

        port = int(
            os.getenv(
                "PORT",
                os.getenv("MCP_PORT", "8000"),
            )
        )

        mcp.run(
            transport="http",
            host=host,
            port=port,
            path="/mcp",
        )

    else:
        mcp.run(
            transport="stdio",
        )