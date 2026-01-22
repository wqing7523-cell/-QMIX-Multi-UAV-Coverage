#!/usr/bin/env python
"""Extract metrics from training logs into a CSV summary."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

START_PATTERNS = [
    re.compile(
        r"Training\s+(?P<algo>Q-Learning)\s+\((?P<variant>[^)]+)\)\s+on\s+map=\((?P<map_h>\d+),\s*(?P<map_w>\d+)\),\s+num_uavs=(?P<num_uavs>\d+),\s+obstacle_density=(?P<obstacle>[-+]?[0-9]*\.?[0-9]+)"
    ),
    re.compile(
        r"Training\s+(?P<algo>QMIX)\s+on\s+map=\((?P<map_h>\d+),\s*(?P<map_w>\d+)\),\s+num_uavs=(?P<num_uavs>\d+),\s+obstacle_density=(?P<obstacle>[-+]?[0-9]*\.?[0-9]+)"
    ),
]

FINISH_PATTERN = re.compile(
    r"Training finished \| coverage_mean=(?P<coverage>[0-9.]+) \| pa_mean=(?P<pa>[0-9.]+) \| steps_mean=(?P<steps>[0-9.]+)"
)


def parse_log_file(log_path: Path) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            for pattern in START_PATTERNS:
                match = pattern.search(line)
                if match:
                    groups = match.groupdict()
                    current = {
                        "algorithm": groups.get("algo", "").lower(),
                        "variant": groups.get("variant", "global").lower(),
                        "map_height": groups.get("map_h", ""),
                        "map_width": groups.get("map_w", ""),
                        "num_uavs": groups.get("num_uavs", ""),
                        "obstacle_density": groups.get("obstacle", ""),
                        "log_file": str(log_path.relative_to(log_path.parents[1])),
                    }
                    break
            else:
                if current:
                    finish_match = FINISH_PATTERN.search(line)
                    if finish_match:
                        current.update(
                            {
                                "coverage_mean": finish_match.group("coverage"),
                                "pa_mean": finish_match.group("pa"),
                                "steps_mean": finish_match.group("steps"),
                            }
                        )
                        results.append(current)
                        current = None
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract metrics from logs")
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("experiments/logs"),
        help="Directory containing log files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/results/metrics.csv"),
        help="Output CSV file",
    )
    args = parser.parse_args()

    logs_dir: Path = args.logs_dir
    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, str]] = []
    for log_path in sorted(logs_dir.glob("*.log")):
        rows.extend(parse_log_file(log_path))

    if not rows:
        print("No metrics found in logs directory", logs_dir)
        return

    fieldnames = [
        "algorithm",
        "variant",
        "map_height",
        "map_width",
        "num_uavs",
        "obstacle_density",
        "coverage_mean",
        "pa_mean",
        "steps_mean",
        "log_file",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} entries to {output_path}")


if __name__ == "__main__":
    main()
