#!/usr/bin/env python
"""检查实验进度"""
import re
from pathlib import Path
from datetime import datetime

log_file = Path("experiments/logs/qmix.log")
if not log_file.exists():
    print("日志文件不存在")
    exit(1)

with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找所有训练开始和结束的记录
experiments = []
current_exp = None

for line in lines:
    line = line.strip()
    
    # 检测新实验开始
    if "Training QMIX on" in line:
        match = re.search(r'Training QMIX on map=\((\d+), (\d+)\), num_uavs=(\d+), obstacle_density=([\d.]+)', line)
        if match:
            if current_exp:
                experiments.append(current_exp)
            current_exp = {
                'map_size': f"{match.group(1)}x{match.group(2)}",
                'num_uavs': int(match.group(3)),
                'obstacle_density': float(match.group(4)),
                'start_time': line.split(' - ')[0] if ' - ' in line else None,
                'episodes': [],
                'finished': False
            }
    
    # 检测Episode进度
    if current_exp and "Episode" in line and "coverage_mean" in line:
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
    
    # 检测训练完成
    if current_exp and "Training finished" in line:
        match = re.search(r'coverage_mean=([\d.]+)', line)
        if match:
            current_exp['final_coverage'] = float(match.group(1))
            current_exp['finished'] = True
            current_exp['end_time'] = line.split(' - ')[0] if ' - ' in line else None

if current_exp:
    experiments.append(current_exp)

# 显示进度
print("=" * 80)
print("实验进度报告")
print("=" * 80)
print()

for i, exp in enumerate(experiments, 1):
    print(f"实验 {i}: {exp['map_size']} 地图, {exp['num_uavs']} 架 UAV, 障碍密度 {exp['obstacle_density']}")
    print(f"开始时间: {exp['start_time']}")
    
    if exp['finished']:
        print(f"状态: [已完成]")
        print(f"最终覆盖率: {exp.get('final_coverage', 'N/A'):.3f}")
        print(f"结束时间: {exp.get('end_time', 'N/A')}")
    else:
        if exp['episodes']:
            latest = exp['episodes'][-1]
            progress = (latest['episode'] / 600) * 100
            print(f"状态: [进行中]")
            print(f"当前 Episode: {latest['episode']}/600 ({progress:.1f}%)")
            print(f"当前覆盖率: {latest['coverage']:.3f}")
            print(f"当前步数均值: {latest['steps']:.1f}")
            print(f"当前 Epsilon: {latest['epsilon']:.3f}")
            print(f"最后更新时间: {latest['time']}")
            
            # 估算剩余时间
            if len(exp['episodes']) >= 2:
                time_diff = None
                if latest['time'] and exp['episodes'][-2]['time']:
                    try:
                        t1 = datetime.strptime(latest['time'], "%Y-%m-%d %H:%M:%S,%f")
                        t2 = datetime.strptime(exp['episodes'][-2]['time'], "%Y-%m-%d %H:%M:%S,%f")
                        time_diff = (t1 - t2).total_seconds()
                        ep_diff = latest['episode'] - exp['episodes'][-2]['episode']
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
    
    print("-" * 80)
    print()

# 检查是否有进程在运行
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
        print(f"[运行中] 有 {proc_count} 个 Python 进程正在运行")
    else:
        print("[警告] 没有检测到运行中的 Python 进程")
except:
    print("[警告] 无法检查进程状态")

print("=" * 80)

