#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""实时显示实验进度，类似训练日志格式"""
import re
from pathlib import Path
from datetime import datetime

log_file = Path("experiments/logs/qmix.log")
if not log_file.exists():
    print("日志文件不存在")
    exit(1)

with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找最新的实验
current_exp = None
start_line_idx = 0

for i, line in enumerate(reversed(lines[-500:]), 1):
    line = line.strip()
    if "Training QMIX on" in line:
        match = re.search(r'Training QMIX on map=\((\d+), (\d+)\), num_uavs=(\d+), obstacle_density=([\d.]+)', line)
        if match:
            current_exp = {
                'map_size': f"{match.group(1)}x{match.group(2)}",
                'num_uavs': int(match.group(3)),
                'obstacle_density': float(match.group(4)),
                'start_time': line.split(' - ')[0] if ' - ' in line else None,
                'start_line': len(lines) - i,
                'episodes': [],
                'finished': False
            }
            start_line_idx = len(lines) - i
            break

if not current_exp:
    print("未找到当前实验信息")
    exit(1)

# 查找该实验的所有episode和完成信息
for line in lines[start_line_idx:]:
    line = line.strip()
    
    # 检查是否开始了新实验
    if "Training QMIX on" in line and "Training QMIX on" not in lines[start_line_idx]:
        # 确保不是当前实验
        if not (f"map=({current_exp['map_size'].split('x')[0]}, {current_exp['map_size'].split('x')[1]})" in line and
                f"num_uavs={current_exp['num_uavs']}" in line and
                f"obstacle_density={current_exp['obstacle_density']}" in line):
            break
    
    # 查找Episode日志
    if "Episode" in line and "coverage_mean" in line:
        match = re.search(r'Episode (\d+)', line)
        if match:
            ep_num = int(match.group(1))
            cov_match = re.search(r'coverage_mean=([\d.]+)', line)
            pa_match = re.search(r'pa_mean=([\d.]+)', line)
            steps_match = re.search(r'steps_mean=([\d.]+)', line)
            eps_match = re.search(r'epsilon=([\d.]+)', line)
            
            current_exp['episodes'].append({
                'episode': ep_num,
                'coverage': float(cov_match.group(1)) if cov_match else None,
                'pa': float(pa_match.group(1)) if pa_match else None,
                'steps': float(steps_match.group(1)) if steps_match else None,
                'epsilon': float(eps_match.group(1)) if eps_match else None,
                'time': line.split(' - ')[0] if ' - ' in line else None,
                'raw_line': line
            })
    
    # 查找训练完成信息
    if "Training finished" in line:
        match = re.search(r'coverage_mean=([\d.]+)', line)
        if match:
            current_exp['final_coverage'] = float(match.group(1))
            current_exp['finished'] = True
            current_exp['end_time'] = line.split(' - ')[0] if ' - ' in line else None
            break

# 显示进度
print("=" * 90)
print(f"实验配置: {current_exp['map_size']} 地图, {current_exp['num_uavs']} 架 UAV, 障碍密度 {current_exp['obstacle_density']}")
print(f"开始时间: {current_exp['start_time']}")
print("=" * 90)
print()

if current_exp['finished']:
    print("[已完成] 训练已完成")
    print(f"最终覆盖率: {current_exp.get('final_coverage', 'N/A'):.3f}")
    print(f"结束时间: {current_exp.get('end_time', 'N/A')}")
    print()
    print("最近10个Episode:")
    print("-" * 90)
    for ep in current_exp['episodes'][-10:]:
        print(ep['raw_line'])
else:
    if current_exp['episodes']:
        latest = current_exp['episodes'][-1]
        progress = (latest['episode'] / 600) * 100
        
        print(f"[进行中] Episode {latest['episode']}/600 ({progress:.1f}%)")
        print()
        
        # 显示最近15个Episode的详细日志
        print("最近的训练日志 (格式: Episode | coverage_mean | pa_mean | steps_mean | epsilon):")
        print("-" * 90)
        for ep in current_exp['episodes'][-15:]:
            print(ep['raw_line'])
        
        print()
        print("-" * 90)
        print(f"当前状态:")
        print(f"  Episode: {latest['episode']}/600")
        print(f"  覆盖率: {latest['coverage']:.3f}")
        print(f"  PA均值: {latest['pa']:.3f}")
        print(f"  步数均值: {latest['steps']:.1f}")
        print(f"  Epsilon: {latest['epsilon']:.3f}")
        print(f"  更新时间: {latest['time']}")
        
        # 估算剩余时间
        if len(current_exp['episodes']) >= 2:
            try:
                t1 = datetime.strptime(latest['time'], "%Y-%m-%d %H:%M:%S,%f")
                prev_ep = current_exp['episodes'][-2]
                if prev_ep['time']:
                    t2 = datetime.strptime(prev_ep['time'], "%Y-%m-%d %H:%M:%S,%f")
                    time_diff = (t1 - t2).total_seconds()
                    ep_diff = latest['episode'] - prev_ep['episode']
                    if ep_diff > 0 and time_diff > 0:
                        time_per_ep = time_diff / ep_diff
                        remaining_eps = 600 - latest['episode']
                        remaining_time = remaining_eps * time_per_ep
                        hours = int(remaining_time // 3600)
                        minutes = int((remaining_time % 3600) // 60)
                        print(f"  预计剩余时间: {hours}小时 {minutes}分钟")
            except:
                pass
    else:
        print("[等待开始] 实验已启动，等待第一个Episode...")

print()
print("=" * 90)
print(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 90)

