import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
from starlette.requests import Request
from starlette.responses import JSONResponse,HTMLResponse,FileResponse
from app.artifacts.service import (
    ArtifactService,
    ArtifactNotFoundError,
)
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
) -> HTMLResponse:
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>Data Analyst MCP - Upload Dataset</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: Arial, sans-serif;
                background: #f5f5f5;
                padding: 24px;
            }

            .card {
                width: 100%;
                max-width: 560px;
                background: white;
                padding: 32px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            }

            h1 {
                margin-top: 0;
                margin-bottom: 8px;
            }

            .subtitle {
                margin-top: 0;
                margin-bottom: 28px;
                color: #666;
            }

            input[type="file"] {
                width: 100%;
                padding: 14px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-bottom: 16px;
            }

            button {
                width: 100%;
                padding: 13px 16px;
                border: 0;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            }

            #uploadButton {
                background: #111;
                color: white;
            }

            #uploadButton:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            #result {
                display: none;
                margin-top: 24px;
                padding: 18px;
                background: #f7f7f7;
                border-radius: 8px;
            }

            #datasetId {
                display: block;
                margin: 10px 0;
                padding: 10px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                overflow-wrap: anywhere;
            }

            #copyButton {
                margin-top: 10px;
                background: #e9e9e9;
            }

            #error {
                display: none;
                margin-top: 20px;
                padding: 14px;
                border-radius: 8px;
                background: #ffe8e8;
                color: #9c1c1c;
            }
        </style>
    </head>

    <body>
        <div class="card">

            <h1>Upload Dataset</h1>

            <p class="subtitle">
                Upload a CSV or XLSX dataset for Data Analyst MCP.
            </p>

            <form id="uploadForm">

                <input
                    id="fileInput"
                    name="file"
                    type="file"
                    accept=".csv,.xlsx"
                    required
                >

                <button
                    id="uploadButton"
                    type="submit"
                >
                    Upload Dataset
                </button>

            </form>

            <div id="result">

                <strong>Dataset uploaded successfully</strong>

                <span id="datasetId"></span>

                <button
                    id="copyButton"
                    type="button"
                >
                    Copy Dataset ID
                </button>

            </div>

            <div id="error"></div>

        </div>

        <script>
            const form =
                document.getElementById("uploadForm");

            const fileInput =
                document.getElementById("fileInput");

            const uploadButton =
                document.getElementById("uploadButton");

            const result =
                document.getElementById("result");

            const datasetId =
                document.getElementById("datasetId");

            const copyButton =
                document.getElementById("copyButton");

            const error =
                document.getElementById("error");

            form.addEventListener(
                "submit",
                async (event) => {

                    event.preventDefault();

                    result.style.display = "none";
                    error.style.display = "none";

                    const file =
                        fileInput.files[0];

                    if (!file) {
                        return;
                    }

                    const formData =
                        new FormData();

                    formData.append(
                        "file",
                        file,
                    );

                    uploadButton.disabled = true;
                    uploadButton.textContent =
                        "Uploading...";

                    try {

                        const response =
                            await fetch(
                                "/api/v1/datasets/upload",
                                {
                                    method: "POST",
                                    body: formData,
                                }
                            );

                        const data =
                            await response.json();

                        if (!response.ok) {
                            throw new Error(
                                data.detail ||
                                "Dataset upload failed."
                            );
                        }

                        datasetId.textContent =
                            data.dataset_id;

                        result.style.display =
                            "block";

                    } catch (uploadError) {

                        error.textContent =
                            uploadError.message;

                        error.style.display =
                            "block";

                    } finally {

                        uploadButton.disabled =
                            false;

                        uploadButton.textContent =
                            "Upload Dataset";
                    }
                }
            );

            copyButton.addEventListener(
                "click",
                async () => {

                    await navigator.clipboard.writeText(
                        datasetId.textContent
                    );

                    copyButton.textContent =
                        "Copied!";

                    setTimeout(
                        () => {
                            copyButton.textContent =
                                "Copy Dataset ID";
                        },
                        1500
                    );
                }
            );
        </script>
    </body>
    </html>
    """

    return HTMLResponse(html) 


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