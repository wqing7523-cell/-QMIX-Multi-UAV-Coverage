#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""详细分析实验结果，找出需要改进的地方"""
import csv
import pandas as pd
from pathlib import Path
from collections import defaultdict

metrics_file = Path("experiments/results/metrics.csv")
if not metrics_file.exists():
    print("metrics.csv 文件不存在")
    exit(1)

# 读取所有实验结果
df = pd.read_csv(metrics_file)

# 筛选QMIX实验结果
qmix_df = df[df['algorithm'] == 'qmix'].copy()
qmix_df['map_size'] = qmix_df['map_height'].astype(str) + 'x' + qmix_df['map_width'].astype(str)
qmix_df['obstacle_density'] = qmix_df['obstacle_density'].astype(float)
qmix_df['coverage_mean'] = qmix_df['coverage_mean'].astype(float)
qmix_df['steps_mean'] = qmix_df['steps_mean'].astype(float)
qmix_df['num_uavs'] = qmix_df['num_uavs'].astype(int)

# 分离Stage 1和Stage 2
stage1 = qmix_df[qmix_df['obstacle_density'] == 0.0].copy()
stage2 = qmix_df[qmix_df['obstacle_density'] > 0.0].copy()

# 只关注extended配置（12x12, 16x16, 24x24）
target_maps = ['12x12', '16x16', '24x24']
stage1_ext = stage1[stage1['map_size'].isin(target_maps)].copy()
stage2_ext = stage2[stage2['map_size'].isin(target_maps)].copy()

print("=" * 90)
print("实验结果详细分析")
print("=" * 90)
print()

# 1. Stage 1 分析（无障碍）
print("=" * 90)
print("1. Stage 1 实验结果分析（无障碍）")
print("=" * 90)
print()

stage1_summary = stage1_ext.groupby(['map_size', 'num_uavs']).agg({
    'coverage_mean': ['mean', 'min', 'max'],
    'steps_mean': ['mean', 'min', 'max']
}).round(3)

print("Stage 1 实验结果汇总:")
print("-" * 90)
for (map_size, num_uavs), group in stage1_ext.groupby(['map_size', 'num_uavs']):
    coverage = group['coverage_mean'].values[0]
    steps = group['steps_mean'].values[0]
    status = "良好" if coverage >= 0.98 else "需改进" if coverage >= 0.90 else "较差"
    print(f"{map_size:8s} | {num_uavs} UAVs | 覆盖率: {coverage:.3f} | 步数: {steps:.1f} | 状态: {status}")

print()

# 找出Stage 1中需要改进的配置
print("Stage 1 需要改进的配置:")
print("-" * 90)
stage1_issues = []
for (map_size, num_uavs), group in stage1_ext.groupby(['map_size', 'num_uavs']):
    coverage = group['coverage_mean'].values[0]
    steps = group['steps_mean'].values[0]
    if coverage < 0.98:
        stage1_issues.append({
            'map_size': map_size,
            'num_uavs': num_uavs,
            'coverage': coverage,
            'steps': steps,
            'issue': '覆盖率低于目标值0.98'
        })
        print(f"  - {map_size}, {num_uavs} UAVs: 覆盖率 {coverage:.3f} < 0.98, 步数 {steps:.1f}")

if not stage1_issues:
    print("  无 - 所有Stage 1实验都达到了目标覆盖率（≥0.98）")

print()

# 2. Stage 2 分析（有障碍）
print("=" * 90)
print("2. Stage 2 实验结果分析（有障碍）")
print("=" * 90)
print()

# 按障碍密度分组分析
obstacle_densities = [0.05, 0.10, 0.20]
print("Stage 2 实验结果汇总（按障碍密度）:")
print("-" * 90)

stage2_issues = []

for obs_density in obstacle_densities:
    print(f"\n障碍密度: {obs_density}")
    print("-" * 90)
    obs_data = stage2_ext[stage2_ext['obstacle_density'] == obs_density]
    
    for (map_size, num_uavs), group in obs_data.groupby(['map_size', 'num_uavs']):
        coverage = group['coverage_mean'].values[0]
        steps = group['steps_mean'].values[0]
        
        # 判断性能等级
        if obs_density == 0.05:
            threshold = 0.95
        elif obs_density == 0.10:
            threshold = 0.90
        else:  # 0.20
            threshold = 0.80
        
        if coverage < threshold:
            status = "需改进"
            stage2_issues.append({
                'map_size': map_size,
                'num_uavs': num_uavs,
                'obstacle_density': obs_density,
                'coverage': coverage,
                'steps': steps,
                'threshold': threshold,
                'issue': f'覆盖率 {coverage:.3f} < 阈值 {threshold}'
            })
        elif steps >= 1995:  # 接近最大步数
            status = "需优化"
            stage2_issues.append({
                'map_size': map_size,
                'num_uavs': num_uavs,
                'obstacle_density': obs_density,
                'coverage': coverage,
                'steps': steps,
                'threshold': threshold,
                'issue': f'步数过多（{steps:.1f}），接近最大步数2000'
            })
        else:
            status = "良好"
        
        print(f"  {map_size:8s} | {num_uavs} UAVs | 覆盖率: {coverage:.3f} | 步数: {steps:.1f} | 状态: {status}")

print()

# 3. 性能趋势分析
print("=" * 90)
print("3. 性能趋势分析")
print("=" * 90)
print()

# 分析障碍密度对性能的影响
print("障碍密度对覆盖率的影响:")
print("-" * 90)
for map_size in target_maps:
    for num_uavs in [4, 6]:
        data = stage2_ext[(stage2_ext['map_size'] == map_size) & 
                          (stage2_ext['num_uavs'] == num_uavs)].sort_values('obstacle_density')
        if len(data) > 0:
            coverages = data['coverage_mean'].values
            densities = data['obstacle_density'].values
            print(f"{map_size}, {num_uavs} UAVs:")
            for d, c in zip(densities, coverages):
                print(f"  障碍密度 {d:.2f}: 覆盖率 {c:.3f}")
            
            # 计算下降率
            if len(coverages) >= 2:
                decline = (coverages[0] - coverages[-1]) / coverages[0] * 100
                print(f"  从0.05到0.20的下降率: {decline:.1f}%")
            print()

# 4. 找出需要改进的配置
print("=" * 90)
print("4. 需要改进的配置汇总")
print("=" * 90)
print()

if stage1_issues:
    print("Stage 1 需要改进的配置:")
    print("-" * 90)
    for issue in stage1_issues:
        print(f"  - {issue['map_size']}, {issue['num_uavs']} UAVs: {issue['issue']}")
    print()

if stage2_issues:
    print("Stage 2 需要改进的配置:")
    print("-" * 90)
    for issue in stage2_issues:
        print(f"  - {issue['map_size']}, {issue['num_uavs']} UAVs, 障碍密度 {issue['obstacle_density']}: {issue['issue']}")
    print()

# 5. 改进建议
print("=" * 90)
print("5. 改进建议")
print("=" * 90)
print()

suggestions = []

# 分析Stage 1问题
if stage1_issues:
    print("Stage 1 改进建议:")
    print("-" * 90)
    for issue in stage1_issues:
        if issue['steps'] >= 1995:
            suggestions.append({
                'category': 'Stage 1',
                'config': f"{issue['map_size']}, {issue['num_uavs']} UAVs",
                'issue': '步数过多，接近最大步数',
                'suggestions': [
                    '增加探索奖励权重（shaping_weight）',
                    '调整epsilon衰减策略，增加早期探索',
                    '优化奖励函数，鼓励更高效的路径规划',
                    '考虑增加episode数量或调整学习率'
                ]
            })
        else:
            suggestions.append({
                'category': 'Stage 1',
                'config': f"{issue['map_size']}, {issue['num_uavs']} UAVs",
                'issue': '覆盖率未达到目标',
                'suggestions': [
                    '调整恢复机制参数（coverage_threshold, drop_tolerance）',
                    '优化epsilon衰减曲线',
                    '增加训练episode数量',
                    '调整网络结构（hidden_dim）'
                ]
            })

# 分析Stage 2问题
if stage2_issues:
    print("Stage 2 改进建议:")
    print("-" * 90)
    
    # 按问题类型分组
    coverage_issues = [i for i in stage2_issues if '覆盖率' in i['issue']]
    steps_issues = [i for i in stage2_issues if '步数' in i['issue']]
    
    if coverage_issues:
        print("\n覆盖率问题:")
        high_density_issues = [i for i in coverage_issues if i['obstacle_density'] == 0.20]
        if high_density_issues:
            print("  高障碍密度（0.20）配置:")
            for issue in high_density_issues:
                print(f"    - {issue['map_size']}, {issue['num_uavs']} UAVs: 覆盖率 {issue['coverage']:.3f}")
            suggestions.append({
                'category': 'Stage 2 - 高障碍密度',
                'config': '所有0.20密度配置',
                'issue': '高障碍密度下覆盖率显著下降',
                'suggestions': [
                    '增加障碍回避奖励权重（obstacle_shaping_weight），当前5.0可尝试提高到6.0-8.0',
                    '优化障碍检测和回避策略',
                    '使用课程学习：从低障碍密度模型warm-start',
                    '调整探索策略：在高障碍密度场景使用更高的epsilon_end（0.12-0.15）',
                    '增加奖励函数中完成探索的奖励',
                    '考虑使用动态障碍物检测和预测'
                ]
            })
        
        medium_density_issues = [i for i in coverage_issues if i['obstacle_density'] == 0.10]
        if medium_density_issues:
            print("  中等障碍密度（0.10）配置:")
            for issue in medium_density_issues:
                print(f"    - {issue['map_size']}, {issue['num_uavs']} UAVs: 覆盖率 {issue['coverage']:.3f}")
            suggestions.append({
                'category': 'Stage 2 - 中等障碍密度',
                'config': '部分0.10密度配置',
                'issue': '中等障碍密度下性能下降',
                'suggestions': [
                    '微调obstacle_shaping_weight（当前5.0）',
                    '优化探索和利用的平衡',
                    '调整恢复机制以适应有障碍场景'
                ]
            })
    
    if steps_issues:
        print("\n步数过多问题:")
        for issue in steps_issues:
            print(f"  - {issue['map_size']}, {issue['num_uavs']} UAVs, 障碍密度 {issue['obstacle_density']}: 步数 {issue['steps']:.1f}")
        suggestions.append({
            'category': 'Stage 2 - 步数优化',
            'config': '多个配置',
            'issue': '步数接近最大步数2000',
            'suggestions': [
                '增加探索效率奖励',
                '优化路径规划，减少重复访问',
                '调整奖励函数，鼓励更短的路径',
                '考虑增加最大步数（max_steps）或优化探索策略'
            ]
        })

# 打印详细建议
print()
print("=" * 90)
print("详细改进建议")
print("=" * 90)
print()

for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion['category']}: {suggestion['config']}")
    print(f"   问题: {suggestion['issue']}")
    print(f"   建议:")
    for j, sug in enumerate(suggestion['suggestions'], 1):
        print(f"     {j}. {sug}")
    print()

# 6. 总体统计
print("=" * 90)
print("6. 总体统计")
print("=" * 90)
print()

print(f"Stage 1 实验总数: {len(stage1_ext)}")
print(f"Stage 1 达到目标（≥0.98）: {len([1 for _, row in stage1_ext.iterrows() if row['coverage_mean'] >= 0.98])}")
print(f"Stage 1 需要改进: {len(stage1_issues)}")
print()

print(f"Stage 2 实验总数: {len(stage2_ext)}")
print(f"Stage 2 需要改进: {len(stage2_issues)}")
print()

# 计算平均覆盖率
print("平均覆盖率:")
print(f"  Stage 1: {stage1_ext['coverage_mean'].mean():.3f}")
print(f"  Stage 2 (障碍密度0.05): {stage2_ext[stage2_ext['obstacle_density']==0.05]['coverage_mean'].mean():.3f}")
print(f"  Stage 2 (障碍密度0.10): {stage2_ext[stage2_ext['obstacle_density']==0.10]['coverage_mean'].mean():.3f}")
print(f"  Stage 2 (障碍密度0.20): {stage2_ext[stage2_ext['obstacle_density']==0.20]['coverage_mean'].mean():.3f}")
print()

print("=" * 90)

