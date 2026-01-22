#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成QMIX框架图的Python脚本（使用matplotlib）"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# 定义颜色
color_env = '#E8F4F8'
color_agent = '#FFF4E6'
color_mixer = '#F0E8F6'
color_action = '#E8F8E8'
color_buffer = '#F8E8E8'
color_train = '#F8F0E8'

# 1. 环境层
env_box = FancyBboxPatch((0.5, 9.5), 9, 2, 
                         boxstyle="round,pad=0.1", 
                         facecolor=color_env, 
                         edgecolor='black', 
                         linewidth=2)
ax.add_patch(env_box)
ax.text(5, 10.8, 'Environment Layer', ha='center', va='center', fontsize=14, weight='bold')
ax.text(2, 10.2, 'Map State', ha='center', va='center', fontsize=10)
ax.text(5, 10.2, 'UAV Positions', ha='center', va='center', fontsize=10)
ax.text(8, 10.2, 'Obstacles', ha='center', va='center', fontsize=10)
ax.text(5, 9.7, 'Observations: (o_1, o_2, ..., o_N)', ha='center', va='center', fontsize=9)

# 2. 智能体层
agent_box = FancyBboxPatch((0.5, 6.5), 9, 2.5, 
                          boxstyle="round,pad=0.1", 
                          facecolor=color_agent, 
                          edgecolor='black', 
                          linewidth=2)
ax.add_patch(agent_box)
ax.text(5, 8.7, 'Agent Layer', ha='center', va='center', fontsize=14, weight='bold')

# Agent Networks
for i, x_pos in enumerate([2, 5, 8]):
    agent_net = FancyBboxPatch((x_pos-0.8, 7.2), 1.6, 1, 
                              boxstyle="round,pad=0.05", 
                              facecolor='white', 
                              edgecolor='blue', 
                              linewidth=1.5)
    ax.add_patch(agent_net)
    ax.text(x_pos, 7.9, f'Agent {i+1}', ha='center', va='center', fontsize=9, weight='bold')
    ax.text(x_pos, 7.5, 'FC1→RNN→FC2', ha='center', va='center', fontsize=8)
    ax.text(x_pos, 7.1, f'o_{i+1} → Q_{i+1}', ha='center', va='center', fontsize=8)

ax.text(5, 6.7, 'Q-values: (Q_1, Q_2, ..., Q_N)', ha='center', va='center', fontsize=9)

# 3. 混合层
mixer_box = FancyBboxPatch((2.5, 4), 5, 2, 
                          boxstyle="round,pad=0.1", 
                          facecolor=color_mixer, 
                          edgecolor='black', 
                          linewidth=2)
ax.add_patch(mixer_box)
ax.text(5, 5.7, 'Mixing Layer', ha='center', va='center', fontsize=14, weight='bold')

mixer_net = FancyBboxPatch((3.5, 4.3), 3, 1.2, 
                           boxstyle="round,pad=0.05", 
                           facecolor='white', 
                           edgecolor='purple', 
                           linewidth=1.5)
ax.add_patch(mixer_net)
ax.text(5, 5.1, 'Mixing Network', ha='center', va='center', fontsize=10, weight='bold')
ax.text(5, 4.7, 'Hypernetwork', ha='center', va='center', fontsize=9)
ax.text(5, 4.4, 'Q_total = Mix(Q_1, Q_2, ..., Q_N, state)', ha='center', va='center', fontsize=8)

# 4. 动作选择
action_box = FancyBboxPatch((2.5, 2.5), 5, 1, 
                           boxstyle="round,pad=0.1", 
                           facecolor=color_action, 
                           edgecolor='black', 
                           linewidth=2)
ax.add_patch(action_box)
ax.text(5, 3.2, 'Action Selection', ha='center', va='center', fontsize=12, weight='bold')
ax.text(5, 2.7, 'Epsilon-greedy: argmax(Q_total) or random', ha='center', va='center', fontsize=9)

# 5. 经验回放
buffer_box = FancyBboxPatch((0.5, 0.5), 4, 1.5, 
                           boxstyle="round,pad=0.1", 
                           facecolor=color_buffer, 
                           edgecolor='black', 
                           linewidth=2)
ax.add_patch(buffer_box)
ax.text(2.5, 1.5, 'Replay Buffer', ha='center', va='center', fontsize=12, weight='bold')
ax.text(2.5, 1.0, 'Store: (s_t, a_t, r_t, s_{t+1})', ha='center', va='center', fontsize=9)

# 6. 训练更新
train_box = FancyBboxPatch((5.5, 0.5), 4, 1.5, 
                          boxstyle="round,pad=0.1", 
                          facecolor=color_train, 
                          edgecolor='black', 
                          linewidth=2)
ax.add_patch(train_box)
ax.text(7.5, 1.5, 'Training Update', ha='center', va='center', fontsize=12, weight='bold')
ax.text(7.5, 1.0, 'TD Loss → Backprop → Update', ha='center', va='center', fontsize=9)

# 箭头连接
# 环境 → 智能体
arrow1 = FancyArrowPatch((5, 9.5), (5, 9), 
                         arrowstyle='->', lw=2, color='black')
ax.add_patch(arrow1)

# 智能体 → 混合
arrow2 = FancyArrowPatch((5, 6.5), (5, 6), 
                         arrowstyle='->', lw=2, color='black')
ax.add_patch(arrow2)

# 混合 → 动作选择
arrow3 = FancyArrowPatch((5, 4), (5, 3.5), 
                         arrowstyle='->', lw=2, color='black')
ax.add_patch(arrow3)

# 动作选择 → 环境
arrow4 = FancyArrowPatch((5, 2.5), (5, 2), 
                         arrowstyle='->', lw=2, color='black')
ax.add_patch(arrow4)

# 环境 → 经验回放
arrow5 = FancyArrowPatch((2.5, 9.5), (2.5, 2), 
                         arrowstyle='->', lw=2, color='red', linestyle='--')
ax.add_patch(arrow5)

# 经验回放 → 训练
arrow6 = FancyArrowPatch((4.5, 1.25), (5.5, 1.25), 
                         arrowstyle='->', lw=2, color='red', linestyle='--')
ax.add_patch(arrow6)

# 训练 → 智能体/混合（参数更新）
arrow7 = FancyArrowPatch((7.5, 2), (7.5, 6.5), 
                         arrowstyle='->', lw=2, color='green', linestyle=':')
ax.add_patch(arrow7)

# 添加图例
legend_elements = [
    mpatches.Patch(facecolor='black', label='Data Flow'),
    mpatches.Patch(facecolor='red', label='Experience Collection'),
    mpatches.Patch(facecolor='green', label='Parameter Update')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

plt.title('QMIX Framework for Multi-UAV Path Planning', fontsize=16, weight='bold', pad=20)
plt.tight_layout()
plt.savefig('experiments/figures/qmix_framework.png', dpi=300, bbox_inches='tight')
plt.savefig('experiments/figures/qmix_framework.pdf', bbox_inches='tight')
print("Framework diagram saved to experiments/figures/qmix_framework.png and .pdf")

