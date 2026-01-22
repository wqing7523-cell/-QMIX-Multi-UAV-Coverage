import csv
from collections import defaultdict

# Read metrics
with open('experiments/results/metrics.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Stage 1 (no obstacles)
stage1 = [r for r in rows if r['algorithm'] == 'qmix' and r['map_height'] in ['12', '16', '24'] and float(r['obstacle_density']) == 0]
print('=== Stage 1 Results (no obstacles) ===')
print(f'Total experiments: {len(stage1)}')
print('\nBy configuration:')
stage1_by_config = defaultdict(list)
for r in stage1:
    key = f"Map {r['map_height']}x{r['map_width']}, UAVs: {r['num_uavs']}"
    stage1_by_config[key].append(float(r['coverage_mean']))
for key, covs in sorted(stage1_by_config.items()):
    print(f"{key}: Coverage={sum(covs)/len(covs):.3f} (n={len(covs)})")

# Stage 2 (with obstacles)
stage2 = [r for r in rows if r['algorithm'] == 'qmix' and r['map_height'] in ['12', '16', '24'] and float(r['obstacle_density']) > 0]
print('\n=== Stage 2 Results (with obstacles) ===')
print(f'Total experiments: {len(stage2)}')
print('\nBy configuration:')
stage2_by_config = defaultdict(list)
for r in stage2:
    key = f"Map {r['map_height']}x{r['map_width']}, UAVs: {r['num_uavs']}, Obstacle: {r['obstacle_density']}"
    stage2_by_config[key].append(float(r['coverage_mean']))
for key, covs in sorted(stage2_by_config.items()):
    print(f"{key}: Coverage={sum(covs)/len(covs):.3f} (n={len(covs)})")

# Latest results
print('\n=== Latest 10 Stage 2 Results ===')
for r in stage2[-10:]:
    print(f"Map {r['map_height']}x{r['map_width']}, UAVs: {r['num_uavs']}, Obstacle: {r['obstacle_density']}, Coverage: {r['coverage_mean']}, Steps: {r['steps_mean']}")

