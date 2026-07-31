import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import ensure_data_directories
from app.config import (
    DATA_DIR,
    METADATA_DIR,
)

from app.datasets.store import (
    DatasetStore,
    InvalidDatasetError,
)

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


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

auth = GitHubProvider(
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    base_url=os.environ["BASE_URL"],
)


# ---------------------------------------------------------
# MCP Server
# ---------------------------------------------------------

mcp = FastMCP(
    "Data Analyst MCP",
    auth=auth,
)


# ---------------------------------------------------------
# Services
# ---------------------------------------------------------

dataset_store = DatasetStore()


# ---------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------

@mcp.tool
def health_check() -> dict[str, str]:
    """
    Check whether the Data Analyst MCP server
    is running.
    """

    return {
        "status": "ok",
        "server": "Data Analyst MCP",
    }


register_dataset_tools(mcp)
register_analytics_tools(mcp)
register_powerbi_tools(mcp)
register_workflow_tools(mcp)


# ---------------------------------------------------------
# HTTP API
# ---------------------------------------------------------

@mcp.custom_route(
    "/api/v1/datasets/upload",
    methods=["POST"],
)
async def upload_dataset_http(
    request: Request,
) -> JSONResponse:
    """
    Upload a CSV or XLSX dataset using
    multipart/form-data.

    Expected field:
        file=<CSV/XLSX>

    Returns dataset metadata including dataset_id.
    """

    try:
        form = await request.form()

        upload = form.get("file")

        if upload is None:
            return JSONResponse(
                {
                    "detail": (
                        "Missing multipart field 'file'."
                    )
                },
                status_code=400,
            )

        filename = getattr(
            upload,
            "filename",
            None,
        )

        if not filename:
            return JSONResponse(
                {
                    "detail": (
                        "Uploaded file must have "
                        "a filename."
                    )
                },
                status_code=400,
            )

        # Save using the existing DatasetStore.
        #
        # upload is a Starlette UploadFile.
        # FastAPI UploadFile is based on the same
        # underlying implementation.
        metadata = dataset_store.save_upload(
                                upload
                            )
        
        return JSONResponse(
            metadata,
            status_code=201,
        )

    except InvalidDatasetError as exc:
        return JSONResponse(
            {
                "detail": str(exc),
            },
            status_code=400,
        )

    except Exception as exc:
        return JSONResponse(
            {
                "detail": (
                    f"Dataset upload failed: {exc}"
                ),
            },
            status_code=500,
        )


# ---------------------------------------------------------
# HTTP Health Endpoint
# ---------------------------------------------------------

@mcp.custom_route(
    "/health",
    methods=["GET"],
)
async def http_health_check(
    request: Request,
) -> JSONResponse:

    return JSONResponse(
        {
            "status": "ok",
            "service": "data-analyst-mcp",
            "mcp_endpoint": "/mcp",
            "upload_endpoint": (
                "/api/v1/datasets/upload"
            ),
        }
    )


# ---------------------------------------------------------
# Server Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":

    ensure_data_directories()

    print(
        f"DATA_DIR={DATA_DIR} "
        f"exists={DATA_DIR.exists()}",
        flush=True,
    )

    print(
        f"METADATA_DIR={METADATA_DIR} "
        f"exists={METADATA_DIR.exists()}",
        flush=True,
    )


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
                os.getenv(
                    "MCP_PORT",
                    "8000",
                ),
            )
        )

        mcp.run(
            transport="http",
            host=host,
            port=port,
            path="/",
        )

    else:
        mcp.run(
            transport="stdio",
        )