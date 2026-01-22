# QMIX模型框架详细说明（用于论文）

## 🏗️ 整体架构概述

本论文提出的系统基于QMIX（Q-value Mixing）多智能体强化学习算法，用于解决多UAV集群路径规划问题。系统由四个主要组件构成：环境层、智能体层、混合层和训练层。

---

## 📐 详细架构描述

### 1. 环境层 (Environment Layer)

**GridWorldEnv**: 多UAV网格世界环境

**状态表示**:
- **地图信息**: 
  - 访问状态矩阵 (H × W): 0=未访问, 1=已访问, 2=障碍物, 3=UAV位置
  - 障碍物分布: 根据障碍密度随机生成
- **UAV信息**:
  - 位置坐标: (x_i, y_i) for i = 1, ..., N
  - 能量状态: energy_i
  - 历史动作: action_history
- **观察维度**: 
  ```
  obs_dim = H × W × 3 + 1 + N × 3
  ```
  - 地图特征: H × W × 3 (访问状态、障碍物、UAV位置)
  - 全局信息: 1 (覆盖率)
  - UAV信息: N × 3 (位置x, 位置y, 能量)

**奖励函数**:
- 新单元格奖励: R_new = 358.74
- 已访问单元格: R_visited = -31.14
- 障碍物碰撞: R_obstacle = -225.17
- 完成覆盖: R_complete = 1000.0
- 形状奖励: R_shaping = -shaping_weight × distance_to_unvisited + obstacle_shaping_weight × distance_to_obstacle

---

### 2. 智能体层 (Agent Layer)

**Agent Network**: 每个UAV有独立的Q网络

**网络结构**:
```
输入: 观察 o_i (obs_dim)
  ↓
FC1: Linear(obs_dim → hidden_dim) + ReLU
  ↓
RNN: GRUCell(hidden_dim → hidden_dim)
  ↓
FC2: Linear(hidden_dim → action_dim)
  ↓
输出: Q值 Q_i(a_i | o_i) (action_dim)
```

**参数**:
- obs_dim: 观察维度（取决于地图大小和UAV数量）
- hidden_dim: 64（可配置）
- action_dim: 4（上、下、左、右）

**特点**:
- 每个UAV有独立的Agent Network
- 使用GRU处理时序信息，捕捉历史依赖
- 输出每个动作的Q值，用于动作选择

---

### 3. 混合层 (Mixing Layer)

**Mixing Network**: 混合各个agent的Q值成全局Q值

**网络结构**:
```
输入:
  - Agent Q值: [Q_1, Q_2, ..., Q_N] (N × 1)
  - 全局状态: state (state_dim)
  ↓
Hypernetwork (生成混合权重):
  - Hyper_W1: state → (N × mixing_hidden_dim)
  - Hyper_B1: state → mixing_hidden_dim
  - Hyper_W2: state → mixing_hidden_dim
  - Hyper_B2: state → 1
  ↓
混合过程:
  - Hidden = ReLU([Q_1, ..., Q_N] × W1 + B1)
  - Q_total = Hidden × W2 + B2
  ↓
输出: 全局Q值 Q_total(s, a_1, ..., a_N)
```

**参数**:
- num_agents: UAV数量 (4 或 6)
- state_dim: 全局状态维度（与obs_dim相同）
- mixing_hidden_dim: 32（可配置）
- hyper_hidden_dim: 64（可配置）

**关键特性**:
- **单调性保证**: 使用绝对值确保 ∂Q_total/∂Q_i ≥ 0
- **状态依赖**: 混合权重根据全局状态动态生成
- **可分解性**: 全局Q值可以分解为局部Q值的混合

---

### 4. 训练层 (Training Layer)

**Replay Buffer**: 经验回放缓冲区

- 存储格式: (s_t, a_t, r_t, s_{t+1}, done)
- 缓冲区大小: 12000
- 采样方式: 随机采样batch_size=64

**TD Loss计算**:
```
Q_target = r_t + γ × max_{a'} Q_target(s_{t+1}, a')
Loss = (Q_total(s_t, a_t) - Q_target)²
```

**参数更新**:
- 优化器: RMSprop
- 学习率: 0.0002
- 折扣因子: γ = 0.99
- 目标网络更新间隔: 400 episodes

---

## 🔄 训练流程

### 前向传播阶段

1. **环境观察**
   ```
   环境状态 s_t
     ↓
   各UAV观察 (o_1, o_2, ..., o_N)
   ```

2. **Q值计算**
   ```
   各UAV观察 → Agent Networks → Q值 (Q_1, Q_2, ..., Q_N)
   ```

3. **全局Q值**
   ```
   Q值 + 全局状态 → Mixing Network → Q_total
   ```

4. **动作选择**
   ```
   Epsilon-greedy:
     - 以概率(1-ε)选择: argmax_a Q_total
     - 以概率ε随机选择动作
   ```

5. **环境执行**
   ```
   执行动作 → 新状态 s_{t+1} + 奖励 r_t
   ```

### 训练更新阶段

1. **经验收集**
   ```
   (s_t, a_t, r_t, s_{t+1}, done) → Replay Buffer
   ```

2. **批次采样**
   ```
   从Replay Buffer采样batch_size=64个经验
   ```

3. **TD Loss计算**
   ```
   使用Target Networks计算Q_target
   Loss = (Q_total - Q_target)²
   ```

4. **参数更新**
   ```
   反向传播 → 更新Agent Networks和Mixing Network
   ```

5. **目标网络更新**
   ```
   每400个episodes更新Target Networks
   ```

---

## 📊 框架图说明

### 主要数据流

1. **前向流（黑色实线）**:
   - 环境 → 智能体 → 混合 → 动作选择 → 环境

2. **经验收集流（红色虚线）**:
   - 环境 → 经验回放缓冲区

3. **训练更新流（绿色点线）**:
   - 经验回放 → 训练更新 → 智能体/混合网络

### 关键组件

- **环境层**: 提供状态、观察、奖励
- **智能体层**: 计算局部Q值
- **混合层**: 混合成全局Q值
- **动作选择**: Epsilon-greedy策略
- **经验回放**: 存储和采样经验
- **训练更新**: TD Loss和参数更新

---

## 🎨 论文中的框架图建议

### 图1: 整体架构图（推荐）

应该包含：
1. 环境层（顶部）
2. 智能体层（中间上部）
3. 混合层（中间）
4. 动作选择（中间下部）
5. 经验回放和训练（底部）

显示：
- 数据流（实线箭头）
- 经验收集（虚线箭头）
- 参数更新（点线箭头）

### 图2: Agent Network详细图（可选）

显示：
- 输入层 → FC1 → RNN → FC2 → 输出层
- 标注每层的维度

### 图3: Mixing Network详细图（可选）

显示：
- Agent Q值输入
- Hypernetwork结构
- 混合过程
- 全局Q值输出

---

## 📝 论文中的文字描述建议

### Methodology章节结构

1. **3.1 环境设置**
   - GridWorld环境描述
   - 状态和观察表示
   - 动作空间
   - 奖励函数设计

2. **3.2 QMIX算法**
   - 3.2.1 Agent Network架构
   - 3.2.2 Mixing Network架构
   - 3.2.3 训练流程

3. **3.3 实现细节**
   - 网络参数设置
   - 训练超参数
   - 优化策略（动态权重、探索策略等）

---

*最后更新: 2025-11-15 18:50*

