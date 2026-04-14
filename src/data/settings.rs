use crate::strategy::{default_strategy_param_values, strategy_specs, validate_strategy_param};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};

const APP_DIR: &str = "config";
const SETTINGS_FILE: &str = "config.json";

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum AssetClass {
    Stock,
    Etf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeeRule {
    pub commission_rate: f64,
    pub commission_min: f64,
    pub transfer_rate: f64,
    pub transaction_tax_rate: f64,
}

impl Default for FeeRule {
    fn default() -> Self {
        Self {
            commission_rate: 0.0,
            commission_min: 0.0,
            transfer_rate: 0.0,
            transaction_tax_rate: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DividendTaxBracket {
    pub min_holding_days: u32,
    pub max_holding_days: Option<u32>,
    pub tax_rate: f64,
}

impl Default for DividendTaxBracket {
    fn default() -> Self {
        Self {
            min_holding_days: 0,
            max_holding_days: None,
            tax_rate: 0.0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DividendTaxRule {
    pub brackets: Vec<DividendTaxBracket>,
}

impl Default for DividendTaxRule {
    fn default() -> Self {
        Self {
            brackets: vec![DividendTaxBracket::default()],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountProfile {
    pub stock_fee: FeeRule,
    pub etf_fee: FeeRule,
    pub stock_dividend_tax: DividendTaxRule,
    pub etf_dividend_tax: DividendTaxRule,
    pub auto_classify_by_prefix: bool,
}

impl Default for AccountProfile {
    fn default() -> Self {
        Self {
            stock_fee: FeeRule::default(),
            etf_fee: FeeRule::default(),
            stock_dividend_tax: DividendTaxRule::default(),
            etf_dividend_tax: DividendTaxRule::default(),
            auto_classify_by_prefix: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SymbolOverride {
    pub asset_class: Option<AssetClass>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManagerDefaults {
    pub enabled: bool,
    pub max_symbol_weight: f64,
    pub max_turnover: f64,
    pub position_buckets: Vec<f64>,
}

impl Default for ManagerDefaults {
    fn default() -> Self {
        Self {
            enabled: false,
            max_symbol_weight: 1.0,
            max_turnover: 1.0,
            position_buckets: vec![0.0, 0.25, 0.5, 1.0],
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub default_symbol: String,
    pub default_initial_capital: f64,
    #[serde(default)]
    pub account_profile: AccountProfile,
    #[serde(default)]
    pub symbol_overrides: HashMap<String, SymbolOverride>,
    #[serde(default)]
    pub manager_defaults: ManagerDefaults,
    #[serde(default)]
    pub strategy_params: HashMap<String, HashMap<String, f64>>,
}

impl Default for AppSettings {
    fn default() -> Self {
        let mut strategy_params = HashMap::new();
        for spec in strategy_specs() {
            strategy_params.insert(spec.id.to_string(), default_strategy_param_values(spec.id));
        }

        Self {
            default_symbol: "159581".to_string(),
            default_initial_capital: 100_000.0,
            account_profile: AccountProfile::default(),
            symbol_overrides: HashMap::new(),
            manager_defaults: ManagerDefaults::default(),
            strategy_params,
        }
    }
}

impl AppSettings {
    pub fn merge_with_defaults(mut self) -> Self {
        let defaults = Self::default();

        if self.default_symbol.trim().is_empty() {
            self.default_symbol = defaults.default_symbol;
        }
        if self.default_initial_capital <= 0.0 {
            self.default_initial_capital = defaults.default_initial_capital;
        }

        self.account_profile = self.account_profile_or_default(defaults.account_profile);

        self.manager_defaults = self.manager_defaults.sanitized();

        let override_keys: Vec<String> = self.symbol_overrides.keys().cloned().collect();
        for symbol in override_keys {
            if !is_valid_symbol(&symbol) {
                self.symbol_overrides.remove(&symbol);
            }
        }

        for (strategy_id, default_values) in defaults.strategy_params {
            let entry = self.strategy_params.entry(strategy_id.clone()).or_default();
            for (name, value) in default_values {
                entry.entry(name).or_insert(value);
            }

            let keys: Vec<String> = entry.keys().cloned().collect();
            for key in keys {
                if validate_strategy_param(&strategy_id, &key, *entry.get(&key).unwrap_or(&0.0))
                    .is_err()
                {
                    entry.remove(&key);
                }
            }
        }

        self
    }

    pub fn validate(&self) -> Result<(), String> {
        if !is_valid_symbol(&self.default_symbol) {
            return Err("default_symbol must be 6 digits".to_string());
        }
        if self.default_initial_capital <= 0.0 {
            return Err("default_initial_capital must be > 0".to_string());
        }

        validate_fee_rule(&self.account_profile.stock_fee, "account_profile.stock_fee")?;
        validate_fee_rule(&self.account_profile.etf_fee, "account_profile.etf_fee")?;
        validate_dividend_tax_rule(
            &self.account_profile.stock_dividend_tax,
            "account_profile.stock_dividend_tax",
        )?;
        validate_dividend_tax_rule(
            &self.account_profile.etf_dividend_tax,
            "account_profile.etf_dividend_tax",
        )?;

        for symbol in self.symbol_overrides.keys() {
            if !is_valid_symbol(symbol) {
                return Err(format!("symbol_overrides key '{symbol}' must be 6 digits"));
            }
        }

        if self.manager_defaults.max_symbol_weight <= 0.0 || self.manager_defaults.max_symbol_weight > 1.0 {
            return Err("manager_defaults.max_symbol_weight must be in (0, 1]".to_string());
        }
        if self.manager_defaults.max_turnover < 0.0 {
            return Err("manager_defaults.max_turnover must be >= 0".to_string());
        }
        if self.manager_defaults.position_buckets.is_empty() {
            return Err("manager_defaults.position_buckets cannot be empty".to_string());
        }
        for bucket in &self.manager_defaults.position_buckets {
            if !bucket.is_finite() || *bucket < 0.0 || *bucket > 1.0 {
                return Err("manager_defaults.position_buckets must be finite and in [0, 1]".to_string());
            }
        }

        for (strategy_id, params) in &self.strategy_params {
            for (name, value) in params {
                validate_strategy_param(strategy_id, name, *value)?;
            }
        }

        Ok(())
    }

    pub fn resolve_asset_class(&self, symbol: &str) -> Option<AssetClass> {
        if let Some(override_item) = self.symbol_overrides.get(symbol) {
            if let Some(asset_class) = override_item.asset_class {
                return Some(asset_class);
            }
        }

        if !self.account_profile.auto_classify_by_prefix {
            return None;
        }

        classify_asset_class_by_symbol_prefix(symbol)
    }

    fn account_profile_or_default(&self, default_profile: AccountProfile) -> AccountProfile {
        let mut profile = self.account_profile.clone();

        if profile.stock_dividend_tax.brackets.is_empty() {
            profile.stock_dividend_tax = default_profile.stock_dividend_tax.clone();
        }
        if profile.etf_dividend_tax.brackets.is_empty() {
            profile.etf_dividend_tax = default_profile.etf_dividend_tax;
        }

        profile
    }

    pub fn strategy_values(&self, strategy_id: &str) -> HashMap<String, f64> {
        let mut values = default_strategy_param_values(strategy_id);
        if let Some(saved) = self.strategy_params.get(strategy_id) {
            for (name, value) in saved {
                values.insert(name.clone(), *value);
            }
        }
        values
    }

    pub fn set_strategy_param(
        &mut self,
        strategy_id: &str,
        name: &str,
        value: f64,
    ) -> Result<(), String> {
        validate_strategy_param(strategy_id, name, value)?;
        self.strategy_params
            .entry(strategy_id.to_string())
            .or_default()
            .insert(name.to_string(), value);
        Ok(())
    }

    pub fn reset_strategy_params(&mut self, strategy_id: &str) {
        self.strategy_params.insert(
            strategy_id.to_string(),
            default_strategy_param_values(strategy_id),
        );
    }
}

pub fn app_dir() -> PathBuf {
    Path::new(APP_DIR).to_path_buf()
}

pub fn settings_path() -> PathBuf {
    app_dir().join(SETTINGS_FILE)
}

pub fn load_settings() -> Result<AppSettings, Box<dyn Error>> {
    let path = settings_path();
    if !path.exists() {
        return Ok(AppSettings::default());
    }

    let content = fs::read_to_string(path)?;
    let loaded: AppSettings = serde_json::from_str(&content)?;
    let merged = loaded.merge_with_defaults();
    merged.validate().map_err(|msg| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            format!("Invalid settings: {msg}"),
        )
    })?;
    Ok(merged)
}

pub fn save_settings(settings: &AppSettings) -> Result<PathBuf, Box<dyn Error>> {
    settings.validate().map_err(|msg| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            format!("Invalid settings: {msg}"),
        )
    })?;

    let dir = app_dir();
    fs::create_dir_all(&dir)?;
    let path = settings_path();
    let content = serde_json::to_string_pretty(settings)?;
    fs::write(&path, content)?;
    Ok(path)
}

fn is_valid_symbol(symbol: &str) -> bool {
    symbol.len() == 6 && symbol.chars().all(|c| c.is_ascii_digit())
}

fn validate_fee_rule(rule: &FeeRule, path: &str) -> Result<(), String> {
    if !rule.commission_rate.is_finite() || rule.commission_rate < 0.0 || rule.commission_rate > 1.0 {
        return Err(format!("{path}.commission_rate must be in [0, 1]"));
    }
    if !rule.commission_min.is_finite() || rule.commission_min < 0.0 {
        return Err(format!("{path}.commission_min must be >= 0"));
    }
    if !rule.transfer_rate.is_finite() || rule.transfer_rate < 0.0 || rule.transfer_rate > 1.0 {
        return Err(format!("{path}.transfer_rate must be in [0, 1]"));
    }
    if !rule.transaction_tax_rate.is_finite() || rule.transaction_tax_rate < 0.0 || rule.transaction_tax_rate > 1.0 {
        return Err(format!("{path}.transaction_tax_rate must be in [0, 1]"));
    }
    Ok(())
}

fn validate_dividend_tax_rule(rule: &DividendTaxRule, path: &str) -> Result<(), String> {
    if rule.brackets.is_empty() {
        return Err(format!("{path}.brackets cannot be empty"));
    }

    let mut last_min_days = 0u32;
    for (idx, bracket) in rule.brackets.iter().enumerate() {
        if !bracket.tax_rate.is_finite() || bracket.tax_rate < 0.0 || bracket.tax_rate > 1.0 {
            return Err(format!("{path}.brackets[{idx}].tax_rate must be in [0, 1]"));
        }

        if idx > 0 && bracket.min_holding_days < last_min_days {
            return Err(format!(
                "{path}.brackets[{idx}].min_holding_days must be non-decreasing"
            ));
        }

        if let Some(max_days) = bracket.max_holding_days {
            if max_days < bracket.min_holding_days {
                return Err(format!(
                    "{path}.brackets[{idx}].max_holding_days must be >= min_holding_days"
                ));
            }
        }

        last_min_days = bracket.min_holding_days;
    }

    Ok(())
}

fn classify_asset_class_by_symbol_prefix(symbol: &str) -> Option<AssetClass> {
    let first = symbol.chars().next()?;
    match first {
        '1' | '5' => Some(AssetClass::Etf),
        '0' | '2' | '3' | '6' | '8' | '9' => Some(AssetClass::Stock),
        _ => None,
    }
}

impl ManagerDefaults {
    fn sanitized(mut self) -> Self {
        if !self.max_symbol_weight.is_finite() || self.max_symbol_weight <= 0.0 || self.max_symbol_weight > 1.0 {
            self.max_symbol_weight = 1.0;
        }
        if !self.max_turnover.is_finite() || self.max_turnover < 0.0 {
            self.max_turnover = 1.0;
        }
        self.position_buckets = self
            .position_buckets
            .into_iter()
            .filter(|v| v.is_finite() && *v >= 0.0 && *v <= 1.0)
            .collect();
        if self.position_buckets.is_empty() {
            self.position_buckets = vec![0.0, 0.25, 0.5, 1.0];
        }
        self
    }
}
