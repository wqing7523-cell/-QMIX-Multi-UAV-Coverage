#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查所有已完成的实验"""
import pandas as pd
from pathlib import Path

df = pd.read_csv('experiments/results/metrics.csv')

print("=" * 70)
print("所有实验结果统计")
print("=" * 70)
print()

print(f"总记录数: {len(df)}")
print()

print("按算法分组:")
print(df['algorithm'].value_counts())
print()

print("=" * 70)
print("QMIX实验详情")
print("=" * 70)
print()

df_qmix = df[df['algorithm'] == 'qmix']
print(f"QMIX总记录数: {len(df_qmix)}")
print()

print("所有QMIX实验组合 (地图大小, UAV数量, 障碍密度):")
combos = df_qmix.groupby(['map_height', 'map_width', 'num_uavs', 'obstacle_density']).size().reset_index(name='count')
combos = combos.sort_values(['map_height', 'num_uavs', 'obstacle_density'])
for _, row in combos.iterrows():
    print(f"  {int(row['map_height'])}x{int(row['map_width'])}, {int(row['num_uavs'])} UAV, 障碍密度 {row['obstacle_density']:.2f}: {int(row['count'])} 条记录")
print()

print("=" * 70)
print("Q-Learning实验详情")
print("=" * 70)
print()

df_ql = df[df['algorithm'] == 'q-learning']
print(f"Q-Learning总记录数: {len(df_ql)}")
print()

if len(df_ql) > 0:
    print("所有Q-Learning实验组合 (地图大小, UAV数量, 障碍密度):")
    combos_ql = df_ql.groupby(['map_height', 'map_width', 'num_uavs', 'obstacle_density']).size().reset_index(name='count')
    combos_ql = combos_ql.sort_values(['map_height', 'num_uavs', 'obstacle_density'])
    for _, row in combos_ql.iterrows():
        print(f"  {int(row['map_height'])}x{int(row['map_width'])}, {int(row['num_uavs'])} UAV, 障碍密度 {row['obstacle_density']:.2f}: {int(row['count'])} 条记录")
    print()

print("=" * 70)
print("实验配置对比")
print("=" * 70)
print()

print("grid_extended配置 (目标实验):")
print("  地图大小: [12, 16, 24]")
print("  UAV数量: [4, 6]")
print("  障碍密度: [0.0, 0.05, 0.10, 0.20]")
print("  总组合数: 3 x 2 x 4 = 24")
print()

print("grid_small配置 (基线实验):")
print("  地图大小: [5, 6, 7, 8, 9]")
print("  UAV数量: [1, 2, 3]")
print("  障碍密度: [0.0]")
print("  总组合数: 5 x 3 x 1 = 15")
print()

print("grid_obstacle配置 (障碍实验):")
print("  地图大小: [5, 6, 7, 8, 9]")
print("  UAV数量: [1, 2, 3]")
print("  障碍密度: [0.10]")
print("  总组合数: 5 x 3 x 1 = 15")
print()

