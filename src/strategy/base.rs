use crate::data::data_source::DailyQuote;

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Signal {
	Buy,
	Hold,
	Sell,
}

#[allow(dead_code)]
pub trait Strategy {
	fn name(&self) -> &str;
	fn on_bar(&mut self, quote: &DailyQuote) -> Signal;
	fn description(&self) -> &str;
}
