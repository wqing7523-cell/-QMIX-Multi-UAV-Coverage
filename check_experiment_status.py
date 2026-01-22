#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查实验完成状态"""
import yaml
import pandas as pd
from pathlib import Path

# 读取配置
config_file = Path("configs/envs/grid_extended.yaml")
with open(config_file, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 读取实验结果
metrics_file = Path("experiments/results/metrics.csv")
if metrics_file.exists():
    df = pd.read_csv(metrics_file)
    # 只考虑qmix算法
    df_qmix = df[df['algorithm'] == 'qmix'].copy()
else:
    df_qmix = pd.DataFrame()

# 获取配置中的实验组合
map_sizes = config.get("map_size", [])
num_uavs = config.get("num_uavs", [])
obstacle_densities = config.get("obstacle_density", [0.0])

# 处理map_size（可能是列表或单个值）
if isinstance(map_sizes, list):
    if isinstance(map_sizes[0], list):
        # 如果是嵌套列表，取第一个元素
        map_sizes = [ms[0] if isinstance(ms, list) else ms for ms in map_sizes]
else:
    map_sizes = [map_sizes]

# 处理num_uavs
if isinstance(num_uavs, list):
    pass
else:
    num_uavs = [num_uavs]

# 处理obstacle_density
if isinstance(obstacle_densities, list):
    pass
else:
    obstacle_densities = [obstacle_densities]

print("=" * 70)
print("实验完成状态检查")
print("=" * 70)
print()

print("配置的实验组合:")
print(f"  地图大小: {map_sizes}")
print(f"  UAV数量: {num_uavs}")
print(f"  障碍密度: {obstacle_densities}")
print(f"  总组合数: {len(map_sizes) * len(num_uavs) * len(obstacle_densities)}")
print()

# 生成所有应该有的组合
expected_combinations = []
for map_size in map_sizes:
    for num_uav in num_uavs:
        for obs_density in obstacle_densities:
            expected_combinations.append({
                'map_size': map_size,
                'num_uavs': num_uav,
                'obstacle_density': obs_density
            })

print("=" * 70)
print("实验完成情况")
print("=" * 70)
print()

completed = []
missing = []

for combo in expected_combinations:
    map_size = combo['map_size']
    num_uav = combo['num_uavs']
    obs_density = combo['obstacle_density']
    
    # 检查是否有结果
    if len(df_qmix) > 0:
        matches = df_qmix[
            (df_qmix['map_height'] == map_size) &
            (df_qmix['map_width'] == map_size) &
            (df_qmix['num_uavs'] == num_uav) &
            (df_qmix['obstacle_density'] == obs_density)
        ]
        
        if len(matches) > 0:
            coverage = matches.iloc[0]['coverage_mean']
            completed.append({
                'map_size': map_size,
                'num_uavs': int(num_uav),
                'obstacle_density': float(obs_density),
                'coverage': float(coverage)
            })
        else:
            missing.append(combo)
    else:
        missing.append(combo)

print(f"[OK] 已完成: {len(completed)}/{len(expected_combinations)}")
print(f"[X] 未完成: {len(missing)}/{len(expected_combinations)}")
print()

if completed:
    print("已完成的实验:")
    print("-" * 70)
    for exp in completed:
        print(f"  地图: {exp['map_size']}×{exp['map_size']}, "
              f"UAV: {exp['num_uavs']}, "
              f"障碍密度: {exp['obstacle_density']:.2f}, "
              f"覆盖率: {exp['coverage']:.3f}")
    print()

if missing:
    print("未完成的实验:")
    print("-" * 70)
    for exp in missing:
        print(f"  地图: {exp['map_size']}×{exp['map_size']}, "
              f"UAV: {exp['num_uavs']}, "
              f"障碍密度: {exp['obstacle_density']:.2f}")
    print()
else:
    print("[SUCCESS] 所有实验均已完成！")
    print()

# 统计信息
if completed:
    print("=" * 70)
    print("实验结果统计")
    print("=" * 70)
    print()
    
    # 按障碍密度统计
    print("按障碍密度统计:")
    for obs_d in obstacle_densities:
        exp_obs = [e for e in completed if abs(e['obstacle_density'] - obs_d) < 0.001]
        if exp_obs:
            avg_cov = sum(e['coverage'] for e in exp_obs) / len(exp_obs)
            print(f"  障碍密度 {obs_d:.2f}: {len(exp_obs)} 个实验, 平均覆盖率: {avg_cov:.3f}")
    print()
    
    # 按地图大小统计
    print("按地图大小统计:")
    for map_s in map_sizes:
        exp_map = [e for e in completed if e['map_size'] == map_s]
        if exp_map:
            avg_cov = sum(e['coverage'] for e in exp_map) / len(exp_map)
            print(f"  地图 {map_s}×{map_s}: {len(exp_map)} 个实验, 平均覆盖率: {avg_cov:.3f}")
    print()
    
    # 按UAV数量统计
    print("按UAV数量统计:")
    for num_u in num_uavs:
        exp_uav = [e for e in completed if e['num_uavs'] == num_u]
        if exp_uav:
            avg_cov = sum(e['coverage'] for e in exp_uav) / len(exp_uav)
            print(f"  {num_u} 架UAV: {len(exp_uav)} 个实验, 平均覆盖率: {avg_cov:.3f}")

