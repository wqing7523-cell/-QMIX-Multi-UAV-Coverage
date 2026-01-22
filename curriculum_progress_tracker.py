#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""课程学习进度跟踪器"""
import re
from pathlib import Path
from datetime import datetime

def parse_log_for_curriculum_progress(log_file):
    """解析日志获取课程学习进度"""
    if not log_file.exists():
        return None
    
    content = log_file.read_text(encoding="utf-8")
    
    # 查找所有训练记录
    training_pattern = r"Training QMIX on map=\(24, 24\), num_uavs=4, obstacle_density=([\d.]+)"
    trainings = list(re.finditer(training_pattern, content))
    
    if not trainings:
        return None
    
    # 获取最后一次训练
    last_training = trainings[-1]
    obstacle_density = float(last_training.group(1))
    start_idx = last_training.start()
    log_section = content[start_idx:]
    
    # 提取Episode信息
    episode_pattern = r"Episode (\d+) \| coverage_mean=([\d.]+) \| pa_mean=([\d.]+) \| steps_mean=([\d.]+) \| epsilon=([\d.]+)"
    episodes = re.findall(episode_pattern, log_section)
    
    if not episodes:
        return None
    
    latest_episode = episodes[-1]
    episode_num = int(latest_episode[0])
    coverage = float(latest_episode[1])
    pa = float(latest_episode[2])
    steps = float(latest_episode[3])
    epsilon = float(latest_episode[4])
    
    # 检查是否有checkpoint保存
    checkpoint_pattern = r"Checkpoint saved to.*obs(\d+).*\.pt"
    checkpoint_match = re.search(checkpoint_pattern, log_section)
    checkpoint_saved = checkpoint_match is not None
    
    # 检查是否使用了课程学习
    curriculum_pattern = r"Curriculum learning: Loading checkpoint|Loading initial checkpoint"
    curriculum_used = bool(re.search(curriculum_pattern, log_section))
    
    return {
        "obstacle_density": obstacle_density,
        "episode": episode_num,
        "coverage": coverage,
        "pa": pa,
        "steps": steps,
        "epsilon": epsilon,
        "checkpoint_saved": checkpoint_saved,
        "curriculum_used": curriculum_used,
        "progress": (episode_num / 600) * 100,
    }

def format_progress_report(progress_data):
    """格式化进度报告"""
    if not progress_data:
        return "未检测到训练进度"
    
    obs_density = progress_data["obstacle_density"]
    episode = progress_data["episode"]
    coverage = progress_data["coverage"]
    progress = progress_data["progress"]
    
    # 确定当前步骤
    if obs_density == 0.05:
        step = "步骤1: 障碍密度0.05"
        next_step = "→ 步骤2: 障碍密度0.10 (将使用课程学习)"
    elif obs_density == 0.10:
        step = "步骤2: 障碍密度0.10"
        next_step = "→ 步骤3: 障碍密度0.20 (将使用课程学习)"
    elif obs_density == 0.20:
        step = "步骤3: 障碍密度0.20"
        next_step = "→ 课程学习流程完成"
    else:
        step = f"障碍密度{obs_density}"
        next_step = ""
    
    report = f"""
{'='*70}
课程学习进度报告
{'='*70}

当前步骤: {step}
{'='*70}

训练状态:
  - 障碍密度: {obs_density:.2f}
  - 当前Episode: {episode}/600 ({progress:.1f}%)
  - 当前覆盖率: {coverage:.3f}
  - 当前PA: {progress_data['pa']:.3f}
  - 当前步数: {progress_data['steps']:.1f}
  - 当前Epsilon: {progress_data['epsilon']:.3f}
  - 课程学习: {'已启用' if progress_data['curriculum_used'] else '未启用'}
  - Checkpoint: {'已保存' if progress_data['checkpoint_saved'] else '未保存'}

下一步: {next_step}

{'='*70}
更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
"""
    return report

def main():
    log_file = Path("experiments/logs/qmix.log")
    progress_data = parse_log_for_curriculum_progress(log_file)
    report = format_progress_report(progress_data)
    print(report)
    
    # 保存到文件
    report_file = Path("curriculum_progress_report.txt")
    report_file.write_text(report, encoding="utf-8")
    print(f"进度报告已保存到: {report_file}")

if __name__ == "__main__":
    main()

