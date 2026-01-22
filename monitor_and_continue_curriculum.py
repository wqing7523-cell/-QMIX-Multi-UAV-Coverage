#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""监控训练进度并自动继续课程学习流程"""
import time
import subprocess
import sys
from pathlib import Path
import re

def check_training_complete(log_file, target_episode=600):
    """检查训练是否完成"""
    if not log_file.exists():
        return False, 0
    
    content = log_file.read_text(encoding="utf-8")
    
    # 查找最新的训练记录
    pattern = r"Training QMIX on map=\(24, 24\), num_uavs=4, obstacle_density=0\.0?5"
    matches = list(re.finditer(pattern, content))
    if not matches:
        return False, 0
    
    # 获取最后一次训练的开始位置
    last_match = matches[-1]
    start_idx = last_match.start()
    log_section = content[start_idx:]
    
    # 查找Episode 600
    episode_pattern = rf"Episode {target_episode} \| coverage_mean=([\d.]+)"
    match = re.search(episode_pattern, log_section)
    if match:
        coverage = float(match.group(1))
        # 检查是否有checkpoint保存
        checkpoint_pattern = r"Checkpoint saved to.*obs00[5-9].*\.pt"
        if re.search(checkpoint_pattern, log_section):
            return True, coverage
    return False, 0

def get_current_episode(log_file):
    """获取当前训练的episode数"""
    if not log_file.exists():
        return 0
    
    content = log_file.read_text(encoding="utf-8")
    # 查找最新的Episode记录
    pattern = r"Episode (\d+) \| coverage_mean=([\d.]+)"
    matches = re.findall(pattern, content)
    if matches:
        return int(matches[-1][0])
    return 0

def run_training(obstacle_index, seed=1234):
    """运行训练"""
    venv_python = Path('.venv') / 'Scripts' / 'python.exe'
    cmd = [
        str(venv_python),
        "scripts/run_experiments.py",
        "--maps", "grid_extended",
        "--map-indices", "2",
        "--uav-indices", "0",
        "--algorithms", "qmix_obstacle",
        "--seed", str(seed),
        "--obstacle-indices", str(obstacle_index),
    ]
    print(f"\n{'='*70}")
    print(f"启动训练: 障碍密度索引 {obstacle_index}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*70}\n")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    return process

def main():
    log_file = Path("experiments/logs/qmix.log")
    
    # 课程学习流程：0.05 -> 0.10 -> 0.20
    curriculum_steps = [
        (1, 0.05, "障碍密度0.05"),
        (2, 0.10, "障碍密度0.10 (使用0.05的checkpoint)"),
        (3, 0.20, "障碍密度0.20 (使用0.10的checkpoint)"),
    ]
    
    seed = 1234
    
    for step_idx, (obs_idx, density, description) in enumerate(curriculum_steps):
        print(f"\n{'='*70}")
        print(f"步骤 {step_idx + 1}/{len(curriculum_steps)}: {description}")
        print(f"{'='*70}")
        
        # 检查是否已完成
        if obs_idx == 1:  # 第一个步骤，检查是否正在运行
            current_episode = get_current_episode(log_file)
            if current_episode > 0 and current_episode < 600:
                print(f"检测到正在运行的训练: Episode {current_episode}/600")
                print("等待训练完成...")
            elif current_episode >= 600:
                is_complete, coverage = check_training_complete(log_file, 600)
                if is_complete:
                    print(f"训练已完成: 最终覆盖率 {coverage:.3f}")
                    continue
        else:
            is_complete, coverage = check_training_complete(log_file, 600)
            if is_complete:
                print(f"训练已完成: 最终覆盖率 {coverage:.3f}")
                continue
        
        # 启动训练
        process = run_training(obs_idx, seed)
        
        # 监控进度
        print(f"监控训练进度 (每30秒检查一次)...")
        while True:
            time.sleep(30)  # 每30秒检查一次
            
            current_episode = get_current_episode(log_file)
            if current_episode >= 600:
                # 再等待一下确保checkpoint已保存
                time.sleep(10)
                is_complete, coverage = check_training_complete(log_file, 600)
                if is_complete:
                    print(f"\n训练完成: 最终覆盖率 {coverage:.3f}")
                    break
            
            if current_episode > 0:
                progress = (current_episode / 600) * 100
                print(f"进度: Episode {current_episode}/600 ({progress:.1f}%)")
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                # 进程已结束，检查是否成功
                if process.returncode == 0:
                    print("训练进程已结束")
                    time.sleep(5)  # 等待日志写入
                    is_complete, coverage = check_training_complete(log_file, 600)
                    if is_complete:
                        print(f"训练完成: 最终覆盖率 {coverage:.3f}")
                        break
                else:
                    print(f"训练进程异常退出，返回码: {process.returncode}")
                    print("请检查日志文件")
                    sys.exit(1)
        
        print(f"\n步骤 {step_idx + 1} 完成，等待5秒后继续下一步...")
        time.sleep(5)
    
    print(f"\n{'='*70}")
    print("课程学习流程全部完成！")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

