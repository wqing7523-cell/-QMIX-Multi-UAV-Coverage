#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有Stage 2实验的完成情况"""
import csv
from pathlib import Path

metrics_file = Path("experiments/results/metrics.csv")
if not metrics_file.exists():
    print("metrics.csv 文件不存在")
    exit(1)

# 读取所有实验结果
with open(metrics_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Stage 2 实验（有障碍）
stage2_experiments = []
for r in rows:
    if (r['algorithm'] == 'qmix' and 
        r['map_height'] in ['12', '16', '24'] and 
        float(r['obstacle_density']) > 0):
        stage2_experiments.append({
            'map': f"{r['map_height']}x{r['map_width']}",
            'uavs': int(r['num_uavs']),
            'obstacle': float(r['obstacle_density']),
            'coverage': float(r['coverage_mean']),
            'steps': float(r['steps_mean'])
        })

# 预期的实验配置
expected_configs = [
    # 12x12
    (12, 4, 0.05), (12, 4, 0.10), (12, 4, 0.20),
    (12, 6, 0.05), (12, 6, 0.10), (12, 6, 0.20),
    # 16x16
    (16, 4, 0.05), (16, 4, 0.10), (16, 4, 0.20),
    (16, 6, 0.05), (16, 6, 0.10), (16, 6, 0.20),
    # 24x24
    (24, 4, 0.05), (24, 4, 0.10), (24, 4, 0.20),
    (24, 6, 0.05), (24, 6, 0.10), (24, 6, 0.20),
]

print("=" * 80)
print("Stage 2 实验完成情况检查")
print("=" * 80)
print()

# 检查每个配置
completed = []
missing = []

for map_size, num_uavs, obstacle_density in expected_configs:
    found = [e for e in stage2_experiments if 
             e['map'] == f"{map_size}x{map_size}" and 
             e['uavs'] == num_uavs and 
             abs(e['obstacle'] - obstacle_density) < 0.001]
    
    if found:
        exp = found[0]
        completed.append({
            'config': f"{map_size}x{map_size}, {num_uavs} UAVs, 障碍密度 {obstacle_density}",
            'coverage': exp['coverage'],
            'steps': exp['steps']
        })
    else:
        missing.append(f"{map_size}x{map_size}, {num_uavs} UAVs, 障碍密度 {obstacle_density}")

print(f"已完成实验: {len(completed)}/{len(expected_configs)}")
print()
print("已完成的实验:")
print("-" * 80)
for exp in sorted(completed, key=lambda x: x['config']):
    print(f"{exp['config']:40s} | 覆盖率: {exp['coverage']:.3f} | 步数: {exp['steps']:.1f}")

if missing:
    print()
    print("缺失的实验:")
    print("-" * 80)
    for config in missing:
        print(f"  - {config}")
else:
    print()
    print("=" * 80)
    print("✅ 所有 Stage 2 实验已完成！")
    print("=" * 80)

print()

