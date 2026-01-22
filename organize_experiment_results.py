#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""整理实验结果和对比数据，生成论文所需的数据表格"""
import pandas as pd
from pathlib import Path

# 读取数据
df = pd.read_csv('experiments/results/metrics.csv')
df_qmix = df[df['algorithm'] == 'qmix'].copy()
df_qmix_extended = df_qmix[
    (df_qmix['map_height'].isin([12, 16, 24])) &
    (df_qmix['num_uavs'].isin([4, 6])) &
    (df_qmix['obstacle_density'].isin([0.0, 0.05, 0.10, 0.20]))
].copy()

# 整理grid_extended的24个实验
print("=" * 70)
print("grid_extended实验结果整理")
print("=" * 70)
print()

# 按障碍密度、地图大小、UAV数量分组
results_table = []
for obs_d in [0.0, 0.05, 0.10, 0.20]:
    for map_size in [12, 16, 24]:
        for num_uav in [4, 6]:
            subset = df_qmix_extended[
                (df_qmix_extended['obstacle_density'] == obs_d) &
                (df_qmix_extended['map_height'] == map_size) &
                (df_qmix_extended['num_uavs'] == num_uav)
            ]
            if len(subset) > 0:
                row = subset.iloc[0]
                results_table.append({
                    'Map Size': f'{map_size}×{map_size}',
                    'UAVs': num_uav,
                    'Obstacle Density': f'{obs_d:.2f}',
                    'Coverage': f"{row['coverage_mean']:.3f}",
                    'PA': f"{row['pa_mean']:.3f}",
                    'Steps': f"{row['steps_mean']:.1f}",
                })

results_df = pd.DataFrame(results_table)
print("完整实验结果表（24个实验）:")
print(results_df.to_string(index=False))
print()

# 保存为CSV
results_df.to_csv('experiments/results/paper_results_table.csv', index=False)
print("结果表已保存到: experiments/results/paper_results_table.csv")
print()

# 按障碍密度统计
print("=" * 70)
print("按障碍密度统计")
print("=" * 70)
print()

for obs_d in [0.0, 0.05, 0.10, 0.20]:
    subset = df_qmix_extended[df_qmix_extended['obstacle_density'] == obs_d]
    if len(subset) > 0:
        avg_cov = subset['coverage_mean'].mean()
        min_cov = subset['coverage_mean'].min()
        max_cov = subset['coverage_mean'].max()
        print(f"障碍密度 {obs_d:.2f}: 平均={avg_cov:.3f}, 最小={min_cov:.3f}, 最大={max_cov:.3f}, 样本数={len(subset)}")
print()

# 按地图大小统计
print("=" * 70)
print("按地图大小统计")
print("=" * 70)
print()

for map_size in [12, 16, 24]:
    subset = df_qmix_extended[df_qmix_extended['map_height'] == map_size]
    if len(subset) > 0:
        avg_cov = subset['coverage_mean'].mean()
        min_cov = subset['coverage_mean'].min()
        max_cov = subset['coverage_mean'].max()
        print(f"地图 {map_size}×{map_size}: 平均={avg_cov:.3f}, 最小={min_cov:.3f}, 最大={max_cov:.3f}, 样本数={len(subset)}")
print()

# 按UAV数量统计
print("=" * 70)
print("按UAV数量统计")
print("=" * 70)
print()

for num_uav in [4, 6]:
    subset = df_qmix_extended[df_qmix_extended['num_uavs'] == num_uav]
    if len(subset) > 0:
        avg_cov = subset['coverage_mean'].mean()
        min_cov = subset['coverage_mean'].min()
        max_cov = subset['coverage_mean'].max()
        print(f"{num_uav} 架UAV: 平均={avg_cov:.3f}, 最小={min_cov:.3f}, 最大={max_cov:.3f}, 样本数={len(subset)}")
print()

# 对比数据：QMIX vs Q-Learning（小规模场景）
print("=" * 70)
print("QMIX vs Q-Learning对比（小规模场景，8×8地图）")
print("=" * 70)
print()

df_small = df[df['map_height'] == 8].copy()
comparison_table = []
for obs_d in [0.0, 0.10]:
    for num_uav in [1, 2, 3]:
        qmix_subset = df_small[
            (df_small['algorithm'] == 'qmix') &
            (df_small['obstacle_density'] == obs_d) &
            (df_small['num_uavs'] == num_uav)
        ]
        ql_subset = df_small[
            (df_small['algorithm'] == 'q-learning') &
            (df_small['obstacle_density'] == obs_d) &
            (df_small['num_uavs'] == num_uav) &
            (df_small['variant'] == 'global')
        ]
        
        if len(qmix_subset) > 0 and len(ql_subset) > 0:
            qmix_cov = qmix_subset['coverage_mean'].mean()
            ql_cov = ql_subset['coverage_mean'].mean()
            comparison_table.append({
                'Obstacle Density': f'{obs_d:.2f}',
                'UAVs': num_uav,
                'Q-Learning': f'{ql_cov:.3f}',
                'QMIX': f'{qmix_cov:.3f}',
                'Difference': f'{qmix_cov - ql_cov:+.3f}',
            })

if comparison_table:
    comparison_df = pd.DataFrame(comparison_table)
    print(comparison_df.to_string(index=False))
    comparison_df.to_csv('experiments/results/qmix_vs_qlearning_comparison.csv', index=False)
    print("\n对比表已保存到: experiments/results/qmix_vs_qlearning_comparison.csv")
print()

# 高障碍密度详细结果
print("=" * 70)
print("高障碍密度(0.20)详细结果")
print("=" * 70)
print()

df_high = df_qmix_extended[df_qmix_extended['obstacle_density'] == 0.20].copy()
df_high_sorted = df_high.sort_values(['map_height', 'num_uavs'])
high_obs_table = []
for _, row in df_high_sorted.iterrows():
    high_obs_table.append({
        'Map Size': f"{int(row['map_height'])}×{int(row['map_width'])}",
        'UAVs': int(row['num_uavs']),
        'Coverage': f"{row['coverage_mean']:.3f}",
        'PA': f"{row['pa_mean']:.3f}",
        'Steps': f"{row['steps_mean']:.1f}",
    })

high_obs_df = pd.DataFrame(high_obs_table)
print(high_obs_df.to_string(index=False))
high_obs_df.to_csv('experiments/results/high_obstacle_density_results.csv', index=False)
print("\n高障碍密度结果已保存到: experiments/results/high_obstacle_density_results.csv")

