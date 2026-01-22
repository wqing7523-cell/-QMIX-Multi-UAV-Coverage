#!/usr/bin/env python
"""Generate summary plots from metrics CSV."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid")


def load_metrics(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["map_size"] = df["map_height"].astype(int)
    df["num_uavs"] = df["num_uavs"].astype(int)
    df["obstacle_density"] = df["obstacle_density"].astype(float)
    df["coverage_mean"] = df["coverage_mean"].astype(float)
    df["pa_mean"] = df["pa_mean"].astype(float)
    df["steps_mean"] = df["steps_mean"].astype(float)
    df["variant"] = df["variant"].fillna("global")
    return df


def plot_metric(
    df: pd.DataFrame,
    metric: str,
    output_dir: Path,
    title_suffix: str = "",
    filename_suffix: str = "",
) -> None:
    if df.empty:
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    ylabel = metric.replace("_", " ").title()
    suffix_title = f" {title_suffix}" if title_suffix else ""
    suffix_file = filename_suffix if filename_suffix else ""

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df,
        x="map_size",
        y=metric,
        hue="algorithm",
        errorbar="sd",
    )
    plt.title(f"{metric} vs Map Size{suffix_title}")
    plt.xlabel("Map Size (grid dimension)")
    plt.ylabel(ylabel)
    plt.legend(title="Algorithm")
    output_path = output_dir / f"{metric}_vs_map_size{suffix_file}.png"
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df,
        x="num_uavs",
        y=metric,
        hue="algorithm",
        errorbar="sd",
    )
    plt.title(f"{metric} vs Number of UAVs{suffix_title}")
    plt.xlabel("Number of UAVs")
    plt.ylabel(ylabel)
    plt.legend(title="Algorithm")
    output_path = output_dir / f"{metric}_vs_uavs{suffix_file}.png"
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def sanitize_label(value) -> str:
    text = str(value).strip()
    return text.replace(" ", "_").replace("/", "-")


def add_subsets_by_obstacle(df: pd.DataFrame) -> List[Tuple[pd.DataFrame, str, str]]:
    subsets = []
    for obstacle in sorted(df["obstacle_density"].unique()):
        subset = df[df["obstacle_density"] == obstacle]
        label = f"obstacle={obstacle:.2f}"
        file_suffix = f"_obstacle_{obstacle:.2f}"
        subsets.append((subset, label, file_suffix))
    return subsets


def add_subsets_by_variant(df: pd.DataFrame) -> List[Tuple[pd.DataFrame, str, str]]:
    subsets = []
    variants = sorted(df["variant"].unique())
    if len(variants) <= 1:
        return []
    for variant in variants:
        subset = df[df["variant"] == variant]
        label = f"variant={variant}"
        file_suffix = f"_variant_{sanitize_label(variant)}"
        subsets.append((subset, label, file_suffix))
    return subsets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate plots from metrics.csv")
    parser.add_argument("--metrics", type=Path, default=Path("experiments/results/metrics.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/results/plots"))
    parser.add_argument("--obstacle", type=float, default=None, help="Filter by obstacle density")
    parser.add_argument("--split-obstacle", action="store_true", help="Generate plots per obstacle density")
    parser.add_argument("--split-variant", action="store_true", help="Generate plots per network variant")
    args = parser.parse_args()

    df = load_metrics(args.metrics)

    subsets: List[Tuple[pd.DataFrame, str, str]] = []

    if args.obstacle is not None:
        df = df[df["obstacle_density"] == args.obstacle]
        subsets.append((df, f"obstacle={args.obstacle:.2f}", f"_obstacle_{args.obstacle:.2f}"))
    elif args.split_obstacle:
        subsets.extend(add_subsets_by_obstacle(df))
    else:
        subsets.append((df, "", ""))

    final_subsets: List[Tuple[pd.DataFrame, str, str, Path]] = []
    for subset_df, label, file_suffix in subsets:
        if args.split_variant:
            variant_subsets = add_subsets_by_variant(subset_df)
            if not variant_subsets:
                variant_subsets = [(subset_df, "", "")]
            for v_df, v_label, v_suffix in variant_subsets:
                combined_label = " ".join(filter(None, [label, v_label]))
                combined_suffix = f"{file_suffix}{v_suffix}"
                out_dir = args.output_dir / sanitize_label(combined_label) if combined_label else args.output_dir
                final_subsets.append((v_df, combined_label, combined_suffix, out_dir))
        else:
            out_dir = args.output_dir / sanitize_label(label) if label else args.output_dir
            final_subsets.append((subset_df, label, file_suffix, out_dir))

    for data, label, suffix, out_dir in final_subsets:
        title_suffix = f"({label})" if label else ""
        for metric in ["coverage_mean", "pa_mean", "steps_mean"]:
            plot_metric(data, metric, out_dir, title_suffix=title_suffix, filename_suffix=suffix)

    print(f"Plots saved to {args.output_dir}")


if __name__ == "__main__":
    main()
