# 智能五子棋AI (Intelligent Gomoku AI)

一个集成了大语言模型（LLM）的智能五子棋游戏，融合了传统AI策略和现代AI技术，提供具有挑战性的游戏体验。

## 🎮 功能特色

- **双AI模式**: 支持传统AI算法和大语言模型（LLM）AI
- **智能决策**: 支持活三、活四检测和复杂威胁分析
- **中文界面**: 完美支持中文显示和用户交互
- **音效体验**: 内置游戏音效，支持自定义音效文件
- **时间限制**: 每步棋限时30秒，增加紧张感
- **游戏日志**: 详细的调试日志记录游戏过程
- **自适应难度**: 结合传统评估算法与AI决策

## 🛠️ 技术架构

- **图形界面**: 使用 Pygame 实现
- **AI决策**: 支持 OpenAI API 兼容服务
- **配置管理**: 支持环境变量配置
- **音频处理**: 使用 Numpy 生成音频效果
- **国际化**: 支持中文字体渲染

## 📋 依赖要求

- Python 3.8+
- pygame
- openai
- python-dotenv
- numpy

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件并配置以下参数：

```bash
OPENAI_API_KEY=
OPENAI_BASE_URL=
MODEL_NAME=
```

### 3. 运行游戏

```bash
# 普通模式（仅使用传统AI）
python main.py

# 启用LLM模式
python main.py --llm
```

## 🎯 游戏策略

### AI决策优先级：

1. **立即获胜**: 检测并执行能立即获胜的棋步
2. **紧急防守**: 阻止对手的立即获胜机会
3. **活四攻击/防守**: 识别并利用活四机会，或阻止对手活四
4. **活三策略**: 检测活三并进行攻击或防守
5. **评估策略**: 基于位置价值评估进行决策

### 传统AI算法：

- Alpha-Beta剪枝搜索
- 位置评估函数
- 威胁检测系统

### LLM增强：

- 当启用LLM时，AI会将当前棋盘状态发送到大语言模型
- LLM以职业棋手的视角分析局势并提供最佳落子建议
- 结合传统算法和AI智慧的混合决策模式

## ⚙️ 自定义配置

在 `.env` 文件中可配置：

- `OPENAI_API_KEY`: API密钥
- `OPENAI_BASE_URL`: API基础URL
- `MODEL_NAME`: 使用的模型名称

在 `main.py` 文件中可配置：

- `BOARD_SIZE`: 棋盘大小（默认15x15）
- `CELL_SIZE`: 每格像素大小
- `MAX_TURN_TIME`: 每步最大时间（默认30秒）

## 🔧 开发说明

### 音效系统

- 游戏会尝试加载 `place.wav`（落子音效）和 `win.wav`（胜利音效）
- 如果文件不存在，则自动生成简单音效
- 使用 Numpy 生成正弦波音频

### 字体支持

- 优先使用支持中文的字体（Noto Sans CJK 等）
- 自动降级到系统字体以保证中文显示

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

[GPL]

## 🙏 致谢

- [Pygame](https://www.pygame.org/) - 游戏开发框架
- [OpenAI](https://openai.com/) - AI模型接口
- [python-dotenv](https://github.com/theskumar/python-dotenv) - 环境变量管理