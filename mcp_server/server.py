import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
from starlette.requests import Request
from starlette.responses import JSONResponse,HTMLResponse,FileResponse
from app.artifacts.service import (
    ArtifactService,
    ArtifactNotFoundError,
)
from pathlib import Path
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
artifact_service = ArtifactService()

BASE_DIR = Path(__file__).parent

TEMPLATE_DIR = (
    BASE_DIR / "templates"
)

STATIC_DIR = (
    BASE_DIR / "static"
)


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

@mcp.custom_route(
    "/upload",
    methods=["GET"],
)
async def upload_page(
    request: Request,
) -> FileResponse:

    return FileResponse(
        TEMPLATE_DIR / "upload.html",
        media_type="text/html",
    )


@mcp.custom_route(
    "/static/upload.css",
    methods=["GET"],
)
async def upload_css(
    request: Request,
) -> FileResponse:

    return FileResponse(
        STATIC_DIR / "upload.css",
        media_type="text/css",
    )

@mcp.custom_route(
    "/static/upload.js",
    methods=["GET"],
)
async def upload_js(
    request: Request,
) -> FileResponse:

    return FileResponse(
        STATIC_DIR / "upload.js",
        media_type="application/javascript",
    )

@mcp.custom_route(
    "/static/upload.js",
    methods=["GET"],
)
async def upload_js(
    request: Request,
) -> FileResponse:

    return FileResponse(
        STATIC_DIR / "upload.js",
        media_type="application/javascript",
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


@mcp.custom_route(
    "/api/v1/exports/{dataset_id}/download",
    methods=["GET"],
)
async def download_powerbi_artifact(
    request: Request,
) -> FileResponse:

    dataset_id = request.path_params["dataset_id"]

    try:
        archive_path = (
            artifact_service.get_powerbi_archive(
                dataset_id
            )
        )

    except ArtifactNotFoundError:
        return JSONResponse(
            {
                "detail": (
                    f"No Power BI artifact found "
                    f"for dataset '{dataset_id}'."
                )
            },
            status_code=404,
        )

    return FileResponse(
        path=archive_path,
        filename=f"{dataset_id}_powerbi_dashboard.zip",
        media_type="application/zip",
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