use crate::strategy::{default_strategy_param_values, strategy_specs, validate_strategy_param};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};

const APP_DIR: &str = ".beruto";
const SETTINGS_FILE: &str = "settings.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub default_symbol: String,
    pub default_initial_capital: f64,
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
    Ok(loaded.merge_with_defaults())
}

pub fn save_settings(settings: &AppSettings) -> Result<PathBuf, Box<dyn Error>> {
    let dir = app_dir();
    fs::create_dir_all(&dir)?;
    let path = settings_path();
    let content = serde_json::to_string_pretty(settings)?;
    fs::write(&path, content)?;
    Ok(path)
}
