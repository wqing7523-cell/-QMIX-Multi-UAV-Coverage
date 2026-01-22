#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析课程学习结果"""
import re
from pathlib import Path
from collections import defaultdict

def extract_training_results(log_file):
    """提取所有训练结果"""
    if not log_file.exists():
        return {}
    
    content = log_file.read_text(encoding="utf-8")
    
    # 查找所有训练记录
    training_pattern = r"Training QMIX on map=\(24, 24\), num_uavs=4, obstacle_density=([\d.]+)"
    trainings = list(re.finditer(training_pattern, content))
    
    results = {}
    
    for training in trainings:
        obstacle_density = float(training.group(1))
        start_idx = training.start()
        
        # 找到下一个训练的开始位置（或文件结尾）
        next_training_idx = len(content)
        if trainings.index(training) < len(trainings) - 1:
            next_training_idx = trainings[trainings.index(training) + 1].start()
        
        log_section = content[start_idx:next_training_idx]
        
        # 检查是否使用了课程学习
        curriculum_pattern = r"Curriculum learning: Loading checkpoint|Loading initial checkpoint from.*obs(\d+)"
        curriculum_match = re.search(curriculum_pattern, log_section)
        curriculum_used = curriculum_match is not None
        curriculum_from = None
        if curriculum_match:
            if curriculum_match.group(1):
                # 提取障碍密度
                obs_str = curriculum_match.group(1)
                if obs_str == "005":
                    curriculum_from = 0.05
                elif obs_str == "010":
                    curriculum_from = 0.10
                elif obs_str == "020":
                    curriculum_from = 0.20
        
        # 提取Episode数据
        episode_pattern = r"Episode (\d+) \| coverage_mean=([\d.]+) \| pa_mean=([\d.]+) \| steps_mean=([\d.]+) \| epsilon=([\d.]+)"
        episodes = re.findall(episode_pattern, log_section)
        
        # 提取关键Episode
        key_episodes = [10, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600]
        episode_data = {}
        for ep_num, cov, pa, steps, eps in episodes:
            ep_num = int(ep_num)
            if ep_num in key_episodes:
                episode_data[ep_num] = {
                    "coverage": float(cov),
                    "pa": float(pa),
                    "steps": float(steps),
                    "epsilon": float(eps),
                }
        
        # 检查checkpoint保存
        checkpoint_pattern = r"Checkpoint saved to.*obs(\d+).*\.pt"
        checkpoint_match = re.search(checkpoint_pattern, log_section)
        checkpoint_saved = checkpoint_match is not None
        
        # 获取最终覆盖率
        final_coverage = None
        if 600 in episode_data:
            final_coverage = episode_data[600]["coverage"]
        
        results[obstacle_density] = {
            "curriculum_used": curriculum_used,
            "curriculum_from": curriculum_from,
            "episodes": episode_data,
            "checkpoint_saved": checkpoint_saved,
            "final_coverage": final_coverage,
        }
    
    return results

def format_results_analysis(results):
    """格式化结果分析"""
    analysis = []
    analysis.append("=" * 70)
    analysis.append("课程学习结果分析")
    analysis.append("=" * 70)
    analysis.append("")
    
    # 按障碍密度排序
    densities = sorted(results.keys())
    
    for density in densities:
        data = results[density]
        analysis.append(f"障碍密度 {density:.2f}:")
        analysis.append("-" * 70)
        analysis.append(f"  课程学习: {'✅ 已启用' if data['curriculum_used'] else '❌ 未启用'}")
        if data['curriculum_from']:
            analysis.append(f"  从障碍密度 {data['curriculum_from']:.2f} 的checkpoint warm-start")
        analysis.append(f"  Checkpoint: {'✅ 已保存' if data['checkpoint_saved'] else '❌ 未保存'}")
        final_cov_str = f"{data['final_coverage']:.3f}" if data['final_coverage'] else 'N/A'
        analysis.append(f"  最终覆盖率: {final_cov_str}")
        
        # 显示关键Episode
        if data['episodes']:
            analysis.append("  关键Episode:")
            key_eps = [10, 50, 100, 200, 300, 400, 500, 600]
            for ep in key_eps:
                if ep in data['episodes']:
                    ep_data = data['episodes'][ep]
                    analysis.append(f"    Episode {ep}: 覆盖率={ep_data['coverage']:.3f}, PA={ep_data['pa']:.3f}")
        analysis.append("")
    
    # 对比分析
    analysis.append("=" * 70)
    analysis.append("对比分析")
    analysis.append("=" * 70)
    analysis.append("")
    
    # 对比障碍密度0.20的结果（有课程学习 vs 无课程学习）
    if 0.20 in results:
        data_020 = results[0.20]
        analysis.append("障碍密度0.20的对比:")
        analysis.append("-" * 70)
        
        # 查找之前无课程学习的0.20结果
        # 这需要从之前的测试中获取
        analysis.append("  当前结果（有课程学习）:")
        if data_020['final_coverage']:
            analysis.append(f"    最终覆盖率: {data_020['final_coverage']:.3f}")
        if 10 in data_020['episodes']:
            analysis.append(f"    Episode 10: {data_020['episodes'][10]['coverage']:.3f}")
        
        analysis.append("")
        analysis.append("  之前结果（无课程学习，第三次调整后）:")
        analysis.append("    最终覆盖率: 0.592")
        analysis.append("    Episode 10: 0.746")
        analysis.append("")
        
        if data_020['final_coverage']:
            improvement = data_020['final_coverage'] - 0.592
            improvement_pct = (improvement / 0.592) * 100
            analysis.append(f"  改进:")
            analysis.append(f"    覆盖率提升: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    
    return "\n".join(analysis)

def main():
    log_file = Path("experiments/logs/qmix.log")
    results = extract_training_results(log_file)
    
    if not results:
        print("未找到训练结果")
        return
    
    analysis = format_results_analysis(results)
    print(analysis)
    
    # 保存到文件
    output_file = Path("curriculum_learning_analysis.txt")
    output_file.write_text(analysis, encoding="utf-8")
    print(f"\n分析结果已保存到: {output_file}")

if __name__ == "__main__":
    main()

