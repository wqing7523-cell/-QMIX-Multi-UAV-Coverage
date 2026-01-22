#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查课程学习状态和checkpoint可用性"""
import yaml
from pathlib import Path

# 检查环境配置
env_config = Path("configs/envs/grid_extended.yaml")
with open(env_config, "r", encoding="utf-8") as f:
    env_data = yaml.safe_load(f)

obstacle_density = env_data.get("obstacle_density", [])
print("障碍密度列表:", obstacle_density)
print("障碍密度索引映射:")
for i, d in enumerate(obstacle_density):
    print(f"  索引 {i}: {d:.2f}")

# 检查checkpoint
checkpoint_dir = Path("experiments/checkpoints")
print("\n检查各障碍密度的checkpoint (24x24, 4 UAV):")
map_size = 24
uav_count = 4

obs_densities = [0.0, 0.05, 0.10, 0.20]
for obs_d in obs_densities:
    obs_str = f"obs{obs_d:.2f}".replace(".", "")
    # 查找匹配的checkpoint
    pattern = f"qmix_map{map_size}_uavs{uav_count}_{obs_str}_*.pt"
    matches = list(checkpoint_dir.glob(pattern))
    
    print(f"\n  障碍密度 {obs_d:.2f} (索引 {obs_densities.index(obs_d)}): {len(matches)} 个checkpoint")
    if matches:
        latest = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        print(f"    最新: {latest.name}")
        print(f"    时间: {latest.stat().st_mtime}")
    else:
        print(f"    [缺少checkpoint]")

# 检查课程学习逻辑
print("\n课程学习逻辑检查:")
print("  当训练障碍密度0.20 (索引3)时，应该使用障碍密度0.10 (索引2)的checkpoint")
obs_idx_high = 3  # 障碍密度0.20
prev_obs_idx = obs_idx_high - 1  # 障碍密度0.10
prev_obs_density = obstacle_density[prev_obs_idx]
prev_obs_str = f"obs{prev_obs_density:.2f}".replace(".", "")
pattern = f"qmix_map{map_size}_uavs{uav_count}_{prev_obs_str}_*.pt"
checkpoints = list(checkpoint_dir.glob(pattern))

if checkpoints:
    checkpoints.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    checkpoint_path = str(checkpoints[0])
    print(f"  [OK] 找到checkpoint: {checkpoint_path}")
    print(f"  可以在训练障碍密度0.20时使用此checkpoint进行课程学习")
else:
    print(f"  [警告] 未找到障碍密度{prev_obs_density:.2f}的checkpoint")
    print(f"  需要先运行障碍密度{prev_obs_density:.2f}的训练以生成checkpoint")

