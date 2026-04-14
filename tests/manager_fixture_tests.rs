use beruto::manager::{Manager, ManagerContext, ManagerKind, OrderSide, ScoreRankManager, SignalIntent, VoidManager};
use beruto::portfolio::{Portfolio, PortfolioConfig};
use serde::Deserialize;
use std::fs;
use std::path::Path;

#[derive(Debug, Deserialize)]
struct ManagerFixture {
    name: String,
    kind: String,
    status: String,
    description: String,
    #[serde(default)]
    inputs: FixtureInputs,
    #[serde(default)]
    expected: Option<ExpectedOutcome>,
}

#[derive(Debug, Default, Deserialize)]
struct FixtureInputs {
    #[serde(default)]
    t_index: usize,
    #[serde(default)]
    cash: f64,
    #[serde(default)]
    candidate_intents: Vec<FixtureIntent>,
}

#[derive(Debug, Deserialize)]
struct FixtureIntent {
    symbol: String,
    strategy_id: String,
    score: f64,
    target_weight: f64,
}

#[derive(Debug, Deserialize)]
struct ExpectedOutcome {
    #[serde(default)]
    order_count: Option<usize>,
    #[serde(default)]
    symbols: Vec<String>,
    #[serde(default)]
    sides: Vec<String>,
    #[serde(default)]
    note: Option<String>,
}

fn build_context(inputs: &FixtureInputs) -> ManagerContext {
    ManagerContext {
        t_index: inputs.t_index,
        snapshots: Vec::new(),
        candidate_intents: inputs
            .candidate_intents
            .iter()
            .map(|intent| SignalIntent {
                symbol: intent.symbol.clone(),
                strategy_id: intent.strategy_id.clone(),
                score: intent.score,
                target_weight: intent.target_weight,
            })
            .collect(),
        portfolio: Portfolio::new(inputs.cash, PortfolioConfig::default()),
    }
}

#[test]
fn manager_fixtures_are_valid_json_cases() {
    let fixtures = read_manager_fixtures();
    assert!(!fixtures.is_empty(), "manager fixtures folder should not be empty");

    for fixture in fixtures {
        assert!(!fixture.name.trim().is_empty(), "fixture name must not be empty");
        assert!(!fixture.kind.trim().is_empty(), "fixture kind must not be empty");
        assert!(!fixture.status.trim().is_empty(), "fixture status must not be empty");
        assert!(!fixture.description.trim().is_empty(), "fixture description must not be empty");

        if fixture.status == "implemented" {
            let expected = fixture
                .expected
                .as_ref()
                .unwrap_or_else(|| panic!("implemented fixture {} must have expected outcome", fixture.name));
            let context = build_context(&fixture.inputs);
            let decisions = run_manager(&fixture.kind, context);

            if let Some(expected_count) = expected.order_count {
                assert_eq!(decisions.len(), expected_count, "{} order count mismatch", fixture.name);
            }

            let actual_symbols: Vec<String> = decisions.iter().map(|decision| decision.symbol.clone()).collect();
            assert_eq!(actual_symbols, expected.symbols, "{} symbol ordering mismatch", fixture.name);

            let actual_sides: Vec<String> = decisions
                .iter()
                .map(|decision| match decision.side {
                    OrderSide::Buy => "buy".to_string(),
                    OrderSide::Sell => "sell".to_string(),
                })
                .collect();
            assert_eq!(actual_sides, expected.sides, "{} side mapping mismatch", fixture.name);
        }
    }
}

#[test]
fn naive_dca_fixture_is_documented_but_not_implemented_yet() {
    let fixture = load_fixture("naive_dca_daily.json");
    assert_eq!(fixture.status, "planned");
    assert_eq!(fixture.kind, "planned");
    assert!(fixture.expected.is_some());
    assert_eq!(fixture.expected.as_ref().and_then(|expected| expected.note.as_deref()), Some("future implementation placeholder"));
}

#[test]
fn manager_kind_serializes_as_kebab_case() {
    let kind: ManagerKind = serde_json::from_str("\"score-rank\"").expect("score-rank should deserialize");
    assert!(matches!(kind, ManagerKind::ScoreRank));

    let json = serde_json::to_string(&ManagerKind::ScoreRank).expect("score-rank should serialize");
    assert_eq!(json, "\"score-rank\"");
}

fn run_manager(kind: &str, context: ManagerContext) -> Vec<beruto::manager::OrderDecision> {
    match kind {
        "void" => {
            let mut manager = VoidManager;
            manager.decide(&context)
        }
        "score-rank" => {
            let mut manager = ScoreRankManager;
            manager.decide(&context)
        }
        other => panic!("unsupported implemented manager fixture kind: {other}"),
    }
}

fn read_manager_fixtures() -> Vec<ManagerFixture> {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("managers");
    let mut fixtures = Vec::new();

    for entry in fs::read_dir(dir).expect("failed to read managers directory") {
        let entry = entry.expect("failed to read manager fixture entry");
        let path = entry.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("json") {
            continue;
        }

        fixtures.push(load_fixture_from_path(&path));
    }

    fixtures.sort_by(|a, b| a.name.cmp(&b.name));
    fixtures
}

fn load_fixture(name: &str) -> ManagerFixture {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("managers").join(name);
    load_fixture_from_path(&path)
}

fn load_fixture_from_path(path: &Path) -> ManagerFixture {
    let content = fs::read_to_string(path).expect("failed to read manager fixture");
    serde_json::from_str(&content).expect("failed to parse manager fixture JSON")
}
