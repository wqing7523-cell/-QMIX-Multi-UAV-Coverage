#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取课程学习结果"""
import re
from pathlib import Path

log_file = Path("experiments/logs/qmix.log")
content = log_file.read_text(encoding="utf-8")

print("=" * 70)
print("课程学习结果分析")
print("=" * 70)
print()

# 分析每个障碍密度
obs_densities = [0.05, 0.10, 0.20]

for obs_d in obs_densities:
    pattern = f"Training QMIX on map=\\(24, 24\\), num_uavs=4, obstacle_density={obs_d}"
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        continue
    
    # 获取最后一次训练
    last_match = matches[-1]
    start_idx = last_match.start()
    
    # 找到下一个训练的开始位置
    next_idx = len(content)
    if matches.index(last_match) < len(matches) - 1:
        next_idx = matches[matches.index(last_match) + 1].start()
    
    log_section = content[start_idx:next_idx]
    
    # 检查课程学习
    curriculum_pattern = r"Curriculum learning: Loading checkpoint|Loading initial checkpoint from.*obs(\d+)"
    curriculum_match = re.search(curriculum_pattern, log_section)
    curriculum_used = curriculum_match is not None
    curriculum_from = None
    if curriculum_match and curriculum_match.group(1):
        obs_str = curriculum_match.group(1)
        if obs_str == "005":
            curriculum_from = 0.05
        elif obs_str == "010":
            curriculum_from = 0.10
    
    # 提取Episode 600
    ep600_pattern = r"Episode 600 \| coverage_mean=([\d.]+) \| pa_mean=([\d.]+)"
    ep600_match = re.search(ep600_pattern, log_section)
    
    # 提取Episode 10
    ep10_pattern = r"Episode 10 \| coverage_mean=([\d.]+)"
    ep10_match = re.search(ep10_pattern, log_section)
    
    print(f"障碍密度 {obs_d:.2f}:")
    print(f"  课程学习: {'已启用' if curriculum_used else '未启用'}")
    if curriculum_from:
        print(f"  从障碍密度 {curriculum_from:.2f} 的checkpoint warm-start")
    if ep10_match:
        print(f"  Episode 10: {ep10_match.group(1)}")
    if ep600_match:
        print(f"  Episode 600: {ep600_match.group(1)}")
    else:
        print(f"  Episode 600: 训练中...")
    print()

print("=" * 70)
print("对比分析")
print("=" * 70)
print()

# 对比障碍密度0.20的结果
pattern_020 = "Training QMIX on map=\\(24, 24\\), num_uavs=4, obstacle_density=0\\.20"
matches_020 = list(re.finditer(pattern_020, content))

if matches_020:
    # 获取最后一次0.20的训练
    last_020 = matches_020[-1]
    start_020 = last_020.start()
    next_020 = len(content)
    if matches_020.index(last_020) < len(matches_020) - 1:
        next_020 = matches_020[matches_020.index(last_020) + 1].start()
    section_020 = content[start_020:next_020]
    
    curriculum_020 = bool(re.search(r"Curriculum learning|Loading initial checkpoint", section_020))
    ep600_020 = re.search(r"Episode 600 \| coverage_mean=([\d.]+)", section_020)
    
    print("障碍密度0.20的对比:")
    print("-" * 70)
    print("  当前结果（有课程学习）:")
    if ep600_020:
        cov_020 = float(ep600_020.group(1))
        print(f"    最终覆盖率: {cov_020:.3f}")
        
        # 对比之前的结果
        print()
        print("  之前结果（无课程学习，第三次调整后）:")
        print("    最终覆盖率: 0.592")
        print()
        
        improvement = cov_020 - 0.592
        improvement_pct = (improvement / 0.592) * 100
        print(f"  改进:")
        print(f"    覆盖率提升: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    else:
        print("    训练中，等待完成...")

