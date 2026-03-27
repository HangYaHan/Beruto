use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

pub struct MacdStrategy {
    has_position: bool,
    ema_fast: Option<f64>,
    ema_slow: Option<f64>,
    dea: f64,
    prev_dif: Option<f64>,
    prev_dea: Option<f64>,
    fast_period: f64,
    slow_period: f64,
    signal_period: f64,
}

impl MacdStrategy {
    pub fn new() -> Self {
        Self::with_periods(12.0, 26.0, 9.0)
    }

    pub fn with_periods(fast_period: f64, slow_period: f64, signal_period: f64) -> Self {
        Self {
            has_position: false,
            ema_fast: None,
            ema_slow: None,
            dea: 0.0,
            prev_dif: None,
            prev_dea: None,
            fast_period,
            slow_period,
            signal_period,
        }
    }

    fn ema_next(prev: f64, value: f64, period: f64) -> f64 {
        let alpha = 2.0 / (period + 1.0);
        alpha * value + (1.0 - alpha) * prev
    }
}

impl Strategy for MacdStrategy {
    fn name(&self) -> &str {
        "MACD"
    }

    fn on_bar(&mut self, quote: &DailyQuote) -> Signal {
        let close = quote.close;

        let next_fast = match self.ema_fast {
            Some(prev) => Self::ema_next(prev, close, self.fast_period),
            None => close,
        };
        let next_slow = match self.ema_slow {
            Some(prev) => Self::ema_next(prev, close, self.slow_period),
            None => close,
        };

        self.ema_fast = Some(next_fast);
        self.ema_slow = Some(next_slow);

        let dif = next_fast - next_slow;
        self.dea = Self::ema_next(self.dea, dif, self.signal_period);

        let signal = match (self.prev_dif, self.prev_dea) {
            (Some(prev_dif), Some(prev_dea)) => {
                let cross_up = prev_dif <= prev_dea && dif > self.dea;
                let cross_down = prev_dif >= prev_dea && dif < self.dea;

                if !self.has_position && cross_up {
                    self.has_position = true;
                    Signal::Buy
                } else if self.has_position && cross_down {
                    self.has_position = false;
                    Signal::Sell
                } else {
                    Signal::Hold
                }
            }
            _ => Signal::Hold,
        };

        self.prev_dif = Some(dif);
        self.prev_dea = Some(self.dea);
        signal
    }

    fn description(&self) -> &str {
        "MACD crossover strategy: buy on DIF crossing above DEA, sell on crossing below."
    }
}
