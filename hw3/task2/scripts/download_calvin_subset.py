from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hw3_calvin_act.remote_subset import default_cache_root, default_output_root, download_archive_subset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download small official CALVIN frame windows with HTTP Range requests."
    )
    parser.add_argument("--archive", choices=["ABC", "D", "ALL"], default="ALL")
    parser.add_argument("--output-root", type=Path, default=default_output_root())
    parser.add_argument("--cache-root", type=Path, default=default_cache_root())
    parser.add_argument("--windows-per-env", type=int, default=4)
    parser.add_argument("--window-size", type=int, default=24)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--index-only", action="store_true")
    args = parser.parse_args()

    archives = ["ABC", "D"] if args.archive == "ALL" else [args.archive]
    summaries = []
    for archive in archives:
        summary = download_archive_subset(
            archive=archive,
            output_root=args.output_root,
            cache_root=args.cache_root,
            windows_per_env=args.windows_per_env,
            window_size=args.window_size,
            workers=args.workers,
            index_only=args.index_only,
        )
        summaries.append(summary)
        print(json.dumps(summary, indent=2))
    print(f"Completed {len(summaries)} CALVIN subset archive(s).")


if __name__ == "__main__":
    main()
