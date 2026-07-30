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
    mcp.run()