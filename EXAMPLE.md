# EXAMPLE

本文档给出当前 CLI 的全部命令、参数含义与示例。

## 基础说明

- 所有命令在 `cargo run` 进入 REPL 后执行。
- 带 `[]` 的参数是可选参数。
- `run` 会先展开为一组 backtest 任务，再逐个执行。

## 1) help

用途：查看命令帮助。

- 主命令：`help`
- 缩写：`h`

示例：
```text
beruto> help
beruto> h
```

## 2) exit / quit

用途：退出Beruto CLI。

- 主命令：`exit`、`quit`
- 缩写：`x`、`q`

示例：
```text
beruto> quit
beruto> q
```

## 3) clear

用途：清屏。

- 主命令：`clear`
- 缩写：`cls`、`cl`

示例：
```text
beruto> clear
beruto> cls
```

## 4) fetch <code>

用途：拉取指定股票代码的日线数据并保存到本地。

参数：
- `<code>`：6 位股票代码，例如 `600519`、`159581`。

行为：
- 保存路径：`data/<code>_daily.csv`
- 若代码不合法会报错。

- 主命令：`fetch <code>`
- 缩写：`f <code>`

示例：
```text
beruto> fetch 600519
beruto> f 159581
```

## 5) strategy list

用途：列出可用策略。

- 主命令：`strategy list`
- 缩写：`st l`

示例：
```text
beruto> strategy list
beruto> st l
```

## 6) strategy show <name>

用途：查看某个策略的说明、参数和用法。

参数：
- `<name>`：策略 ID，例如 `buyhold`、`contrarian`。

- 主命令：`strategy show <name>`
- 缩写：`st sh <name>`

示例：
```text
beruto> strategy show contrarian
beruto> st sh buyhold
```

## 7) backtest

用途：执行单次回测。

主命令：
```text
backtest --symbol <code> --strategy <name> [--initial-capital <n>] [--buy-drop <n>] [--sell-rise <n>]
```

参数：
- `--symbol <code>`：股票代码，默认 `159581`。
- `--strategy <name>`：策略 ID，默认 `buyhold`。
- `--initial-capital <n>`：初始资金，默认 `100000`。
- `--buy-drop <n>`：仅 `contrarian` 使用，买入阈值（百分比），默认 `-1.0`。
- `--sell-rise <n>`：仅 `contrarian` 使用，卖出阈值（百分比），默认 `1.0`。

缩写：`bt`（其余参数不变）

示例：
```text
beruto> backtest --symbol 600519 --strategy buyhold
beruto> bt --symbol 159581 --strategy contrarian --buy-drop -0.8 --sell-rise 1.2
```

## 8) run（批量任务）

用途：批量回测。会先展开为多条 backtest 任务，然后复用回测模块执行。

### 8.1 命令行参数模式

```text
run --symbols <a,b,...> --strategies <s1,s2,...> [--initial-capital <n>] [--buy-drop-values <v1,v2,...>] [--sell-rise-values <v1,v2,...>] [--retry <n>] [--force]
```

参数：
- `--symbols <a,b,...>`：股票代码列表（逗号分隔）。
- `--strategies <s1,s2,...>`：策略列表（逗号分隔），如 `buyhold,contrarian`。
- `--initial-capital <n>`：每个任务的初始资金，默认 `100000`。
- `--buy-drop-values <v1,v2,...>`：`contrarian` 买入阈值列表，默认 `-1.0`。
- `--sell-rise-values <v1,v2,...>`：`contrarian` 卖出阈值列表，默认 `1.0`。
- `--retry <n>`：失败重试次数，默认 `1`。
- `--force`：强制执行，不跳过已完成任务。

行为说明：
- 默认会跳过历史中已完成的同配置任务。
- 会输出批量摘要到 `.beruto/results/batch_<id>.json`。

示例：
```text
beruto> run --symbols 159581,600519 --strategies buyhold,contrarian --buy-drop-values -1.0,-0.8 --sell-rise-values 1.0,1.2
beruto> run --symbols 159581 --strategies buyhold --retry 2 --force
```

### 8.2 计划文件模式

```text
run --plan <path/to/plan.json> [--retry <n>] [--force]
```

参数：
- `--plan <path>`：计划文件路径（JSON）。
- `--retry <n>`、`--force`：可覆盖计划文件中的同名配置。

计划文件字段（当前支持）：
- `symbols`：字符串数组，股票代码列表。
- `strategies`：字符串数组，策略列表。
- `initial_capital`：数字，可选。
- `buy_drop_values`：数字数组，可选。
- `sell_rise_values`：数字数组，可选。
- `retry`：整数，可选。
- `force`：布尔，可选。

计划文件示例（`plan.json`）：
```json
{
  "symbols": ["159581", "600519"],
  "strategies": ["buyhold", "contrarian"],
  "initial_capital": 100000,
  "buy_drop_values": [-1.0, -0.8],
  "sell_rise_values": [1.0, 1.2],
  "retry": 1,
  "force": false
}
```

执行示例：
```text
beruto> run --plan plan.json
beruto> run --plan plan.json --retry 2 --force
```

## 9) leaderboard

用途：按总收益率展示历史回测排行榜。

主命令：
```text
leaderboard [--top <n>]
```

参数：
- `--top <n>`：显示前 N 条，默认 `10`。

缩写：`lb`

示例：
```text
beruto> leaderboard
beruto> lb --top 20
```

## 10) clean results

用途：清理 `.beruto/results` 下的回测结果文件。

主命令：
```text
clean results [--yes]
```

参数：
- `--yes`：不二次确认直接删除。

支持写法：
- `clean results`
- `clean res`
- `clean r`

缩写：`c`

示例：
```text
beruto> clean results
beruto> c r --yes
```

## 11) clean data

用途：清理 `data/` 目录下的文件（用于重拉数据前清空本地数据）。

主命令：
```text
clean data [--yes]
```

参数：
- `--yes`：不二次确认直接删除。

支持写法：
- `clean data`
- `clean d`

缩写：`c`

示例：
```text
beruto> clean data
beruto> c d --yes
```
