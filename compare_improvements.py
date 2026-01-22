#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比改进前后的实验结果"""
import csv
from pathlib import Path
from datetime import datetime

# 之前的实验结果（改进前）
previous_results = {
    "24x24_4_0.20": {
        "coverage": 0.730,
        "steps": 2000.0,
        "note": "改进前最终结果"
    }
}

# 读取当前实验结果
metrics_file = Path("experiments/results/metrics.csv")
current_result = None

if metrics_file.exists():
    with open(metrics_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # 查找最新的24x24, 4 UAVs, 障碍密度0.20的结果
    for row in reversed(rows):
        if (row['algorithm'] == 'qmix' and 
            row['map_height'] == '24' and 
            row['map_width'] == '24' and
            row['num_uavs'] == '4' and
            abs(float(row['obstacle_density']) - 0.20) < 0.001):
            current_result = {
                "coverage": float(row['coverage_mean']),
                "steps": float(row['steps_mean']),
                "timestamp": row.get('log_file', 'N/A')
            }
            break

# 读取当前训练日志
log_file = Path("experiments/logs/qmix.log")
current_training = None

if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找最新的训练
    for line in reversed(lines[-100:]):
        if "Training QMIX on map=(24, 24), num_uavs=4, obstacle_density=0.2" in line:
            # 查找最新的episode
            for i in range(len(lines) - 1, -1, -1):
                if "Episode" in lines[i] and "coverage_mean" in lines[i]:
                    parts = lines[i].split("|")
                    for part in parts:
                        if "Episode" in part:
                            ep_num = int(part.split("Episode")[1].split()[0])
                        if "coverage_mean=" in part:
                            coverage = float(part.split("=")[1])
                        if "steps_mean=" in part:
                            steps = float(part.split("=")[1])
                        if "epsilon=" in part:
                            epsilon = float(part.split("=")[1])
                    
                    current_training = {
                        "episode": ep_num,
                        "coverage": coverage,
                        "steps": steps,
                        "epsilon": epsilon,
                        "time": lines[i].split(" - ")[0] if " - " in lines[i] else "N/A"
                    }
                    break
            break

print("=" * 80)
print("改进效果对比分析")
print("=" * 80)
print()

print("实验配置: 24×24 地图, 4 架 UAV, 障碍密度 0.20")
print("-" * 80)
print()

# 显示之前的实验结果
print("改进前的实验结果:")
print(f"  最终覆盖率: {previous_results['24x24_4_0.20']['coverage']:.3f}")
print(f"  最终步数: {previous_results['24x24_4_0.20']['steps']:.1f}")
print()

# 显示当前训练进度
if current_training:
    print("当前训练进度（改进后）:")
    print(f"  Episode: {current_training['episode']}/600 ({current_training['episode']/600*100:.1f}%)")
    print(f"  当前覆盖率: {current_training['coverage']:.3f}")
    print(f"  当前步数: {current_training['steps']:.1f}")
    print(f"  当前 Epsilon: {current_training['epsilon']:.3f}")
    print(f"  更新时间: {current_training['time']}")
    print()
    
    # 对比分析
    if current_training['episode'] >= 100:
        print("改进效果分析（基于当前进度）:")
        print("-" * 80)
        improvement = current_training['coverage'] - previous_results['24x24_4_0.20']['coverage']
        if improvement > 0:
            print(f"  ✅ 覆盖率提升: {improvement:+.3f} ({improvement/previous_results['24x24_4_0.20']['coverage']*100:+.1f}%)")
        else:
            print(f"  ⚠️ 覆盖率变化: {improvement:+.3f} ({improvement/previous_results['24x24_4_0.20']['coverage']*100:+.1f}%)")
        
        if current_training['steps'] < previous_results['24x24_4_0.20']['steps']:
            step_improvement = previous_results['24x24_4_0.20']['steps'] - current_training['steps']
            print(f"  ✅ 步数减少: {step_improvement:.1f} 步")
        else:
            step_change = current_training['steps'] - previous_results['24x24_4_0.20']['steps']
            print(f"  ⚠️ 步数变化: {step_change:+.1f} 步")
    else:
        print("提示: 训练仍在早期阶段，需要更多episode才能进行有效对比")
        print("      建议等待到Episode 200-300后再进行对比分析")
else:
    print("当前训练: 未找到训练进度信息")

print()
print("=" * 80)
print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

