# AlphaZero风格五子棋（五子连珠）实现

本项目实现了一个五子棋（五子连珠）的深度强化学习系统，灵感来源于AlphaZero算法。该系统结合了神经网络与蒙特卡洛树搜索（MCTS），通过自我对弈学习最佳走棋策略。

## 架构概述

该系统由以下主要组件构成：

1. **五子棋游戏环境** (`gomoku_game.py`): 处理游戏规则、状态表示和有效走棋生成
2. **神经网络** (`nnet.py`): 输出策略（走棋概率）和价值（位置评估）
3. **MCTS算法** (`mcts.py`): 使用神经网络指导搜索并选择走棋
4. **自我对弈生成** (`selfplay.py`): 通过AI自我对弈创建训练数据
5. **训练循环** (`training.py`): 基于自我对弈数据训练神经网络
6. **推理系统** (`inference.py`): 支持与训练好的模型对弈
7. **主脚本** (`main.py`): 协调整个处理流程

## 依赖要求

- Python 3.7+
- PyTorch
- NumPy

## 用法

### 训练模型

从零开始训练模型：

```bash
python main.py --mode train --board_size 15 --num_iterations 10 --num_mcts_sims 50
```

这将：
1. 使用当前神经网络生成自我对弈游戏
2. 在生成的数据上训练网络
3. 在每次迭代后保存检查点

### 测试实现

运行所有组件的测试：

```bash
python main.py --mode test
```

### 与训练模型对弈

与训练好的模型对弈：

```bash
python main.py --mode play --model_path ./checkpoints/best.pth.tar --board_size 15
```

### AI对战演示

观看两个AI玩家对战：

```bash
python main.py --mode demo --model_path ./checkpoints/best.pth.tar --board_size 15
```

## AlphaZero算法详情

该实现遵循AlphaZero方法：

1. **神经网络**: 获取一个棋盘位置并输出策略向量（选择每步棋的概率）和标量值（预估胜率）

2. **MCTS**: 使用神经网络指导蒙特卡洛模拟并改进走棋选择

3. **自我对弈**: 系统通过自我对弈进行游戏，使用当前神经网络通过MCTS选择走棋

4. **训练**: 神经网络在自我对弈数据上进行训练，以预测MCTS生成的策略和价值

## 主要特性

- **残差网络架构**: 具有策略头和价值头的深度残差网络
- **数据增强**: 使用棋盘对称性增加训练数据
- **神经引导的MCTS**: 结合MCTS搜索与神经网络评估
- **自我对弈训练**: 通过自我对弈持续改进

## 超参数

系统使用多个关键超参数：
- `num_iterations`: 训练过程中的迭代次数
- `num_eps_per_iteration`: 每次迭代的自我对弈游戏数
- `num_mcts_sims`: 每步棋的MCTS模拟次数
- `batch_size`: 训练批次大小
- `learning_rate`: 神经网络训练的学习率
- `temperature`: 自我对弈期间走棋选择的温度

## 文件结构

- `gomoku_game.py`: 游戏环境和规则
- `nnet.py`: 神经网络架构
- `mcts.py`: 蒙特卡洛树搜索实现
- `selfplay.py`: 自我对弈数据生成
- `training.py`: 训练循环实现
- `inference.py`: 推理和游戏功能
- `main.py`: 主入口点

## 训练过程

训练过程遵循AlphaZero方法：

1. 使用随机权重初始化神经网络
2. 每次迭代:
   - 使用当前网络通过MCTS生成自我对弈游戏
   - 收集训练数据（棋盘位置、MCTS策略、游戏结果）
   - 在收集的数据上训练神经网络
3. 重复直到达到期望性能

## 说明

- 训练可能需要大量计算资源和时间
- 实现针对标准15x15五子棋进行了优化，但支持不同的棋盘尺寸
- MCTS实现通过UCB平衡探索和利用
- 神经网络架构遵循AlphaZero论文中的残差块