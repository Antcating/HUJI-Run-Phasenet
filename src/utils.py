import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from config import FILE_LIST_PATH, DATA_ROOT, PICKS_DIR, FIBER_CHANNELS

PICK_FILENAME_PATTERN = re.compile(
    r"^(?P<timestamp>\d+(?:\.\d+)?)\.csv$"
)

# Patch files produced by EQNet with --cut_patch, e.g. "1700000000_0000_0000.csv"
PATCH_FILENAME_PATTERN = re.compile(
    r"^(?P<timestamp>\d+(?:\.\d+)?)_\d{4}_\d{4}\.csv$"
)

def get_last_pick_file() -> Path | None:
    pick_files = [
        file
        for file in PICKS_DIR.glob("*.csv")
        if PICK_FILENAME_PATTERN.match(file.name)
    ]
    if pick_files:
        return max(pick_files, key=lambda file: float(file.stem))
    else:
        return None


def get_new_pick_files(last_pick_file: Path | None = None) -> list[Path]:
    last_timestamp = float(last_pick_file.stem) if last_pick_file else None

    new_files = []
    for file in PICKS_DIR.glob("*.csv"):
        if not PICK_FILENAME_PATTERN.match(file.name):
            print(f"Skipping unrecognized filename: {file.name}")
            continue

        if file.stat().st_size == 0:
            print(f"Skipping empty file: {file.name}")
            continue
        
        if pd.read_csv(file).__len__() < FIBER_CHANNELS * 0.2:
            continue

        if last_timestamp is not None and float(file.stem) <= last_timestamp:
            continue

        new_files.append(file)

    new_files.sort(key=lambda file: float(file.stem))
    return new_files


def delete_old_empty_pick_files(last_pick_file: Path | None = None) -> int:
    """Delete empty pick files, keeping one watermark for future runs.

    The most recent empty ``<timestamp>.csv`` file is preserved so it can be
    reused as ``last_pick_file`` on the next run. Empty patch files in the
    ``<timestamp>_XXXX_XXXX.csv`` format are always deleted.
    """
    empty_plain_files: list[Path] = []

    deleted = 0
    for file in PICKS_DIR.glob("*.csv"):
        if file.stat().st_size != 0:
            continue

        if PATCH_FILENAME_PATTERN.match(file.name):
            file.unlink()
            print(f"Deleted empty patch file: {file.name}")
            deleted += 1
        elif PICK_FILENAME_PATTERN.match(file.name):
            empty_plain_files.append(file)

    # Keep the most recent empty file to serve as a future watermark.
    empty_plain_files.sort(key=lambda file: float(file.stem))
    for file in empty_plain_files[:-1]:
        file.unlink()
        print(f"Deleted empty pick file: {file.name}")
        deleted += 1

    return deleted


def file_time_from_name(path: Path, local_tz: str = "Asia/Jerusalem") -> datetime | None:
    try:
        unix_timestamp = float(path.stem)
    except ValueError:
        print(f"Failed to convert filename {path.name} to timestamp")
        unix_timestamp = 0

    return datetime.fromtimestamp(
        unix_timestamp,
        tz=ZoneInfo(local_tz),
    )


def utc_day_from_name(path: Path) -> str:
    """Return the UTC calendar day label (YYYYMMDD) from a timestamp filename."""
    try:
        unix_timestamp = float(path.stem)
    except ValueError:
        print(f"Failed to convert filename {path.name} to timestamp")
        unix_timestamp = 0

    return datetime.fromtimestamp(
        unix_timestamp,
        tz=timezone.utc,
    ).strftime("%Y%m%d")


def build_file_list(
    skip_existing: bool = True,
    last_pick_file: Path | None = None,
    one_day: bool = False,
) -> tuple[int, str | None]:
    """Build the EQNet input file list.

    When ``one_day`` is True, only include files from the earliest unprocessed
    UTC calendar day (matching ``DATA_ROOT/YYYYMMDD/`` layout). Returns
    ``(num_files, day_label)`` where ``day_label`` is ``YYYYMMDD`` or None.
    """
    last_pick_time = file_time_from_name(last_pick_file) if last_pick_file else None
    files = []

    for path in DATA_ROOT.rglob("*.h5"):
        if skip_existing and last_pick_time is not None and file_time_from_name(path) <= last_pick_time:
            continue
        files.append(path)

    files.sort(
        key=lambda path: float(path.stem)
    )

    day_label = None
    if one_day and files:
        day_label = utc_day_from_name(files[0])
        files = [path for path in files if utc_day_from_name(path) == day_label]

    with FILE_LIST_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        for path in files:
            file.write(path.as_posix() + "\n")

    return len(files), day_label

