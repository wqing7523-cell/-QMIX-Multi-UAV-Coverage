# 参数调整总结

## 调整的参数

### 1. 障碍回避权重
- **调整前**: `obstacle_shaping_weight=8.0` (高障碍密度)
- **调整后**: `obstacle_shaping_weight=6.5` (高障碍密度)
- **理由**: 8.0过高，导致过度回避障碍，限制探索

### 2. 探索策略
- **调整前**: 
  - `epsilon_end=0.12` (高障碍密度)
  - `epsilon_decay=0.9995` (高障碍密度)
- **调整后**: 
  - `epsilon_end=0.10` (高障碍密度)
  - `epsilon_decay=0.9997` (高障碍密度)
- **理由**: 平衡探索和利用，避免过度探索

### 3. 恢复机制（针对高障碍密度）
- **调整前**: 
  - `coverage_threshold=0.98`
  - `drop_tolerance=0.04`
- **调整后**: 
  - `coverage_threshold_high_density=0.90`
  - `drop_tolerance_high_density=0.05`
- **理由**: 高障碍密度场景下，达到0.98的覆盖率很困难，需要调整阈值

## 新的配置

### `configs/envs/grid_extended.yaml`
```yaml
obstacle_shaping_weights:
  0.05: 5.0
  0.10: 6.0
  0.20: 6.5  # 从8.0降低到6.5
```

### `configs/algos/qmix_obstacle.yaml`
```yaml
epsilon_end_high_density: 0.10  # 从0.12降低到0.10
epsilon_decay_high_density: 0.9997  # 从0.9995减慢到0.9997

recovery:
  coverage_threshold_high_density: 0.90  # 针对高障碍密度场景
  drop_tolerance_high_density: 0.05  # 增加容错
```

## 预期效果

1. **障碍回避权重降低 (8.0 → 6.5)**: 
   - 减少过度回避
   - 增加探索能力
   - 预期覆盖率提升 3-5%

2. **探索策略优化 (epsilon_end=0.12 → 0.10, epsilon_decay=0.9995 → 0.9997)**:
   - 平衡探索和利用
   - 避免过度探索
   - 预期覆盖率提升 2-3%

3. **恢复机制优化 (coverage_threshold=0.98 → 0.90)**:
   - 针对高障碍密度场景调整阈值
   - 增加容错
   - 预期训练更稳定

## 总体预期

- **预期覆盖率**: 从 0.654 提升到 **0.75+**
- **预期改进**: 提升 10-15%

