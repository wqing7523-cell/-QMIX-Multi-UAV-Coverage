#!/usr/bin/env python
import pandas as pd
from pathlib import Path

CSV_PATH = Path('experiments/results/metrics.csv')
OUTPUT_PATH = Path('experiments/results/summary_qmix_vs_qlearning.csv')

if not CSV_PATH.exists():
    raise SystemExit(f'Metrics file not found: {CSV_PATH}')

df = pd.read_csv(CSV_PATH)

mask = (df['map_height'] >= 8) & (df['map_width'] >= 8)
filtered = df[mask].copy()
if filtered.empty:
    raise SystemExit('No entries with map size >= 8 found.')

pivot = (
    filtered.groupby(
        ['obstacle_density', 'map_height', 'num_uavs', 'algorithm', 'variant'],
        dropna=False
    )[['coverage_mean', 'pa_mean', 'steps_mean']]
    .mean()
    .reset_index()
    .sort_values(['obstacle_density', 'map_height', 'num_uavs', 'algorithm', 'variant'])
)

pivot.to_csv(OUTPUT_PATH, index=False)
print(f'Summary written to {OUTPUT_PATH}')
print(pivot.to_string(index=False))
