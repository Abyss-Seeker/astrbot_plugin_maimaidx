# maimaiDX 本地版

这是一个基于 Yuri-YuzuChaN大佬的 maimaiDX 项目的本地版本，由 **AbyssSeeker** 移植，可以在本地运行，无需机器人框架。

注意：因为摆烂和忙等原因，这个项目可能只会进行最低限度的更新，目前功能基本就是所有功能了，不过也够用。

全项目目前共**937MB**，有很多能删掉的代码还没优化。欢迎PR（求求了）。

## 功能特性

- 🎵 完整的舞萌DX查分功能
- 🔍 多种查歌方式（关键词、定数、BPM、曲师、谱师、别名、ID）
- 📊 B50查询和成绩分析
- 🎯 完成表和定数表生成
- 🎨 美观的图片渲染
- 🔄 自动数据更新
- ⚙️ 本地配置文件管理

## 安装要求

- Python 3.8+
- 水鱼账号token（用于访问查分器API）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Abyss-Seeker/maimaiDX-local.git
cd maimaiDX-local
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 及 Chromium

```bash
playwright install --with-deps chromium
```

> 如未安装 Playwright，请先运行：
>
> ```bash
> pip install playwright
> ```

### 4. 配置Token

在 `static/config.json` 文件中配置您的水鱼账号token：

```json
{
    "maimaidxtoken": "您的token",
    "maimaidxproberproxy": false,
    "maimaidxaliasproxy": false
}
```

### 5. 运行程序

```bash
python main.py
```

或者使用启动脚本：

```bash
python run.py
```

## 使用说明

### 基本命令

- `help` —— 查看所有可用命令
- `exit` —— 退出程序

### 查分相关

- `b50 [用户名]` —— 查询B50
- `minfo [用户名] [曲名/ID]` —— 查询游玩数据（支持带空格的曲名）
- `ginfo [难度] [曲名/ID]` —— 查询曲目统计（难度为绿/黄/红/紫/白）
- `score [难度+ID] [分数]` 或 `score [难度] [ID] [分数]` —— 分数线计算

### 查歌相关

- `查歌 [关键词] [页数]` —— 关键词查歌，支持分页
- `定数查歌 [定数下限] [定数上限] [页数]` —— 定数查歌，支持范围和分页
- `bpm查歌 [bpm下限] [bpm上限] [页数]` —— BPM查歌，支持范围和分页
- `曲师查歌 [曲师] [页数]` —— 曲师查歌
- `谱师查歌 [谱师] [页数]` —— 谱师查歌
- `[别名]是什么歌` 或 `[别名]是啥歌` —— 别名查歌
- `id[数字]` —— 通过ID查歌

### 表格/图片相关

- `[难度/plate]完成表 [用户名]` —— 生成完成表（如"紫完成表"）
- `[难度]定数表` —— 生成定数表（如"14+定数表"）

### 数据更新与维护

- `update_alias` 或 `更新别名库` —— 更新别名库
- `update_rating_table` 或 `更新定数表` —— 更新定数表
- `update_plate_table` 或 `更新完成表` —— 更新完成表
- `init` 或 `load` —— 手动重新初始化曲库数据（如数据损坏或首次运行）

### 运势相关

- `今日舞萌`、`今日mai`、`今日运势` —— 今日舞萌运势（自动生成图片）

---

> **注意：**
>
> - 程序会自动检查并加载本地缓存数据，通常无需手动执行 `init` 命令。
> - 所有生成的图片/文件会自动保存到 `output/` 目录。
> - 需要有效的水鱼账号token。

---

## 文件结构

```
maimaiDX-local/
├── main.py              # 主程序入口
├── run.py               # 启动脚本
├── path_manager.py      # 路径管理
├── config_manager.py    # 配置管理
├── __init__.py          # 项目初始化
├── command/             # 命令模块
├── libraries/           # 核心库
├── static/              # 静态资源
│   ├── config.json      # 配置文件
│   ├── mai/             # 游戏资源
│   └── *.ttf            # 字体文件
└── output/              # 输出目录
```

## 配置说明

### config.json

- `maimaidxtoken`: 水鱼账号token（必需）
- `maimaidxproberproxy`: 是否使用代理（可选）
- `maimaidxaliasproxy`: 是否使用别名代理（可选）

## 注意事项

1. **Token配置**: 首次使用前必须在 `static/config.json` 中配置有效的水鱼账号token
2. **数据初始化**: 程序首次运行会自动下载和初始化曲库数据
3. **网络连接**: 需要稳定的网络连接来访问查分器API
4. **资源文件**: 确保 `static` 目录下的字体和图片资源完整

## 故障排除

### 常见问题

1. **Token错误**: 检查 `static/config.json` 中的token是否正确
2. **网络问题**: 检查网络连接，必要时配置代理
3. **数据缺失**: 运行 `init` 命令重新初始化数据
4. **字体缺失**: 确保 `static` 目录下有必要的字体文件

### 错误信息

- `未配置maimaidxtoken`: 需要在配置文件中设置token
- `开发者token有误`: token无效或已过期
- `no such user`: 用户名不存在
- `user not exists`: 用户不存在

## 开发说明

### 路径管理

项目使用 `path_manager.py` 统一管理所有路径，避免相对路径问题。

### 配置管理

使用 `config_manager.py` 管理用户配置，支持动态加载和验证。

### 模块结构

- `command/`: 各种命令的实现
- `libraries/`: 核心功能库
- `static/`: 静态资源和配置

## 许可证

基于原项目的许可证，详见 `LICENSE` 文件。

## 致谢

- 原项目: [Yuri-YuzuChaN/maimaiDX](https://github.com/Yuri-YuzuChaN/maimaiDX)
- 查分器API: [diving-fish/maimaidx-prober](https://github.com/diving-fish/maimaidxprober)
- 各位测试的朋友们
