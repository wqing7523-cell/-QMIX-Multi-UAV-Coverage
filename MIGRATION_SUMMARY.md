# 论文相关内容迁移总结

## 迁移完成时间
2024年（具体日期）

## 已迁移的文件

### 论文文件
- ✅ `paper_chinese.md` - 中文论文（已更新）
- ✅ `MODIFICATION_SUMMARY.md` - 修改总结
- ✅ `oral_presentation_outline.md` - 口头汇报大纲
- ✅ `presentation_slides_outline.md` - 幻灯片大纲
- ✅ `快速回答卡片.md` - 快速回答卡片
- ✅ `研究方向回答.md` - 研究方向回答
- ✅ `通俗版开场白.md` - 通俗版开场白

### 消融实验相关
- ✅ `run_ablation_basic.py` - 运行前两个消融实验的脚本
- ✅ `run_ablation_experiments.py` - 运行所有消融实验的脚本
- ✅ `README_ABLATION.md` - 消融实验说明文档

### 配置文件
- ✅ `configs/algos/qmix_baseline.yaml` - Baseline配置
- ✅ `configs/algos/qmix_potential_only.yaml` - +势能奖励配置
- ✅ `configs/algos/qmix_recovery_only.yaml` - +动态恢复配置
- ✅ `configs/algos/qmix_full.yaml` - 完整模型配置
- ✅ `configs/envs/grid_ablation.yaml` - 消融实验环境配置

### 提交相关
- ✅ `submissions/sensors/` - Sensors期刊提交相关文件

## 代码更新

### `src/algos/qmix/train_qmix.py`
- ✅ 添加了 `enable_potential_reward` 配置支持
- ✅ 支持通过配置文件控制势能奖励的开关

## 运行消融实验

### 方法1：运行前两个实验（推荐）
```bash
cd C:\Users\44358\Desktop\uav-qmix
python run_ablation_basic.py
```

### 方法2：手动运行单个实验
```bash
cd C:\Users\44358\Desktop\uav-qmix

# Baseline
python -m src.algos.qmix.train_qmix \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_baseline.yaml \
    --seed 1234

# +势能奖励
python -m src.algos.qmix.train_qmix \
    --env-config configs/envs/grid_ablation.yaml \
    --algo-config configs/algos/qmix_potential_only.yaml \
    --seed 1234
```

## 实验配置

- **地图大小**: 24×24
- **UAV数量**: 6
- **障碍密度**: 0.20
- **训练轮数**: 600 episodes
- **随机种子**: 1234

## 结果位置

- **日志文件**: `experiments/logs/`
- **模型检查点**: `experiments/checkpoints/`
- **论文图表**: `experiments/figures/paper/`

## 注意事项

1. 所有论文相关内容现在都在 `uav-qmix` 目录下，方便复现和查找
2. 运行实验前请确保在 `uav-qmix` 目录下执行命令
3. 动态恢复机制尚未实现，目前只能运行前两个实验（Baseline 和 +势能奖励）

