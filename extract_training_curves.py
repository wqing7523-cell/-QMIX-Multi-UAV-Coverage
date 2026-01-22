#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从日志中提取真实的训练曲线数据"""
import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

def extract_training_curve(log_file, map_size, num_uavs, obstacle_density):
    """从日志中提取特定配置的训练曲线"""
    content = log_file.read_text(encoding="utf-8")
    
    # 查找匹配的训练
    pattern = f"Training QMIX on map=\\({map_size}, {map_size}\\), num_uavs={num_uavs}, obstacle_density={obstacle_density:.2f}"
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        return None
    
    # 获取最后一次训练
    last_match = matches[-1]
    start_idx = last_match.start()
    
    # 找到下一个训练的开始位置
    next_idx = len(content)
    if matches.index(last_match) < len(matches) - 1:
        next_idx = matches[matches.index(last_match) + 1].start()
    
    log_section = content[start_idx:next_idx]
    
    # 提取所有Episode数据
    episode_pattern = r"Episode (\d+) \| coverage_mean=([\d.]+)"
    episodes = re.findall(episode_pattern, log_section)
    
    if not episodes:
        return None
    
    episode_nums = [int(ep[0]) for ep in episodes]
    coverages = [float(ep[1]) for ep in episodes]
    
    return episode_nums, coverages

# 提取24×24, 4 UAV, 0.20障碍密度的训练曲线
log_file = Path("experiments/logs/qmix.log")
episodes, coverages = extract_training_curve(log_file, 24, 4, 0.20)

if episodes and coverages:
    # 生成真实的训练曲线图
    output_dir = Path("experiments/figures/paper")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(episodes, coverages, linewidth=2, label='Coverage Rate', color='#2196F3')
    ax.fill_between(episodes, coverages, alpha=0.3, color='#2196F3')
    
    # 添加关键点
    key_episodes = [100, 200, 300, 400, 500, 600]
    for key_ep in key_episodes:
        if key_ep in episodes:
            idx = episodes.index(key_ep)
            ax.plot(key_ep, coverages[idx], 'ro', markersize=8)
            ax.annotate(f'{coverages[idx]:.2f}', 
                        (key_ep, coverages[idx]),
                        textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    ax.set_xlabel('Episode', fontsize=12)
    ax.set_ylabel('Coverage Rate', fontsize=12)
    ax.set_title('Training Curve: 24×24 Map, 4 UAVs, Obstacle Density 0.20', fontsize=14, weight='bold')
    ax.set_ylim(0.4, 1.0)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure6_training_curve_real.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'figure6_training_curve_real.pdf', bbox_inches='tight')
    plt.close()
    
    print(f"Real training curve extracted: {len(episodes)} data points")
    print(f"Saved to: {output_dir / 'figure6_training_curve_real.png'}")
else:
    print("Training curve data not found")

