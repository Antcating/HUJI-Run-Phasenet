from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

from config import DATA_ROOT, OUTPUT_DIR, FIBER_NAME


@dataclass
class EventPlot:
    image_path: Path
    num_picks: int
    event_time: datetime


def plot_event(
    phasenet_picks_csv: Path,
    local_tz: str = "Asia/Jerusalem",
    dataset_name: str = "data_down",
    channel_start: int | None = None,
    channel_end: int | None = None,
    lowcut_hz: float = 2.0,
    highcut_hz: float = 12.0,
    eqnet_sampling_rate: float = 100.0,
    output_dir: Path = OUTPUT_DIR,
) -> EventPlot:
    """
    Plot a single event from the DAS data.
    """
    timestamp = float(phasenet_picks_csv.stem)
    utc_start = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    local_start = utc_start.astimezone(ZoneInfo(local_tz))

    hdf5_path = (
        DATA_ROOT / utc_start.strftime("%Y%m%d") / f"{phasenet_picks_csv.stem}.h5"
    )

    if not hdf5_path.exists():
        # Handle insignificant timestamp-format differences, such as
        # 1784759139.790 versus 1784759139.79.
        day_directory = hdf5_path.parent

        if day_directory.exists():
            for candidate in day_directory.glob("*.h5"):
                try:
                    if abs(float(candidate.stem) - timestamp) < 0.001:
                        hdf5_path = candidate
                        break
                except ValueError:
                    continue

    if not hdf5_path.exists():
        raise FileNotFoundError(
            f"Could not find HDF5 file for {phasenet_picks_csv.name} under {DATA_ROOT}"
        )

    picks = pd.read_csv(phasenet_picks_csv)

    required_columns = {
        "channel_index",
        "phase_index",
        "phase_type",
    }
    missing_columns = required_columns.difference(picks.columns)

    if missing_columns:
        raise ValueError(f"Missing CSV columns: {sorted(missing_columns)}")

    picks = picks.copy()
    picks["channel_index"] = pd.to_numeric(
        picks["channel_index"],
        errors="coerce",
    )
    picks["phase_index"] = pd.to_numeric(
        picks["phase_index"],
        errors="coerce",
    )

    picks = picks.dropna(subset=["channel_index", "phase_index", "phase_type"])

    picks["channel_index"] = picks["channel_index"].astype(int)
    picks["time_s"] = picks["phase_index"] / eqnet_sampling_rate

    with h5py.File(hdf5_path, "r") as h5:
        if dataset_name not in h5:
            raise KeyError(
                f"{hdf5_path} does not contain {dataset_name!r}; "
                f"available datasets: {list(h5.keys())}"
            )

        dataset = h5[dataset_name]

        if dataset.ndim != 2:
            raise ValueError(f"Expected 2-D DAS data, found shape {dataset.shape}")

        if channel_start is None:
            channel_start = 0
        if channel_end is None:
            channel_end = dataset.shape[0]

        data = dataset[channel_start:channel_end, :].astype(
            np.float32,
            copy=False,
        )

        raw_sampling_rate = h5.attrs["SPS_down"]

    sos = butter(
        4,
        [lowcut_hz, highcut_hz],
        btype="bandpass",
        fs=raw_sampling_rate,
        output="sos",
    )

    data = sosfiltfilt(
        sos,
        data,
        axis=-1,
    ).astype(np.float32, copy=False)

    # Remove the spatially constant component.
    data -= np.mean(
        data,
        axis=0,
        keepdims=True,
        dtype=np.float32,
    )

    duration_s = data.shape[1] / raw_sampling_rate
    last_channel = channel_start + data.shape[0] - 1

    visible_picks = picks[
        picks["time_s"].between(0, duration_s)
        & picks["channel_index"].between(channel_start, last_channel)
    ]

    finite_data = data[np.isfinite(data)]

    if finite_data.size == 0:
        raise ValueError("DAS data contains no finite values")

    amplitude_limit = np.nanstd(finite_data) / 10.0

    if not np.isfinite(amplitude_limit) or amplitude_limit <= 0:
        amplitude_limit = np.nanpercentile(
            np.abs(finite_data),
            99,
        )

    if not np.isfinite(amplitude_limit) or amplitude_limit <= 0:
        amplitude_limit = 1.0

    fig, ax = plt.subplots(figsize=(16, 9))

    image = ax.imshow(
        data,
        aspect="auto",
        cmap="seismic",
        vmin=-amplitude_limit,
        vmax=amplitude_limit,
        interpolation="nearest",
        origin="upper",
        extent=[
            0,
            duration_s,
            last_channel + 0.5,
            channel_start - 0.5,
        ],
    )

    for phase_type, phase_picks in visible_picks.groupby("phase_type"):
        ax.scatter(
            phase_picks["time_s"],
            phase_picks["channel_index"],
            s=10,
            marker=".",
            linewidths=0,
            alpha=0.9,
            rasterized=True,
            label=f"{str(phase_type).upper()} picks",
        )

    ax.set_title(
        f"{FIBER_NAME} | "
        f"{local_start:%Y-%m-%d %H:%M:%S.%f} "
        f"{local_start.tzname()} | "
        f"{len(visible_picks):,} picks"
    )
    ax.set_xlabel("Time from file start [s]")
    ax.set_ylabel("Channel")

    if not visible_picks.empty:
        ax.legend(loc="upper right", markerscale=2)

    colorbar = fig.colorbar(image, ax=ax, pad=0.015)
    colorbar.set_label("Filtered amplitude")

    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{phasenet_picks_csv.stem}.png"

    fig.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)

    return EventPlot(
        image_path=output_path,
        num_picks=len(visible_picks),
        event_time=local_start,
    )
