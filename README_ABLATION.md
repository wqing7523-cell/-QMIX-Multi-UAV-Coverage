# 消融实验说明

## 实验配置

表5的消融实验包含4个配置：

1. **Baseline** (`qmix_baseline.yaml`): 无势能奖励、无动态恢复
2. **+势能奖励** (`qmix_potential_only.yaml`): 有势能奖励、无动态恢复
3. **+动态恢复** (`qmix_recovery_only.yaml`): 无势能奖励、有动态恢复
4. **完整模型** (`qmix_full.yaml`): 有势能奖励、有动态恢复

## 运行方法

### 方法1：使用运行脚本（推荐）

```bash
python run_ablation_experiments.py
```

脚本会自动运行所有4个配置的实验。

### 方法2：手动运行单个实验

```bash
# Baseline
python src/algos/qmix/train_qmix.py \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_baseline.yaml \
    --seed 1234

# +势能奖励
python src/algos/qmix/train_qmix.py \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_potential_only.yaml \
    --seed 1234

# +动态恢复
python src/algos/qmix/train_qmix.py \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_recovery_only.yaml \
    --seed 1234

# 完整模型
python src/algos/qmix/train_qmix.py \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_full.yaml \
    --seed 1234
```

## 实验设置

- **地图大小**: 24×24
- **UAV数量**: 6
- **障碍密度**: 0.20
- **训练轮数**: 600 episodes
- **随机种子**: 1234

## 结果收集

实验完成后，结果会保存在：
- 日志文件: `experiments/logs/`
- 模型检查点: `experiments/checkpoints/`

## 注意事项

⚠️ **动态恢复机制**: 当前代码中可能还没有实现动态恢复机制。如果 `enable_dynamic_recovery: true` 的配置运行失败，需要先实现动态恢复机制。

实现动态恢复机制需要：
1. 性能监控（计算滑动平均覆盖率）
2. Checkpoint保存（保存最佳性能模型）
3. 性能退化检测（判断是否需要恢复）
4. 模型回滚和epsilon提升

如果需要，我可以帮你实现动态恢复机制。

