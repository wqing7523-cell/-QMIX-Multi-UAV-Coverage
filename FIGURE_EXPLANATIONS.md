# 所有图表详细解释

本文档详细解释论文中使用的所有图表，包括数据含义、关键发现和论文中的使用建议。

---

## Figure 1: QMIX Framework（QMIX框架图）

### 图表类型
**整体架构图** - 展示QMIX系统的完整工作流程

### 图表结构

#### 1. 环境层（Environment Layer）- 顶部浅蓝色框
- **组件**：
  - Map State（地图状态）
  - UAV Positions（UAV位置）
  - Obstacles（障碍物）
- **输出**：观察 (o_1, o_2, ..., o_N)
- **作用**：为每个UAV提供局部观察信息

#### 2. 智能体层（Agent Layer）- 中上部浅橙色框
- **组件**：3个独立的Agent Network
  - Agent 1: o_1 → Q_1
  - Agent 2: o_2 → Q_2
  - Agent N: o_N → Q_N
- **网络结构**：FC1 → RNN → FC2
- **输出**：Q值 (Q_1, Q_2, ..., Q_N)
- **作用**：每个UAV独立计算其动作的Q值

#### 3. 混合层（Mixing Layer）- 中部浅紫色框
- **组件**：
  - Mixing Network（混合网络）
  - Hypernetwork（超网络）
- **功能**：Q_total = Mix(Q_1, Q_2, ..., Q_N, state)
- **输出**：全局Q值 Q_total
- **作用**：将局部Q值混合成全局Q值，保证单调性

#### 4. 动作选择（Action Selection）- 中下部浅绿色框
- **策略**：Epsilon-greedy
  - argmax(Q_total) 或 random
- **作用**：平衡探索和利用

#### 5. 经验回放（Replay Buffer）- 底部左侧浅红色框
- **存储**：(s_t, a_t, r_t, s_{t+1})
- **作用**：存储经验用于训练

#### 6. 训练更新（Training Update）- 底部右侧浅黄色框
- **流程**：TD Loss → Backprop → Update
- **作用**：更新Agent和Mixing Network的参数

### 数据流

1. **前向流（黑色实线）**：
   - 环境 → 智能体 → 混合 → 动作选择 → 环境

2. **经验收集流（红色虚线）**：
   - 环境 → 经验回放缓冲区 → 训练更新

3. **参数更新流（绿色点线）**：
   - 训练更新 → 智能体层/混合层（更新网络参数）

### 关键特点

- **分布式决策**：每个UAV有独立的Agent Network
- **集中式训练**：通过Mixing Network实现全局优化
- **经验回放**：提高样本效率
- **端到端学习**：从观察到动作的完整流程

### 论文中的使用

**位置**：Methodology章节，3.2节（QMIX算法）

**说明文字**：
```
Figure 1 illustrates the QMIX framework for multi-UAV path planning. 
The framework consists of four main components: (1) Environment Layer 
provides observations and rewards; (2) Agent Layer: each UAV has an 
independent agent network that computes local Q-values; (3) Mixing 
Layer: hypernetwork-based mixing network that combines local Q-values 
into a global Q-value; (4) Training Layer: experience replay and 
parameter updates. The solid arrows represent forward data flow, the 
dashed arrows represent experience collection, and the dotted arrows 
represent parameter updates.
```

---

## Figure 2: Coverage Rate vs Obstacle Density（障碍密度对覆盖率的影响）

### 图表类型
**折线图** - 显示障碍密度与平均覆盖率的关系

### 数据解读

| 障碍密度 | 平均覆盖率 | 变化趋势 |
|---------|-----------|---------|
| 0.000 | 0.875 | 起始点 |
| 0.050 | 0.939 | ↑ 上升（+7.3%）|
| 0.100 | 0.873 | ↓ 下降（-7.0%）|
| 0.200 | 0.736 | ↓ 继续下降（-15.7%）|

### 关键发现

1. **非单调性**：
   - 障碍密度从0.0增加到0.05时，覆盖率反而上升（0.875 → 0.939）
   - 这可能是因为：
     - 少量障碍物提供了更好的探索引导
     - 障碍物帮助UAV避免无效的重复探索

2. **性能下降**：
   - 障碍密度超过0.05后，覆盖率开始下降
   - 障碍密度0.20时，覆盖率降至0.736（26.4%的下降）

3. **整体趋势**：
   - 虽然0.05密度时性能最好，但整体上障碍密度增加会导致性能下降
   - 高障碍密度（0.20）场景下，系统仍能保持0.736的覆盖率

### 论文中的使用

**位置**：Results章节，5.2节（性能分析）

**说明文字**：
```
Figure 2 shows the relationship between obstacle density and coverage rate. 
Interestingly, the coverage rate increases from 0.875 to 0.939 when 
obstacle density increases from 0.0 to 0.05, suggesting that a small 
amount of obstacles may provide better exploration guidance. However, 
as obstacle density continues to increase, the coverage rate decreases, 
reaching 0.736 at obstacle density 0.20. This demonstrates the impact 
of obstacles on path planning performance.
```

---

## Figure 3: Coverage Rate vs Map Size（地图大小对覆盖率的影响）

### 图表类型
**柱状图** - 比较不同地图大小下的平均覆盖率

### 数据解读

| 地图大小 | 平均覆盖率 | 颜色 |
|---------|-----------|------|
| 12×12 | 0.921 | 绿色 |
| 16×16 | 0.847 | 浅蓝色 |
| 24×24 | 0.826 | 橙色 |

### 关键发现

1. **性能下降趋势**：
   - 地图越大，平均覆盖率越低
   - 12×12 → 16×16：下降8.0%（0.921 → 0.847）
   - 16×16 → 24×24：下降2.5%（0.847 → 0.826）

2. **可扩展性**：
   - 虽然性能下降，但下降幅度相对较小
   - 24×24地图仍能达到0.826的覆盖率，说明系统具有良好的可扩展性

3. **性能差异**：
   - 12×12和24×24之间的性能差异为9.5%
   - 考虑到地图面积增加了4倍（12² → 24²），这个性能下降是合理的

### 论文中的使用

**位置**：Results章节，5.2节（性能分析）

**说明文字**：
```
Figure 3 illustrates the impact of map size on coverage rate. As the 
map size increases from 12×12 to 24×24, the average coverage rate 
decreases from 0.921 to 0.826, representing a 9.5% decrease. However, 
considering that the map area increases by 4 times, this performance 
degradation is reasonable and demonstrates the scalability of the 
proposed method.
```

---

## Figure 4: Coverage Rate vs Number of UAVs（UAV数量对覆盖率的影响）

### 图表类型
**柱状图** - 比较不同UAV数量下的平均覆盖率

### 数据解读

| UAV数量 | 平均覆盖率 | 颜色 |
|---------|-----------|------|
| 4 | 0.831 | 紫色 |
| 6 | 0.909 | 粉色 |

### 关键发现

1. **性能提升**：
   - 6架UAV比4架UAV的平均覆盖率高9.4%（0.909 vs 0.831）
   - 增加50%的UAV数量（4 → 6），带来9.4%的性能提升

2. **协作优势**：
   - 更多UAV可以并行探索，提高效率
   - 更好的协作能力，覆盖更全面
   - 在复杂场景（如高障碍密度）中优势更明显

3. **成本效益**：
   - 虽然增加UAV数量能提升性能，但需要考虑成本
   - 6架UAV的性能提升（9.4%）相对于UAV数量增加（50%）是合理的

### 论文中的使用

**位置**：Results章节，5.2节（性能分析）

**说明文字**：
```
Figure 4 shows the impact of UAV count on coverage rate. Using 6 UAVs 
achieves an average coverage rate of 0.909, which is 9.4% higher than 
using 4 UAVs (0.831). This demonstrates that increasing the number of 
UAVs improves coverage performance, as more UAVs can explore the map 
in parallel and provide better coordination.
```

---

## Figure 5: Coverage Rate Heatmap（覆盖率热力图）

### 图表类型
**热力图** - 展示所有配置组合的覆盖率

### 数据解读

#### Y轴：地图大小
- 12×12（顶部）
- 16×16（中间）
- 24×24（底部）

#### X轴：配置（UAV数量-障碍密度）
- 4UAV-0.00, 4UAV-0.05, 4UAV-0.10, 4UAV-0.20
- 6UAV-0.00, 6UAV-0.05, 6UAV-0.10, 6UAV-0.20

#### 颜色编码
- **深红色（1.00）**：最高覆盖率
- **红色（0.90-0.95）**：高覆盖率
- **橙色（0.75-0.85）**：中等覆盖率
- **浅黄色（0.60-0.70）**：较低覆盖率

### 关键发现

1. **最佳配置**：
   - 12×12, 4UAV-0.00: 1.00（完美覆盖）
   - 12×12, 6UAV-0.00: 1.00（完美覆盖）
   - 16×16, 6UAV-0.00: 1.00（完美覆盖）

2. **最差配置**：
   - 24×24, 4UAV-0.20: 0.73（最低）
   - 24×24, 6UAV-0.20: 0.76

3. **整体趋势**：
   - **障碍密度影响**：从左到右（0.00 → 0.20），颜色逐渐变浅，覆盖率下降
   - **地图大小影响**：从上到下（12×12 → 24×24），颜色逐渐变浅，覆盖率下降
   - **UAV数量影响**：6UAV配置通常比4UAV配置颜色更深，覆盖率更高

4. **性能分布**：
   - 大部分配置的覆盖率在0.75-0.95之间
   - 只有少数配置达到1.00（完美覆盖）
   - 高障碍密度场景（0.20）下，所有配置的覆盖率都在0.73-0.80之间

### 论文中的使用

**位置**：Results章节，5.2节（性能分析）

**说明文字**：
```
Figure 5 presents a comprehensive heatmap showing coverage rates across 
all configuration combinations. The heatmap reveals that: (1) perfect 
coverage (1.00) is achieved in obstacle-free scenarios for smaller 
maps (12×12 and 16×16); (2) coverage rate generally decreases as 
obstacle density increases; (3) using 6 UAVs typically achieves higher 
coverage than 4 UAVs; (4) larger maps show lower coverage rates, 
especially in high obstacle density scenarios.
```

---

## Figure 6: Training Curve Example（训练曲线示例）

### 图表类型
**折线图** - 显示训练过程中覆盖率的变化

### 数据解读

#### 配置
- 地图大小：24×24
- UAV数量：4
- 障碍密度：0.20

#### 训练进度

| Episode | 覆盖率 | 变化 |
|---------|--------|------|
| 0 | ~0.50 | 起始点 |
| 100 | 0.69 | +38% |
| 200 | 0.76 | +10% |
| 300 | 0.79 | +4% |
| 400 | 0.79 | 0% |
| 500 | 0.79 | 0% |
| 600 | 0.80 | +1% |

### 关键发现

1. **快速学习阶段**（Episode 0-200）：
   - 覆盖率从0.50快速上升到0.76
   - 增长率：+52%（0.50 → 0.76）
   - 说明算法在早期快速学习基本策略

2. **收敛阶段**（Episode 200-400）：
   - 覆盖率从0.76缓慢上升到0.79
   - 增长率：+4%（0.76 → 0.79）
   - 说明算法开始收敛，性能提升变慢

3. **稳定阶段**（Episode 400-600）：
   - 覆盖率在0.79-0.80之间波动
   - 增长率：+1%（0.79 → 0.80）
   - 说明算法已经收敛，性能趋于稳定

4. **训练特点**：
   - **收敛速度**：约200个episodes达到主要性能
   - **最终性能**：0.80的覆盖率，对于高障碍密度场景是合理的
   - **训练稳定性**：后期波动小，训练稳定

### 论文中的使用

**位置**：Experiments章节，4.2节（实验结果）

**说明文字**：
```
Figure 6 shows a training curve example for the most challenging 
scenario (24×24 map, 4 UAVs, obstacle density 0.20). The coverage 
rate increases rapidly during the first 200 episodes, from 0.50 to 
0.76, demonstrating fast initial learning. After Episode 200, the 
learning rate slows down, and the coverage rate converges to around 
0.79-0.80 after 400 episodes. This indicates that the algorithm 
successfully learns effective policies for complex scenarios.
```

---

## Figure 7: Multi-Factor Performance Analysis（多因素性能分析）

### 图表类型
**多子图** - 3个子图展示不同因素的综合影响

### 子图(a): Obstacle Density Impact（障碍密度影响）

#### 按地图大小分组

| 地图大小 | 障碍密度0.00 | 障碍密度0.05 | 障碍密度0.10 | 障碍密度0.20 |
|---------|-------------|-------------|-------------|-------------|
| 12×12 | 1.00 | ~0.95 | ~0.90 | ~0.82 |
| 16×16 | ~0.82 | ~0.95 | ~0.89 | ~0.78 |
| 24×24 | ~0.87 | ~0.92 | ~0.87 | ~0.69 |

#### 关键发现
- **12×12地图**：在所有障碍密度下都表现最好
- **16×16地图**：在障碍密度0.05时达到峰值（0.95）
- **24×24地图**：在高障碍密度（0.20）时性能最低（0.69）

### 子图(b): Map Size Impact（地图大小影响）

#### 按障碍密度分组

| 障碍密度 | 12×12 | 16×16 | 24×24 |
|---------|-------|-------|-------|
| 0.00 | 1.00 | ~0.82 | ~0.84 |
| 0.05 | ~0.95 | ~0.95 | ~0.92 |
| 0.10 | ~0.90 | ~0.89 | ~0.88 |
| 0.20 | ~0.80 | ~0.78 | ~0.69 |

#### 关键发现
- **无障碍场景（0.00）**：12×12表现最好（1.00），16×16和24×24相近（~0.82-0.84）
- **低障碍场景（0.05）**：所有地图大小表现相近（0.92-0.95）
- **高障碍场景（0.20）**：地图越大，性能越低（0.80 → 0.78 → 0.69）

### 子图(c): UAV Count Impact（UAV数量影响）

#### 按障碍密度分组

| 障碍密度 | 4 UAVs | 6 UAVs | 提升 |
|---------|--------|--------|------|
| 0.00 | ~0.84 | ~0.99 | +17.9% |
| 0.20 | ~0.71 | ~0.79 | +11.3% |

#### 关键发现
- **无障碍场景（0.00）**：6架UAV比4架UAV提升17.9%（0.84 → 0.99）
- **高障碍场景（0.20）**：6架UAV比4架UAV提升11.3%（0.71 → 0.79）
- **结论**：增加UAV数量在所有场景下都能提升性能，但在无障碍场景中提升更明显

### 综合发现

1. **因素重要性排序**：
   - 障碍密度 > 地图大小 > UAV数量（对性能的影响程度）

2. **最佳配置**：
   - 12×12地图 + 6架UAV + 无障碍（0.00）：1.00覆盖率

3. **最差配置**：
   - 24×24地图 + 4架UAV + 高障碍（0.20）：0.69覆盖率

4. **性能权衡**：
   - 地图大小和障碍密度是主要限制因素
   - 增加UAV数量可以部分补偿这些限制

### 论文中的使用

**位置**：Results章节，5.2节（性能分析）

**说明文字**：
```
Figure 7 provides a comprehensive multi-factor performance analysis. 
Subplot (a) shows that obstacle density has the most significant 
impact on performance, with 12×12 maps consistently achieving the 
highest coverage. Subplot (b) reveals that map size impact varies 
with obstacle density: in obstacle-free scenarios, smaller maps 
perform better, while in high obstacle density scenarios, the 
performance gap increases. Subplot (c) demonstrates that increasing 
UAV count improves performance in all scenarios, with more pronounced 
benefits in obstacle-free scenarios (17.9% improvement) compared to 
high obstacle density scenarios (11.3% improvement).
```

---

## 总结

### 图表使用建议

1. **Methodology章节**：
   - Figure 1：QMIX框架图（必需）

2. **Experiments章节**：
   - Figure 6：训练曲线示例（展示训练过程）

3. **Results章节**：
   - Figure 2：障碍密度影响（单因素分析）
   - Figure 3：地图大小影响（单因素分析）
   - Figure 4：UAV数量影响（单因素分析）
   - Figure 5：热力图（综合视图）
   - Figure 7：多因素分析（深入分析）

### 关键发现总结

1. **障碍密度**：是影响性能的最主要因素
2. **地图大小**：影响相对较小，系统具有良好的可扩展性
3. **UAV数量**：增加UAV数量能提升性能，但提升幅度有限
4. **训练收敛**：算法在200-400个episodes内收敛
5. **整体性能**：在复杂场景下仍能保持0.73-0.80的覆盖率

---

*最后更新: 2025-11-15 19:10*

