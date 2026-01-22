# 第三次参数调整总结

## 调整的参数

### 1. 障碍回避权重
- **调整前**: `obstacle_shaping_weight=6.5` (高障碍密度)
- **调整后**: `obstacle_shaping_weight=7.0` (高障碍密度)
- **理由**: 6.5可能过低，7.0是中等值，平衡障碍回避和探索

### 2. 探索策略
- **调整前**: 
  - `epsilon_end=0.10` (高障碍密度)
  - `epsilon_decay=0.9997` (高障碍密度)
  - `epsilon_accel_episode=400`
- **调整后**: 
  - `epsilon_end=0.11` (高障碍密度) - 从0.10增加到0.11，平衡探索和利用
  - `epsilon_decay=0.9996` (高障碍密度) - 从0.9997调整到0.9996，中等衰减速度
  - `epsilon_accel_episode=350` - 从400提前到350，在崩溃前加速
- **理由**: 使用更平衡的探索策略，提前加速避免性能崩溃

### 3. 恢复机制（针对高障碍密度）
- **调整前**: 
  - `coverage_threshold=0.90`
  - `drop_tolerance=0.05`
  - `start_episode=150`
- **调整后**: 
  - `coverage_threshold=0.85` - 从0.90降低到0.85，更容易触发
  - `drop_tolerance=0.06` - 从0.05增加到0.06，增加容错
  - `start_episode=100` - 从150提前到100，更早开始监控
- **理由**: 增强恢复机制，更早触发，更容易恢复

## 新的配置

### `configs/envs/grid_extended.yaml`
```yaml
obstacle_shaping_weights:
  0.05: 5.0
  0.10: 6.0
  0.20: 7.0  # 从6.5调整到7.0
```

### `configs/algos/qmix_obstacle.yaml`
```yaml
epsilon_end_high_density: 0.11  # 从0.10调整到0.11
epsilon_decay_high_density: 0.9996  # 从0.9997调整到0.9996
epsilon_accel_episode: 350  # 从400提前到350

recovery:
  coverage_threshold_high_density: 0.85  # 从0.90降低到0.85
  drop_tolerance_high_density: 0.06  # 从0.05增加到0.06
  start_episode: 100  # 从150提前到100
```

## 预期效果

1. **障碍回避权重调整 (6.5 → 7.0)**: 
   - 平衡障碍回避和探索
   - 预期覆盖率提升 2-3%

2. **探索策略优化 (epsilon_end=0.10 → 0.11, epsilon_decay=0.9997 → 0.9996, accel_episode=400 → 350)**:
   - 更平衡的探索和利用
   - 提前加速避免崩溃
   - 预期覆盖率提升 3-5%

3. **恢复机制优化 (coverage_threshold=0.90 → 0.85, drop_tolerance=0.05 → 0.06, start_episode=150 → 100)**:
   - 更容易触发恢复
   - 更早开始监控
   - 预期训练更稳定

## 总体预期

- **预期覆盖率**: 从 0.545 提升到 **0.70+**
- **预期改进**: 提升 15-20%
- **预期稳定性**: 避免Episode 350的崩溃

## 对比历史结果

| 版本 | 最终覆盖率 | 变化 |
|------|-----------|------|
| 改进前 | 0.730 | - |
| 第一次改进后 | 0.654 | -0.076 (-10.4%) |
| 第二次调整后 | 0.545 | -0.185 (-25.3%) |
| **第三次调整后** | **待测试** | **目标: 0.70+** |

