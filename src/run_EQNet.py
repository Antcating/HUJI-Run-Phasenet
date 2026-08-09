import os
import subprocess
import torch

from config import EQNET_DIR, RESULTS_PATH, PYTHON_PATH, FIBER_CHANNELS
from pathlib import Path

def run_EQNet(file_list: Path, **kwargs) -> None:

    # For future retrained model support
    model = kwargs.get("model", "phasenet_das")

    # Site specific parameters
    nt = kwargs.get("nt", 6144)
    # Smallest multiple of 1024 that is >= FIBER_CHANNELS
    nx = kwargs.get("nx", ((FIBER_CHANNELS + 1023) // 1024) * 1024)
    min_prob = kwargs.get("min_prob", 0.75)
    sampling_rate = kwargs.get("sampling_rate", 200)
    # Float16 precision to save VRAM
    amp = kwargs.get("amp", False)

    ngpu = torch.cuda.device_count()
    print(f"CUDA devices: {ngpu}")

    command = [
        str(PYTHON_PATH),
        str(EQNET_DIR / "predict.py"),
        "--model",
        model,
        "--device",
        "cuda" if ngpu > 0 else "cpu",
        "--data_list",
        str(file_list),
        "--data_path",
        r"Z:\\",
        "--result_path",
        str(RESULTS_PATH),
        "--format",
        "h5",
        "--dataset",
        "das",
        "--system",
        "huji",
        "--batch_size",
        "1",
        "--workers",
        "0",
        "--cut_patch",
        "--sampling_rate",
        str(sampling_rate),
        "" if sampling_rate != 100 else "--resample_time",
        "--nt",
        str(nt),
        "--nx",
        str(nx),
        "--min_prob",
        str(min_prob),
        "--skip_existing",
    ]

    if ngpu > 0 and amp:
        command.append("--amp")

    env = os.environ.copy()

    print("Running:")
    print(subprocess.list2cmdline(command))

    ret = subprocess.run(
        command,
        cwd=EQNET_DIR,
        env=env,
        check=True,
    )

    return ret.returncode