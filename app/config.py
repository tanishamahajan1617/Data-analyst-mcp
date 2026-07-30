from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
REPAIRED_DATA_DIR = DATA_DIR / "repaired"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
METADATA_DIR = DATA_DIR / "metadata"
EXPORTS_DIR = DATA_DIR / "exports"

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE_MB = 50


def ensure_data_directories() -> None:
    for directory in (
        RAW_DATA_DIR,
        REPAIRED_DATA_DIR,
        CLEANED_DATA_DIR,
        METADATA_DIR,
        EXPORTS_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )