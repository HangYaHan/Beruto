use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

pub struct BuyAndHoldStrategy {
	has_position: bool,
}

impl BuyAndHoldStrategy {
	pub fn new() -> Self {
		Self {
			has_position: false,
		}
	}
}

impl Strategy for BuyAndHoldStrategy {
	fn name(&self) -> &str {
		"BuyAndHold"
	}

	fn on_bar(&mut self, _quote: &DailyQuote) -> Signal {
		if !self.has_position {
			self.has_position = true;
			Signal::Buy
		} else {
			Signal::Hold
		}
	}

    fn description(&self) -> &str {
        "A simple buy-and-hold strategy that buys at the first opportunity and holds indefinitely."
    }
}


pub struct ContrarianStrategy {
	has_position: bool,
	last_close: Option<f64>,
	buy_drop_threshold_pct: f64,
	sell_rise_threshold_pct: f64,
}

impl ContrarianStrategy {
	#[allow(dead_code)]
	pub fn new() -> Self {
		Self::with_thresholds(-1.0, 1.0)
	}

	pub fn with_thresholds(buy_drop_threshold_pct: f64, sell_rise_threshold_pct: f64) -> Self {
		Self {
			has_position: false,
			last_close: None,
			buy_drop_threshold_pct,
			sell_rise_threshold_pct,
		}
	}

	#[allow(dead_code)]
	pub fn thresholds(&self) -> (f64, f64) {
		(self.buy_drop_threshold_pct, self.sell_rise_threshold_pct)
	}
}

impl Strategy for ContrarianStrategy {
	fn name(&self) -> &str {
		"ContrarianSimple"
	}

	fn on_bar(&mut self, quote: &DailyQuote) -> Signal {
		let signal = match self.last_close {
			Some(prev_close) if prev_close > 0.0 => {
				let daily_change_pct = (quote.close / prev_close - 1.0) * 100.0;

				if !self.has_position && daily_change_pct <= self.buy_drop_threshold_pct {
					self.has_position = true;
					Signal::Buy
				} else if self.has_position && daily_change_pct >= self.sell_rise_threshold_pct {
					self.has_position = false;
					Signal::Sell
				} else {
					Signal::Hold
				}
			}
			_ => Signal::Hold,
		};

		self.last_close = Some(quote.close);
		signal
	}

        fn description(&self) -> &str {
		"A simple contrarian strategy that buys after a configured daily drop and sells after a configured daily rise."
	}
}
