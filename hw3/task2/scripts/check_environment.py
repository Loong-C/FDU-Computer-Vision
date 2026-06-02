from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hw3_calvin_act.compat import ensure_lerobot_importable


def main() -> None:
    print(f"python={sys.version.split()[0]}")
    print(f"executable={sys.executable}")
    for name in ["torch", "torchvision", "swanlab", "yaml", "numpy"]:
        module = importlib.import_module(name)
        print(f"{name}={getattr(module, '__version__', 'unknown')}")
    import torch

    print(f"cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"gpu={torch.cuda.get_device_name(0)}")
    ensure_lerobot_importable()
    import lerobot

    print(f"lerobot={getattr(lerobot, '__version__', 'checkout')}")
    for variable in ["HW3_TASK2_DATA_ROOT", "HW3_TASK2_OUTPUT_ROOT", "HF_HOME", "HF_LEROBOT_HOME", "SWANLAB_MODE"]:
        print(f"{variable}={os.getenv(variable, '<unset>')}")


if __name__ == "__main__":
    main()
