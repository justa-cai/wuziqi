# 智能五子棋 Android版

基于Python版本的智能五子棋游戏的Android实现，集成了传统AI算法和大语言模型（LLM）AI。

## 🎮 功能特色

- **双AI模式**: 支持传统AI算法和大语言模型（LLM）AI
- **智能决策**: 支持活三、活四检测和复杂威胁分析
- **中文界面**: 完美支持中文显示和用户交互
- **音效体验**: 内置游戏音效
- **时间限制**: 每步棋限时30秒，增加紧张感
- **自适应难度**: 结合传统评估算法与AI决策

## 🛠️ 技术架构

- **图形界面**: 使用Android Canvas实现
- **AI决策**: 支持OpenAI API兼容服务
- **配置管理**: 通过配置文件管理API密钥
- **音频处理**: 使用AudioTrack生成音频效果

## 🚀 快速开始

### 1. 配置API密钥

在 `Config.java` 中设置你的OpenAI API配置:

```java
public class Config {
    public static String OPENAI_API_KEY = "your-api-key-here";
    public static String OPENAI_BASE_URL = "https://api.openai.com/v1/chat/completions";
    public static String MODEL_NAME = "gpt-4";
}
```

### 2. 环境要求

- Android Studio (推荐最新版本)
- Android SDK with API level 24 or higher
- Java 8 or higher
- Gradle 8.0

### 3. 构建项目

**方法一：使用Android Studio (推荐)**
1. 打开Android Studio
2. 选择 "Open an existing Android Studio project"
3. 导航到 `android` 目录并选择项目
4. 等待Gradle同步完成
5. 点击 "Run" 按钮构建并运行应用

**方法二：使用命令行**
```bash
# 进入项目目录
cd /nvme/work/AI/wuziqi/android

# 创建Gradle Wrapper (需要已安装Gradle)
gradle wrapper --gradle-version 8.0

# 构建debug版本
./gradlew assembleDebug

# 安装到连接的设备
./gradlew installDebug
```

**方法三：使用构建脚本**
```bash
cd /nvme/work/AI/wuziqi/android
./build.sh debug    # 构建debug版本
./build.sh release  # 构建release版本
./build.sh install  # 安装到设备
./build.sh clean    # 清理构建文件
```

## 🔧 常见问题解决

### Gradle构建失败
如果遇到以下错误：
```
Could not initialize class org.codehaus.groovy.runtime.InvokerHelper
Exception java.lang.NoClassDefFoundError: Could not initialize class org.codehaus.groovy.reflection.ReflectionCache
```

这通常是由于Java版本不兼容造成的。请确保：

1. **Java版本兼容**：Gradle 8.0 需要 Java 8, 11, 17 或 21
   ```bash
   java -version
   ```

2. **设置JAVA_HOME环境变量**：
   ```bash
   export JAVA_HOME=/path/to/your/java
   ```

3. **下载完整的Android项目**：
   完整的Android项目应该包含由 `gradle wrapper` 命令生成的二进制文件

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

## 📁 项目结构

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/example/wuziqi/
│   │   │   ├── MainActivity.java      # 主活动
│   │   │   ├── GameEngine.java        # 游戏逻辑引擎
│   │   │   ├── GomokuBoardView.java   # 游戏板视图
│   │   │   ├── OpenAIApiClient.java   # OpenAI API客户端
│   │   │   ├── SoundManager.java      # 音频管理器
│   │   │   └── Config.java            # 配置类
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   └── activity_main.xml  # 主界面布局
│   │   │   ├── values/
│   │   │   │   ├── strings.xml        # 默认字符串资源
│   │   │   │   └── strings-zh.xml     # 中文字符串资源
│   │   └── AndroidManifest.xml        # 应用清单
├── gradle/
│   └── wrapper/
│       ├── gradle-wrapper.jar          # Gradle Wrapper JAR (binary)
│       └── gradle-wrapper.properties   # Gradle Wrapper 配置
├── build.gradle                       # 项目级构建配置
├── settings.gradle                    # 模块设置
├── gradle.properties                  # Gradle 全局配置
├── gradlew                            # Unix Gradle Wrapper 脚本
├── gradlew.bat                        # Windows Gradle Wrapper 脚本
├── build.sh                           # 自定义构建脚本
└── README.md                          # 本文件
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

[GPL]