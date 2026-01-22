# 课程学习状态检查

## 检查结果

### 问题发现

1. **课程学习代码已实现** ✅
   - `run_experiments.py` 中已实现课程学习逻辑（第102-143行）
   - 会自动查找并使用前一个障碍密度的checkpoint

2. **但是课程学习未启用** ❌
   - 缺少障碍密度0.05 (索引1)和0.10 (索引2)的checkpoint
   - 只有障碍密度0.20 (索引3)的checkpoint
   - 所以训练障碍密度0.20时无法找到前一个密度的checkpoint

### Checkpoint状态

| 障碍密度 | 索引 | Checkpoint数量 | 状态 |
|---------|------|---------------|------|
| 0.00 | 0 | 0 | ❌ 缺少 |
| 0.05 | 1 | 0 | ❌ 缺少 |
| 0.10 | 2 | 0 | ❌ 缺少 |
| 0.20 | 3 | 3 | ✅ 存在 |

### 课程学习逻辑

当训练障碍密度0.20 (索引3)时：
1. 会查找障碍密度0.10 (索引2)的checkpoint
2. 如果找到，使用该checkpoint进行warm-start
3. 如果找不到，从头开始训练（当前情况）

## 解决方案

### 方案1: 运行低密度训练生成checkpoint（推荐）

1. **先运行障碍密度0.05的训练**：
   ```bash
   python scripts/run_experiments.py --maps grid_extended --map-indices 2 --uav-indices 0 --algorithms qmix_obstacle --seed 1234 --obstacle-indices 1
   ```

2. **然后运行障碍密度0.10的训练**（使用0.05的checkpoint）：
   ```bash
   python scripts/run_experiments.py --maps grid_extended --map-indices 2 --uav-indices 0 --algorithms qmix_obstacle --seed 1234 --obstacle-indices 2
   ```

3. **最后运行障碍密度0.20的训练**（使用0.10的checkpoint）：
   ```bash
   python scripts/run_experiments.py --maps grid_extended --map-indices 2 --uav-indices 0 --algorithms qmix_obstacle --seed 1234 --obstacle-indices 3
   ```

### 方案2: 检查是否有无障碍（0.0）的checkpoint可以作为起点

如果有无障碍的checkpoint，可以直接使用它作为所有障碍密度的起点。

## 下一步行动

建议：
1. **先运行障碍密度0.05和0.10的训练**（按顺序）
2. **然后重新运行障碍密度0.20的训练**（使用课程学习）
3. **对比结果**（有课程学习 vs 无课程学习）

这样可以验证课程学习是否能提升性能。

