#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""持续监控实验进度，在关键节点自动更新"""
import re
import time
from pathlib import Path
from datetime import datetime

log_file = Path("experiments/logs/qmix.log")
checkpoints = [100, 200, 300, 400, 500, 600]  # 关键检查点
previous_results = {
    "coverage": 0.730,
    "steps": 2000.0,
}

def get_current_progress():
    """获取当前实验进度"""
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找最新的24x24, 4 UAVs, 障碍密度0.20的训练
    current_exp = None
    start_line = 0
    for i, line in enumerate(reversed(lines[-500:]), 1):
        if "Training QMIX on map=(24, 24), num_uavs=4, obstacle_density=0.2" in line:
            start_line = len(lines) - i
            current_exp = {
                'start_line': start_line,
                'episodes': [],
                'finished': False,
                'start_time': line.split(' - ')[0] if ' - ' in line else None
            }
            break
    
    if not current_exp:
        return None
    
    # 检查是否应用了改进 - 检查开始行之前和之后的日志
    improvements_applied = {
        'dynamic_weight': False,
        'high_density_epsilon': False
    }
    # 检查开始行前后各100行
    check_start = max(0, start_line - 10)
    check_end = min(len(lines), start_line + 100)
    for line in lines[check_start:check_end]:
        line_lower = line.lower()
        if "dynamic obstacle_shaping_weight: 8.0" in line or "obstacle_shaping_weight: 8.0" in line:
            improvements_applied['dynamic_weight'] = True
        if "high-density exploration settings" in line_lower or "epsilon_end=0.12" in line:
            improvements_applied['high_density_epsilon'] = True
    
    # 查找该实验的所有episode
    for line in lines[start_line:]:
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
                break
    
    current_exp['improvements_applied'] = improvements_applied
    return current_exp

def print_monitoring_info(current_exp):
    """打印监控信息"""
    print("=" * 90)
    print("改进效果测试 - 持续监控")
    print("=" * 90)
    print()
    
    if not current_exp:
        print("等待实验开始...")
        return
    
    # 检查改进是否应用
    improvements = current_exp.get('improvements_applied', {})
    print("改进应用状态:")
    print("-" * 90)
    if improvements.get('dynamic_weight'):
        print("  [OK] 动态障碍回避权重: 已应用 (obstacle_shaping_weight=8.0)")
    else:
        print("  [WARNING] 动态障碍回避权重: 未检测到")
    
    if improvements.get('high_density_epsilon'):
        print("  [OK] 高密度探索策略: 已应用 (epsilon_end=0.12)")
    else:
        print("  [WARNING] 高密度探索策略: 未检测到")
    print()
    
    if not current_exp['episodes']:
        print("等待第一个Episode...")
        return
    
    latest = current_exp['episodes'][-1]
    progress = (latest['episode'] / 600) * 100
    
    print(f"实验配置: 24×24 地图, 4 架 UAV, 障碍密度 0.20")
    print(f"开始时间: {current_exp.get('start_time', 'N/A')}")
    print()
    print(f"当前进度: Episode {latest['episode']}/600 ({progress:.1f}%)")
    print(f"当前覆盖率: {latest['coverage']:.3f}")
    print(f"当前步数: {latest['steps']:.1f}")
    print(f"当前 Epsilon: {latest['epsilon']:.3f}")
    print(f"更新时间: {latest['time']}")
    print()
    print("-" * 90)
    
    # 显示最近15个episode
    if len(current_exp['episodes']) >= 15:
        print("最近15个Episode:")
        print("-" * 90)
        for ep in current_exp['episodes'][-15:]:
            print(f"  Episode {ep['episode']:3d}: 覆盖率 {ep['coverage']:.3f}, 步数 {ep['steps']:.1f}, Epsilon {ep['epsilon']:.3f}")
        print()
    
    # 对比分析
    print("对比分析（改进后 vs 改进前）:")
    print("-" * 90)
    print(f"改进前最终结果: 覆盖率 {previous_results['coverage']:.3f}, 步数 {previous_results['steps']:.1f}")
    print(f"当前结果 (Episode {latest['episode']}): 覆盖率 {latest['coverage']:.3f}, 步数 {latest['steps']:.1f}")
    
    improvement = latest['coverage'] - previous_results['coverage']
    improvement_pct = (improvement / previous_results['coverage']) * 100
    
    if improvement > 0.01:
        print(f"[提升] 覆盖率提升: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    elif improvement < -0.01:
        print(f"[下降] 覆盖率下降: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    else:
        print(f"[相近] 覆盖率相近: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    
    # 计算趋势
    if len(current_exp['episodes']) >= 10:
        recent = current_exp['episodes'][-10:]
        avg_coverage = sum(ep['coverage'] for ep in recent) / len(recent)
        if avg_coverage > previous_results['coverage']:
            print(f"[高于] 最近10个Episode平均覆盖率: {avg_coverage:.3f} (高于改进前)")
        elif avg_coverage < previous_results['coverage'] - 0.01:
            print(f"[低于] 最近10个Episode平均覆盖率: {avg_coverage:.3f} (低于改进前)")
        else:
            print(f"[接近] 最近10个Episode平均覆盖率: {avg_coverage:.3f} (接近改进前)")
    print()
    
    # 检查是否达到关键检查点
    if latest['episode'] in checkpoints:
        print(f"[检查点] 达到关键检查点: Episode {latest['episode']}")
        print(f"   覆盖率: {latest['coverage']:.3f} (改进前: {previous_results['coverage']:.3f})")
        if latest['coverage'] > previous_results['coverage']:
            print(f"   [提升] 性能提升: {latest['coverage'] - previous_results['coverage']:+.3f}")
        print()
    
    if current_exp['finished']:
        print("=" * 90)
        print("[完成] 训练完成!")
        print(f"最终覆盖率: {current_exp.get('final_coverage', 'N/A'):.3f}")
        final_improvement = current_exp.get('final_coverage', 0) - previous_results['coverage']
        final_improvement_pct = (final_improvement / previous_results['coverage']) * 100
        print(f"改进效果: {final_improvement:+.3f} ({final_improvement_pct:+.1f}%)")
        if final_improvement > 0.01:
            print("[成功] 改进成功！覆盖率显著提升")
        elif final_improvement > -0.01:
            print("[相近] 改进效果不明显")
        else:
            print("[警告] 需要进一步优化")
        print("=" * 90)
    else:
        # 估算剩余时间
        if len(current_exp['episodes']) >= 2:
            try:
                t1 = datetime.strptime(current_exp['episodes'][-1]['time'], "%Y-%m-%d %H:%M:%S,%f")
                t2 = datetime.strptime(current_exp['episodes'][-2]['time'], "%Y-%m-%d %H:%M:%S,%f")
                time_diff = (t1 - t2).total_seconds()
                ep_diff = current_exp['episodes'][-1]['episode'] - current_exp['episodes'][-2]['episode']
                if ep_diff > 0 and time_diff > 0:
                    time_per_ep = time_diff / ep_diff
                    remaining_eps = 600 - latest['episode']
                    remaining_time = remaining_eps * time_per_ep
                    hours = int(remaining_time // 3600)
                    minutes = int((remaining_time % 3600) // 60)
                    print(f"预计剩余时间: {hours}小时 {minutes}分钟")
            except:
                pass
    
    print()
    print("=" * 90)
    print(f"监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

if __name__ == "__main__":
    current_exp = get_current_progress()
    print_monitoring_info(current_exp)

