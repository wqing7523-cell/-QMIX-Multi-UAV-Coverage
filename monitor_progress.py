#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""实时监控实验进度并显示详细信息"""
import re
import subprocess
from pathlib import Path
from datetime import datetime
import time

def get_experiment_status():
    """获取当前实验状态"""
    log_file = Path("experiments/logs/qmix.log")
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找最新的实验
    current_exp = None
    for line in reversed(lines[-200:]):
        line = line.strip()
        
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
    
    if not current_exp:
        return None
    
    # 查找该实验的所有episode
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
    
    return current_exp

def get_process_count():
    """获取Python进程数量"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return int(result.stdout.strip())
    except:
        return 0

def format_progress(exp):
    """格式化进度显示"""
    if not exp:
        return "未找到当前实验信息"
    
    output = []
    output.append("=" * 70)
    output.append("实时实验进度监控")
    output.append("=" * 70)
    output.append("")
    output.append(f"实验配置: {exp['map_size']} 地图, {exp['num_uavs']} 架 UAV, 障碍密度 {exp['obstacle_density']}")
    output.append(f"开始时间: {exp['start_time']}")
    output.append("")
    
    if exp['finished']:
        output.append("状态: [已完成]")
        output.append(f"最终覆盖率: {exp.get('final_coverage', 'N/A'):.3f}")
        output.append(f"结束时间: {exp.get('end_time', 'N/A')}")
    else:
        if exp['episodes']:
            latest = exp['episodes'][-1]
            progress = (latest['episode'] / 600) * 100
            output.append("状态: [进行中]")
            output.append(f"当前 Episode: {latest['episode']}/600 ({progress:.1f}%)")
            output.append(f"当前覆盖率: {latest['coverage']:.3f}")
            output.append(f"当前步数均值: {latest['steps']:.1f}")
            output.append(f"当前 Epsilon: {latest['epsilon']:.3f}")
            output.append(f"最后更新时间: {latest['time']}")
            
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
                            output.append(f"预计剩余时间: {hours}小时 {minutes}分钟")
                    except:
                        pass
        else:
            output.append("状态: [等待开始]")
    
    output.append("")
    proc_count = get_process_count()
    if proc_count > 0:
        output.append(f"[运行中] 有 {proc_count} 个 Python 进程正在运行")
    else:
        output.append("[警告] 没有检测到运行中的 Python 进程")
    
    output.append("")
    output.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 70)
    
    return "\n".join(output)

if __name__ == "__main__":
    exp = get_experiment_status()
    print(format_progress(exp))

