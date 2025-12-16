from __future__ import annotations

# Centralized help texts for CLI commands
# Each entry should explain: purpose, all flags/args, examples.

GENERAL = (
    "FeedbackTrader interactive CLI\n"
    "Commands:\n"
    "    help, h, ?       Show this help\n"
    "    config, cfg      Show or set configuration\n"
    "    backtest, bt     Run a backtest\n"
    "    plot, pt         Plot cached OHLC data\n"
    "    remove, rm       Clean result/log files\n"
    "    exit, quit, q    Exit the CLI\n\n"
    "Tip: use '-?' after any command to see usage.\n"
    "For full docs, see docs/COMMANDS.md\n\n"
    "If you want to see something right now:\n"
    "    plot sh600000 --frame weekly\n"
)

BACKTEST = (
    "Backtest Command\n"
    "Usage:\n"
    "  backtest TASK_NAME [-?]\n"
    "  bt TASK_NAME [-?]\n\n"
    "Args:\n"
    "  TASK_NAME: name of a task json without extension,\n"
    "             located under tasks/. e.g., 't1' or 'task_example'.\n\n"
    "Flags:\n"
    "  -?: show this usage help for the command.\n\n"
    "Examples:\n"
    "  backtest t1\n"
    "  bt task_example\n"
)

PLOT = (
    "Plot Command\n"
    "Usage:\n"
    "  plot SYMBOL [--frame F] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [-?]\n"
    "  pt SYMBOL [--frame F] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [-?]\n\n"
    "Args:\n"
    "  SYMBOL: stock symbol in your dataset, e.g. 'sh600000'.\n\n"
    "Options:\n"
    "  --frame F: timeframe, e.g. 'daily', 'weekly'.\n"
    "  --start YYYY-MM-DD: starting date filter.\n"
    "  --end YYYY-MM-DD: ending date filter.\n\n"
    "Flags:\n"
    "  -?: show this usage help for the command.\n\n"
    "Examples:\n"
    "  plot sh600000 --frame weekly\n"
    "  pt sh601000 --start 2024-01-01 --end 2024-12-31\n"
)

REMOVE = (
    "Remove/Clean Command\n"
    "Usage:\n"
    "  remove -r [leaderboard] | -l | -all [-?]\n"
    "  rm -r [leaderboard] | -l | -all [-?]\n\n"
    "Flags:\n"
    "  -r:  clear result/ outputs except leaderboard.csv.\n"
    "       If followed by 'leaderboard', delete only leaderboard.csv.\n"
    "  -l:  clear logs/ folder.\n"
    "  -all: clear result/ outputs (keep leaderboard.csv) AND logs/.\n"
    "  -?:  show this usage help for the command.\n\n"
    "Examples:\n"
    "  remove -r\n"
    "  rm -r leaderboard\n"
    "  remove -l\n"
    "  rm -all\n"
)

CONFIG = (
    "Config Command\n"
    "Usage:\n"
    "  config [-?]\n"
    "  cfg [-?]\n\n"
    "Description:\n"
    "  Show or set configuration. (Currently not implemented.)\n\n"
    "Flags:\n"
    "  -?: show this usage help for the command.\n"
)

COMMAND_MAP = {
    "help": GENERAL,
    "?": GENERAL,
    "h": GENERAL,
    "backtest": BACKTEST,
    "bt": BACKTEST,
    "plot": PLOT,
    "pt": PLOT,
    "remove": REMOVE,
    "rm": REMOVE,
    "config": CONFIG,
    "cfg": CONFIG,
}


def get_help_text(command: str | None = None) -> str:
    """Return help text for a specific command or general help if None/unknown."""
    if command is None:
        return GENERAL
    return COMMAND_MAP.get(command.lower(), GENERAL)
