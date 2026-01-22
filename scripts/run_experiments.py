#!/usr/bin/env python
import argparse
import subprocess
import sys
from pathlib import Path

import yaml

DEFAULT_MAPS = [
    ("grid_small", [0, 1, 2, 3, 4]),
    ("grid_obstacle", [0, 1, 2, 3, 4]),
    ("grid_extended", [0, 1, 2, 3]),
]
DEFAULT_UAV_INDICES = [0, 1, 2]
DEFAULT_ALGOS = ["qlearning", "qlearning_per", "qmix"]

ALGOS_CONFIGS = {
    "qlearning": ("src.algos.qlearning.train_qlearning", "configs/algos/qlearning.yaml"),
    "qlearning_per": ("src.algos.qlearning.train_qlearning", "configs/algos/qlearning_per_uav.yaml"),
    "qmix": ("src.algos.qmix.train_qmix", "configs/algos/qmix.yaml"),
    "qmix_obstacle": ("src.algos.qmix.train_qmix", "configs/algos/qmix_obstacle.yaml"),
    "qmix_long": ("src.algos.qmix.train_qmix", "configs/algos/qmix_long.yaml"),
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run experiment grid")
    parser.add_argument("--base-config", default="configs/base.yaml")
    parser.add_argument("--maps", nargs="*", default=[item[0] for item in DEFAULT_MAPS])
    parser.add_argument("--map-indices", nargs="*", type=int, default=None)
    parser.add_argument("--uav-indices", nargs="*", type=int, default=DEFAULT_UAV_INDICES)
    parser.add_argument("--algorithms", nargs="*", default=DEFAULT_ALGOS)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--obstacle-indices", nargs="*", type=int, default=None)
    parser.add_argument("--init-checkpoint", type=str, default=None)
    return parser.parse_args()


def run_command(cmd):
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
    print("-")


def main():
    args = parse_args()
    venv_python = Path('.venv') / 'Scripts' / 'python.exe'
    if not venv_python.exists():
        print("Virtual environment python not found at", venv_python)
        sys.exit(1)

    base_config = args.base_config

    map_settings = []
    if args.maps:
        for map_name in args.maps:
            defaults = next((indices for name, indices in DEFAULT_MAPS if name == map_name), None)
            map_indices = args.map_indices if args.map_indices is not None else defaults or [0]
            map_settings.append((map_name, map_indices))
    else:
        map_settings = DEFAULT_MAPS

    for map_name, map_indices in map_settings:
        env_config = f"configs/envs/{map_name}.yaml"
        with open(env_config, "r", encoding="utf-8") as f:
            env_data = yaml.safe_load(f)
        obstacle_density = env_data.get("obstacle_density", [0.0])
        if isinstance(obstacle_density, list):
            density_list = obstacle_density
        else:
            density_list = [obstacle_density]
        if args.obstacle_indices is not None:
            obstacle_indices = [idx for idx in args.obstacle_indices if 0 <= idx < len(density_list)]
        else:
            obstacle_indices = [0]
        if not obstacle_indices:
            print(f"No valid obstacle indices for {map_name}, skipping")
            continue
        for algo in args.algorithms:
            module, algo_config = ALGOS_CONFIGS.get(algo, (None, None))
            if module is None:
                print(f"Unknown algorithm {algo}, skipping")
                continue
            for map_idx in map_indices:
                for obs_idx in obstacle_indices:
                    for uav_idx in args.uav_indices:
                        cmd = [
                        str(venv_python),
                        "-m",
                        module,
                        "--base-config", base_config,
                        "--env-config", env_config,
                        "--algo-config", algo_config,
                        "--seed", str(args.seed),
                        "--map-index", str(map_idx),
                        "--uav-index", str(uav_idx),
                        "--obstacle-index", str(obs_idx),
                    ]
                        
                        # Curriculum learning: use checkpoint from lower obstacle density
                        checkpoint_path = None
                        if args.init_checkpoint:
                            checkpoint_path = args.init_checkpoint
                        elif obs_idx > 0:  # For obstacle density > 0, try to use previous density checkpoint
                            # Try to find checkpoint from previous obstacle density
                            prev_obs_idx = obs_idx - 1
                            if prev_obs_idx >= 0:
                                checkpoint_dir = Path("experiments/checkpoints")
                                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Get map size and UAV count
                                map_sizes = env_data.get("map_size", [])
                                if isinstance(map_sizes, list) and map_idx < len(map_sizes):
                                    map_size_val = map_sizes[map_idx]
                                    if isinstance(map_size_val, list):
                                        map_size_val = map_size_val[0]
                                else:
                                    map_size_val = map_idx
                                
                                uav_counts = env_data.get("num_uavs", [])
                                if isinstance(uav_counts, list) and uav_idx < len(uav_counts):
                                    uav_count = uav_counts[uav_idx]
                                else:
                                    uav_count = uav_idx
                                
                                prev_obs_density = density_list[prev_obs_idx]
                                # Format obstacle density for filename matching (e.g., "obs005" for 0.05)
                                prev_obs_str = f"obs{prev_obs_density:.2f}".replace(".", "")
                                
                                # Look for checkpoint with pattern: qmix_map{map_size}_uavs{uav_count}_obs{prev_density}_*.pt
                                checkpoint_pattern = f"qmix_map{map_size_val}_uavs{uav_count}_{prev_obs_str}_*.pt"
                                checkpoints = list(checkpoint_dir.glob(checkpoint_pattern))
                                
                                # Sort by modification time, get most recent
                                if checkpoints:
                                    checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                    checkpoint_path = str(checkpoints[0])
                                    print(f"Curriculum learning: Loading checkpoint from previous obstacle density {prev_obs_density:.2f}: {checkpoint_path}")
                        
                        if checkpoint_path:
                            cmd.extend(["--init-checkpoint", checkpoint_path])
                        
                        run_command(cmd)


if __name__ == "__main__":
    main()
