from __future__ import annotations

import csv
import os
import warnings
from pathlib import Path
from typing import Any


class ExperimentTracker:
    def __init__(
        self,
        *,
        run_dir: str | Path,
        project: str,
        experiment_name: str,
        config: dict[str, Any],
        mode: str | None = None,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_path = self.run_dir / "metrics.csv"
        self._fieldnames: list[str] = ["step"]
        self._rows: list[dict[str, Any]] = []
        if self.metrics_path.exists():
            with self.metrics_path.open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                self._fieldnames = reader.fieldnames or self._fieldnames
                self._rows = list(reader)
        self._swanlab = None
        self._run = None
        try:
            import swanlab

            self._swanlab = swanlab
            default_logdir = Path(__file__).resolve().parents[2] / "swanlog"
            logdir = os.getenv("SWANLAB_LOG_DIR", str(default_logdir))
            swanlab_mode = os.getenv("SWANLAB_MODE", mode or "offline")
            try:
                self._run = swanlab.init(
                    project=project,
                    experiment_name=experiment_name,
                    config=config,
                    logdir=logdir,
                    mode=swanlab_mode,
                )
            except Exception as error:
                warnings.warn(f"SwanLab {swanlab_mode=} failed ({error}); falling back to offline mode.")
                self._run = swanlab.init(
                    project=project,
                    experiment_name=experiment_name,
                    config=config,
                    logdir=logdir,
                    mode="offline",
                )
        except ImportError:
            warnings.warn("SwanLab is not installed. Metrics will still be written to metrics.csv.")

    def log(self, metrics: dict[str, Any], step: int) -> None:
        row = {"step": step, **metrics}
        self._rows.append(row)
        for field in row:
            if field not in self._fieldnames:
                self._fieldnames.append(field)
        self._rewrite_csv()
        if self._swanlab is not None:
            self._swanlab.log(metrics, step=step)

    def _rewrite_csv(self) -> None:
        with self.metrics_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self._fieldnames)
            writer.writeheader()
            writer.writerows(self._rows)

    def finish(self) -> None:
        if self._swanlab is not None:
            self._swanlab.finish()
