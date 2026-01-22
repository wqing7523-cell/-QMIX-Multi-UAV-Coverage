#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析测试实验结果，找出问题"""
import re
from pathlib import Path

log_file = Path("experiments/logs/qmix.log")
previous_result = 0.730  # 改进前的最终覆盖率

def analyze_training_curve():
    """分析训练曲线"""
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找最新的24x24, 4 UAVs, 障碍密度0.20的训练
    start_line = None
    for i, line in enumerate(reversed(lines[-1000:]), 1):
        if "Training QMIX on map=(24, 24), num_uavs=4, obstacle_density=0.2" in line and "2025-11-15 13:55" in line:
            start_line = len(lines) - i
            break
    
    if start_line is None:
        return None
    
    episodes = []
    for line in lines[start_line:]:
        if "Episode" in line and "coverage_mean" in line:
            match = re.search(r'Episode (\d+).*coverage_mean=([\d.]+)', line)
            if match:
                ep_num = int(match.group(1))
                coverage = float(match.group(2))
                episodes.append((ep_num, coverage))
        
        if "Training finished" in line:
            break
    
    return episodes

def analyze_problem(episodes):
    """分析问题"""
    if not episodes:
        return
    
    print("=" * 90)
    print("测试结果分析")
    print("=" * 90)
    print()
    
    print(f"改进前最终结果: 覆盖率 {previous_result:.3f}")
    print(f"改进后最终结果: 覆盖率 {episodes[-1][1]:.3f}")
    print(f"性能变化: {episodes[-1][1] - previous_result:+.3f} ({(episodes[-1][1] - previous_result)/previous_result*100:+.1f}%)")
    print()
    
    # 分析训练曲线
    print("训练曲线分析:")
    print("-" * 90)
    
    # 找到关键检查点
    checkpoints = [100, 200, 300, 400, 500, 600]
    for cp in checkpoints:
        covs = [c for e, c in episodes if e == cp]
        if covs:
            print(f"Episode {cp:3d}: 覆盖率 {covs[0]:.3f}")
    
    print()
    
    # 分析趋势
    print("性能趋势分析:")
    print("-" * 90)
    
    # 早期阶段（Episode 1-200）
    early_eps = [c for e, c in episodes if e <= 200]
    if early_eps:
        early_avg = sum(early_eps) / len(early_eps)
        print(f"早期阶段 (Episode 1-200) 平均覆盖率: {early_avg:.3f}")
        if early_avg > previous_result:
            print("  [良好] 早期性能优于改进前")
        else:
            print("  [问题] 早期性能低于改进前")
    
    # 中期阶段（Episode 200-400）
    mid_eps = [c for e, c in episodes if 200 < e <= 400]
    if mid_eps:
        mid_avg = sum(mid_eps) / len(mid_eps)
        print(f"中期阶段 (Episode 200-400) 平均覆盖率: {mid_avg:.3f}")
        if mid_avg > previous_result:
            print("  [良好] 中期性能优于改进前")
        else:
            print("  [问题] 中期性能低于改进前")
    
    # 后期阶段（Episode 400-600）
    late_eps = [c for e, c in episodes if 400 < e <= 600]
    if late_eps:
        late_avg = sum(late_eps) / len(late_eps)
        print(f"后期阶段 (Episode 400-600) 平均覆盖率: {late_avg:.3f}")
        if late_avg > previous_result:
            print("  [良好] 后期性能优于改进前")
        else:
            print("  [问题] 后期性能低于改进前")
    
    print()
    
    # 分析问题
    print("问题分析:")
    print("-" * 90)
    
    # 检查是否出现性能崩溃
    max_coverage = max(c for _, c in episodes)
    min_coverage = min(c for _, c in episodes)
    final_coverage = episodes[-1][1]
    
    print(f"最高覆盖率: {max_coverage:.3f} (Episode {[e for e, c in episodes if c == max_coverage][0]})")
    print(f"最低覆盖率: {min_coverage:.3f}")
    print(f"最终覆盖率: {final_coverage:.3f}")
    print(f"覆盖率波动范围: {max_coverage - min_coverage:.3f}")
    print()
    
    # 检查性能下降
    if final_coverage < max_coverage - 0.05:
        print("[问题] 训练后期出现性能崩溃")
        print(f"  从最高 {max_coverage:.3f} 下降到最终 {final_coverage:.3f}")
        print("  可能原因:")
        print("    1. Epsilon衰减过快，后期探索不足")
        print("    2. 恢复机制过于激进，导致模型回退")
        print("    3. 学习率过高，导致训练不稳定")
        print("    4. 障碍回避权重过高，影响了探索")
    
    # 检查是否一直低于改进前
    if all(c < previous_result - 0.02 for _, c in episodes[-50:]):
        print("[问题] 整个训练过程性能都低于改进前")
        print("  可能原因:")
        print("    1. 动态权重设置不当（obstacle_shaping_weight=8.0可能太高）")
        print("    2. Epsilon设置不当（epsilon_end=0.12可能太高，导致过度探索）")
        print("    3. 需要调整其他超参数")
    
    print()
    print("=" * 90)

if __name__ == "__main__":
    episodes = analyze_training_curve()
    if episodes:
        analyze_problem(episodes)
    else:
        print("未找到训练数据")

