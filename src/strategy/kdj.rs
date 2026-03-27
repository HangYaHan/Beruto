use std::collections::VecDeque;

use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

pub struct KdjStrategy {
    has_position: bool,
    period: usize,
    high_window: VecDeque<f64>,
    low_window: VecDeque<f64>,
    k: f64,
    d: f64,
    prev_k: Option<f64>,
    prev_d: Option<f64>,
}

impl KdjStrategy {
    pub fn new() -> Self {
        Self::with_period(9)
    }

    pub fn with_period(period: usize) -> Self {
        Self {
            has_position: false,
            period,
            high_window: VecDeque::new(),
            low_window: VecDeque::new(),
            k: 50.0,
            d: 50.0,
            prev_k: None,
            prev_d: None,
        }
    }

    fn push_window(window: &mut VecDeque<f64>, value: f64, limit: usize) {
        window.push_back(value);
        if window.len() > limit {
            window.pop_front();
        }
    }
}

impl Strategy for KdjStrategy {
    fn name(&self) -> &str {
        "KDJ"
    }

    fn on_bar(&mut self, quote: &DailyQuote) -> Signal {
        Self::push_window(&mut self.high_window, quote.high, self.period);
        Self::push_window(&mut self.low_window, quote.low, self.period);

        let highest = self
            .high_window
            .iter()
            .fold(f64::MIN, |acc, value| acc.max(*value));
        let lowest = self
            .low_window
            .iter()
            .fold(f64::MAX, |acc, value| acc.min(*value));

        let rsv = if highest <= lowest {
            50.0
        } else {
            ((quote.close - lowest) / (highest - lowest) * 100.0).clamp(0.0, 100.0)
        };

        self.k = (2.0 / 3.0) * self.k + (1.0 / 3.0) * rsv;
        self.d = (2.0 / 3.0) * self.d + (1.0 / 3.0) * self.k;

        let signal = match (self.prev_k, self.prev_d) {
            (Some(last_k), Some(last_d)) => {
                let cross_up = last_k <= last_d && self.k > self.d;
                let cross_down = last_k >= last_d && self.k < self.d;

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

        self.prev_k = Some(self.k);
        self.prev_d = Some(self.d);
        signal
    }

    fn description(&self) -> &str {
        "KDJ crossover strategy: buy on K crossing above D, sell on crossing below."
    }
}
