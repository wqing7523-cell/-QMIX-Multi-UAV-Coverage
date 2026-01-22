#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""显示当前实验进度"""
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
for line in reversed(lines[-100:]):
    line = line.strip()
    
    # 检测新实验开始
    if "Training QMIX on" in line:
        match = re.search(r'Training QMIX on map=\((\d+), (\d+)\), num_uavs=(\d+), obstacle_density=([\d.]+)', line)
        if match:
            current_exp = {
                'map_size': f"{match.group(1)}x{match.group(2)}",
                'num_uavs': int(match.group(3)),
                'obstacle_density': float(match.group(4)),
                'start_time': line.split(' - ')[0] if ' - ' in line else None,
                'episodes': [],
                'finished': False
            }
            break

# 查找该实验的所有episode
if current_exp:
    in_current_exp = False
    for line in lines:
        line = line.strip()
        if f"Training QMIX on map=({current_exp['map_size'].split('x')[0]}, {current_exp['map_size'].split('x')[1]})" in line and f"num_uavs={current_exp['num_uavs']}" in line and f"obstacle_density={current_exp['obstacle_density']}" in line:
            in_current_exp = True
            continue
        
        if in_current_exp:
            if "Training QMIX on" in line:
                break
            
            if "Episode" in line and "coverage_mean" in line:
                match = re.search(r'Episode (\d+)', line)
                if match:
                    ep_num = int(match.group(1))
                    cov_match = re.search(r'coverage_mean=([\d.]+)', line)
                    steps_match = re.search(r'steps_mean=([\d.]+)', line)
                    eps_match = re.search(r'epsilon=([\d.]+)', line)
                    
                    current_exp['episodes'].append({
                        'episode': ep_num,
                        'coverage': float(cov_match.group(1)) if cov_match else None,
                        'steps': float(steps_match.group(1)) if steps_match else None,
                        'epsilon': float(eps_match.group(1)) if eps_match else None,
                        'time': line.split(' - ')[0] if ' - ' in line else None
                    })
            
            if "Training finished" in line:
                match = re.search(r'coverage_mean=([\d.]+)', line)
                if match:
                    current_exp['final_coverage'] = float(match.group(1))
                    current_exp['finished'] = True
                    current_exp['end_time'] = line.split(' - ')[0] if ' - ' in line else None
                break

# 显示进度
print("=" * 70)
print("当前实验进度")
print("=" * 70)

if current_exp:
    print(f"实验配置: {current_exp['map_size']} 地图, {current_exp['num_uavs']} 架 UAV, 障碍密度 {current_exp['obstacle_density']}")
    print(f"开始时间: {current_exp['start_time']}")
    
    if current_exp['finished']:
        print(f"状态: [已完成]")
        print(f"最终覆盖率: {current_exp.get('final_coverage', 'N/A'):.3f}")
        print(f"结束时间: {current_exp.get('end_time', 'N/A')}")
    else:
        if current_exp['episodes']:
            latest = current_exp['episodes'][-1]
            progress = (latest['episode'] / 600) * 100
            print(f"状态: [进行中]")
            print(f"当前 Episode: {latest['episode']}/600 ({progress:.1f}%)")
            print(f"当前覆盖率: {latest['coverage']:.3f}")
            print(f"当前步数均值: {latest['steps']:.1f}")
            print(f"当前 Epsilon: {latest['epsilon']:.3f}")
            print(f"最后更新时间: {latest['time']}")
            
            # 估算剩余时间
            if len(current_exp['episodes']) >= 2:
                time_diff = None
                if latest['time'] and current_exp['episodes'][-2]['time']:
                    try:
                        t1 = datetime.strptime(latest['time'], "%Y-%m-%d %H:%M:%S,%f")
                        t2 = datetime.strptime(current_exp['episodes'][-2]['time'], "%Y-%m-%d %H:%M:%S,%f")
                        time_diff = (t1 - t2).total_seconds()
                        ep_diff = latest['episode'] - current_exp['episodes'][-2]['episode']
                        if ep_diff > 0 and time_diff > 0:
                            time_per_ep = time_diff / ep_diff
                            remaining_eps = 600 - latest['episode']
                            remaining_time = remaining_eps * time_per_ep
                            hours = int(remaining_time // 3600)
                            minutes = int((remaining_time % 3600) // 60)
                            print(f"预计剩余时间: {hours}小时 {minutes}分钟")
                    except:
                        pass
        else:
            print(f"状态: [等待开始]")
else:
    print("未找到当前实验信息")

# 检查进程
import subprocess
try:
    result = subprocess.run(
        ["powershell", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"],
        capture_output=True,
        text=True,
        timeout=5
    )
    proc_count = int(result.stdout.strip())
    if proc_count > 0:
        print(f"\n[运行中] 有 {proc_count} 个 Python 进程正在运行")
    else:
        print("\n[警告] 没有检测到运行中的 Python 进程")
except:
    print("\n[警告] 无法检查进程状态")

print("=" * 70)

