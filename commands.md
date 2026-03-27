# Beruto 可用命令清单

本文档列出当前项目中可直接使用的命令，基于现有代码实现整理。

## 一、项目级命令（Cargo）

1. 构建项目

```bash
cargo build
```

2. 运行程序（进入交互式 CLI）

```bash
cargo run
```

3. 运行测试

```bash
cargo test
```

## 二、CLI 交互命令

程序启动后会进入提示符：

```text
beruto>
```

在该提示符下可用命令如下。

### 0) 回测子系统入口

推荐使用新的回测子系统：

```text
backtest
bt
```

进入后提示符变为：

```text
bt>
```

在 `bt>` 中，回测流程支持逐项提示输入参数，也支持快速参数覆盖。

### 1) 帮助与退出

1. 帮助

```text
help
h
?
```

2. 退出

```text
exit
quit
q
```

### 2) 策略相关

1. 列出策略（Linux 风格支持 ls）

```text
strategy list
strategy ls
st list
st ls
```

2. 查看策略详情（Linux 风格支持 sh）

```text
strategy show <name>
strategy sh <name>
st show <name>
st sh <name>
```

当前实现中可用策略名：
- buyhold
- contrarian
- macd
- kdj

### 3) 运行回测（兼容旧入口）

旧入口仍可用，但建议在 `bt>` 里执行。

命令格式（兼容）：

```text
run --symbol <code> --strategy <name> [--initial-capital <n>] [--buy-drop <n>] [--sell-rise <n>]
r --symbol <code> --strategy <name> [--initial-capital <n>] [--buy-drop <n>] [--sell-rise <n>]
```

参数说明：
- --symbol：标的代码，默认值为 159581
- --strategy：策略名，默认值为 buyhold，可选 buyhold / contrarian / macd / kdj
- --initial-capital：初始资金，默认值为 100000
- --buy-drop：仅 contrarian 使用，买入触发阈值（百分比，<=），默认 -1.0
- --sell-rise：仅 contrarian 使用，卖出触发阈值（百分比，>=），默认 1.0
- --fast-period / --slow-period / --signal-period：仅 macd 使用，默认 12 / 26 / 9
- --period：仅 kdj 使用，默认 9

示例：

```text
run --symbol 159581 --strategy buyhold
r --symbol 159581 --strategy contrarian --buy-drop -1.0 --sell-rise 1.0
r --symbol 159581 --strategy macd
r --symbol 159581 --strategy kdj
```

### 3.1) 在 bt> 中运行回测（推荐）

1. 逐项交互输入（推荐）

```text
bt> run
```

系统会依次提示：策略、symbol、initial capital，以及该策略对应参数。每一步可直接回车采用默认值（默认值来自 settings）。

2. 直接输入策略名（快捷）

```text
bt> macd
bt> kdj
bt> contrarian
```

会直接进入该策略的逐项参数提示。

3. 快速模式（显式覆盖）

```text
bt> run --strategy macd --fast-period 8 --slow-period 21 --signal-period 5
```

参数优先级：
- 显式命令行参数
- 交互输入
- settings 默认值
- 策略内建默认值

### 4) 查看排行榜

命令格式：

```text
leaderboard [--top <n>]
lb [--top <n>]
```

参数说明：
- --top：显示前 N 条记录，默认 10

示例：

```text
leaderboard
lb --top 20
```

### 5) 清理回测结果

命令格式：

```text
clean results [--yes]
clean res [--yes]
cl results [--yes]
cl res [--yes]
```

参数说明：
- 不带 --yes：会二次确认
- 带 --yes：跳过确认直接删除结果文件

### 6) 清屏

```text
cls
clear
```

说明：该命令清空当前终端可视区域并将光标移动到左上角。

### 7) 系统设置（已可用）

```text
settings
set
settings <args...>
set <args...>
```

推荐在 `bt>` 中使用，支持以下命令：

```text
settings show [strategy]
settings set global symbol <code>
settings set global initial-capital <n>
settings set <strategy> <param> <value>
settings reset <strategy>
settings save
```

配置会持久化到 `.beruto/settings.json`。

## 三、注意事项

1. CLI 命令只能在 beruto> 交互提示符中执行，不能直接在系统 shell 中执行。
2. 未识别命令会提示 Unknown command。
3. 输入空行会被忽略，不执行任何动作。
