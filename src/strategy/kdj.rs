use std::collections::VecDeque;

use crate::data::data_source::DailyQuote;
use crate::strategy::base::{Signal, Strategy};

pub struct KdjStrategy {
	period: usize,
	buy_threshold: f64,
	sell_threshold: f64,
	has_position: bool,
	highs: VecDeque<f64>,
	lows: VecDeque<f64>,
	k_value: f64,
	d_value: f64,
}

impl KdjStrategy {
	#[allow(dead_code)]
	pub fn new() -> Self {
		Self::with_params(9, 20.0, 80.0)
	}

	#[allow(dead_code)]
	pub fn with_params(period: usize, buy_threshold: f64, sell_threshold: f64) -> Self {
		Self {
			period: period.max(1),
			buy_threshold,
			sell_threshold,
			has_position: false,
			highs: VecDeque::new(),
			lows: VecDeque::new(),
			k_value: 50.0,
			d_value: 50.0,
		}
	}

	#[allow(dead_code)]
	pub fn params(&self) -> (usize, f64, f64) {
		(self.period, self.buy_threshold, self.sell_threshold)
	}

	fn update_window(window: &mut VecDeque<f64>, value: f64, period: usize) {
		window.push_back(value);
		if window.len() > period {
			window.pop_front();
		}
	}

	fn highest_high(&self) -> f64 {
		self.highs
			.iter()
			.copied()
			.fold(f64::NEG_INFINITY, f64::max)
	}

	fn lowest_low(&self) -> f64 {
		self.lows
			.iter()
			.copied()
			.fold(f64::INFINITY, f64::min)
	}
}

impl Strategy for KdjStrategy {
	fn name(&self) -> &str {
		"KDJ"
	}

	fn on_bar(&mut self, quote: &DailyQuote) -> Signal {
		Self::update_window(&mut self.highs, quote.high, self.period);
		Self::update_window(&mut self.lows, quote.low, self.period);

		let highest_high = self.highest_high();
		let lowest_low = self.lowest_low();
		let range = highest_high - lowest_low;
		let rsv = if range.abs() < f64::EPSILON {
			50.0
		} else {
			((quote.close - lowest_low) / range * 100.0).clamp(0.0, 100.0)
		};

		self.k_value = (2.0 * self.k_value + rsv) / 3.0;
		self.d_value = (2.0 * self.d_value + self.k_value) / 3.0;
		let j_value = 3.0 * self.k_value - 2.0 * self.d_value;

		if !self.has_position && j_value <= self.buy_threshold {
			self.has_position = true;
			Signal::Buy
		} else if self.has_position && j_value >= self.sell_threshold {
			self.has_position = false;
			Signal::Sell
		} else {
			Signal::Hold
		}
	}

	fn description(&self) -> &str {
		"A KDJ oscillator strategy that buys when J falls below the buy threshold and sells when J rises above the sell threshold."
	}
}

#[cfg(test)]
mod tests {
	use super::KdjStrategy;
	use crate::data::data_source::DailyQuote;
	use crate::strategy::base::{Signal, Strategy};

	fn quote(date: &str, close: f64) -> DailyQuote {
		DailyQuote {
			date: date.to_string(),
			open: close,
			noon_close: close,
			close,
			high: close,
			low: close,
			volume: 1.0,
			amount: 1.0,
			amplitude_pct: 0.0,
		}
	}

	#[test]
	fn kdj_generates_buy_and_sell_on_reversal() {
		let mut strategy = KdjStrategy::with_params(3, 20.0, 80.0);
		let prices = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0];
		let mut signals = Vec::new();

		for (index, price) in prices.iter().enumerate() {
			signals.push(strategy.on_bar(&quote(&format!("2026-04-{index:02}", index = index + 1), *price)));
		}

		assert!(signals.contains(&Signal::Buy), "expected at least one buy signal");
		assert!(signals.contains(&Signal::Sell), "expected at least one sell signal");
	}
}