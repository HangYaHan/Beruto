"""
Backtest 引擎接口：
- run_backtest(strategy, data, portfolio, start, end, config)
- 支持回测结果导出（绩效、逐笔记录）
"""
from typing import Any, Dict, Optional

from src.system.log import get_logger

logger = get_logger(__name__)

class BacktestEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the backtest engine.

        Make `config` optional so callers that haven't wired config yet
        (e.g. a CLI placeholder) won't get a TypeError. This is a thin
        stub; real implementations should require and validate config.
        """
        if config is None:
            logger.info("Initializing BacktestEngine without config (stub)")
        else:
            logger.info("Initializing BacktestEngine with config (Not Implemented)")
        self.config = config

    def run_backtest(self, strategy: Any = None, data_source: Any = None, portfolio: Any = None, start=None, end=None) -> Dict[str, Any]:
        """Run a backtest.

        Parameters are optional in this stub so callers can invoke the
        method during interactive development without wiring full
        arguments. The function logs the call and returns an empty result
        placeholder. Replace with full implementation later.
        """
        logger.info("Running backtest (stub). strategy=%s, data_source=%s, portfolio=%s, start=%s, end=%s",
                    type(strategy).__name__ if strategy is not None else None,
                    type(data_source).__name__ if data_source is not None else None,
                    type(portfolio).__name__ if portfolio is not None else None,
                    start, end)
        # Return a placeholder result structure to avoid callers getting None
        return {
            "status": "not_implemented",
            "equity_curve": [],
            "trades": [],
            "metrics": {},
        }