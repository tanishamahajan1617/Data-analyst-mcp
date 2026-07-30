import ipaddress
import socket
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from app.config import MAX_FILE_SIZE_MB
from app.datasets.store import DatasetStore, InvalidDatasetError


class RemoteDatasetError(Exception):
    """Raised when a remote dataset cannot be imported."""


class RemoteDatasetImporter:
    def __init__(self) -> None:
        self.store = DatasetStore()

    def import_url(
        self,
        url: str,
        filename: str | None = None,
    ) -> dict[str, Any]:

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise RemoteDatasetError(
                "Only HTTP and HTTPS URLs are supported."
            )

        if not parsed.hostname:
            raise RemoteDatasetError(
                "URL must contain a valid hostname."
            )

        self._validate_public_host(parsed.hostname)

        safe_filename = (
            Path(filename).name
            if filename
            else self._filename_from_url(parsed.path)
        )

        # Reuse DatasetStore's extension validation early.
        self.store._validate_extension(safe_filename)

        max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

        temp_path: Path | None = None

        try:
            with httpx.Client(
                timeout=30.0,
                follow_redirects=False,
            ) as client:
                with client.stream("GET", url) as response:
                    response.raise_for_status()

                    content_length = response.headers.get(
                        "content-length"
                    )

                    if content_length:
                        try:
                            declared_size = int(content_length)
                        except ValueError:
                            declared_size = None

                        if (
                            declared_size is not None
                            and declared_size > max_bytes
                        ):
                            raise RemoteDatasetError(
                                f"Remote file exceeds the "
                                f"{MAX_FILE_SIZE_MB} MB limit."
                            )

                    suffix = Path(safe_filename).suffix

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix,
                    ) as temp_file:
                        temp_path = Path(temp_file.name)

                        downloaded = 0

                        for chunk in response.iter_bytes():
                            downloaded += len(chunk)

                            if downloaded > max_bytes:
                                raise RemoteDatasetError(
                                    f"Remote file exceeds the "
                                    f"{MAX_FILE_SIZE_MB} MB limit."
                                )

                            temp_file.write(chunk)

            if temp_path is None:
                raise RemoteDatasetError(
                    "Remote dataset could not be downloaded."
                )

            return self.store.save_path(
                source_path=temp_path,
                filename=safe_filename,
            )

        except httpx.HTTPError as exc:
            raise RemoteDatasetError(
                f"Unable to download dataset: {exc}"
            ) from exc

        except InvalidDatasetError:
            raise

        finally:
            if (
                temp_path is not None
                and temp_path.exists()
            ):
                temp_path.unlink()

    @staticmethod
    def _filename_from_url(path: str) -> str:
        filename = Path(
            unquote(path)
        ).name

        if not filename:
            raise RemoteDatasetError(
                "Could not determine the filename from the URL. "
                "Provide the filename argument explicitly."
            )

        return filename

    @staticmethod
    def _validate_public_host(hostname: str) -> None:
        try:
            addresses = socket.getaddrinfo(
                hostname,
                None,
            )
        except socket.gaierror as exc:
            raise RemoteDatasetError(
                "Unable to resolve the URL hostname."
            ) from exc

        for address in addresses:
            ip_string = address[4][0]

            try:
                ip = ipaddress.ip_address(ip_string)
            except ValueError:
                continue

            if not ip.is_global:
                raise RemoteDatasetError(
                    "URLs resolving to private, local, "
                    "reserved, or non-public addresses "
                    "are not allowed."
                )