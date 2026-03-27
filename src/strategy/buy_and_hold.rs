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
