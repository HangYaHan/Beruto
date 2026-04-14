use beruto::manager::{Manager, ManagerContext, OrderSide, ScoreRankManager, SignalIntent, VoidManager};
use beruto::portfolio::{Portfolio, PortfolioConfig};

fn context_with(intents: Vec<SignalIntent>) -> ManagerContext {
    ManagerContext {
        t_index: 0,
        snapshots: Vec::new(),
        candidate_intents: intents,
        portfolio: Portfolio::new(100_000.0, PortfolioConfig::default()),
    }
}

#[test]
fn void_manager_emits_no_orders() {
    let mut manager = VoidManager;
    let decisions = manager.decide(&context_with(vec![SignalIntent {
        symbol: "159581".to_string(),
        strategy_id: "buyhold".to_string(),
        score: 0.9,
        target_weight: 1.0,
    }]));

    assert!(decisions.is_empty());
}

#[test]
fn score_rank_manager_orders_by_score_and_side() {
    let mut manager = ScoreRankManager;
    let decisions = manager.decide(&context_with(vec![
        SignalIntent {
            symbol: "000001".to_string(),
            strategy_id: "alpha_a".to_string(),
            score: 0.1,
            target_weight: 0.25,
        },
        SignalIntent {
            symbol: "000002".to_string(),
            strategy_id: "alpha_b".to_string(),
            score: 0.8,
            target_weight: 0.5,
        },
        SignalIntent {
            symbol: "000003".to_string(),
            strategy_id: "alpha_c".to_string(),
            score: 0.4,
            target_weight: -0.2,
        },
    ]));

    assert_eq!(decisions.len(), 3);
    assert_eq!(decisions[0].symbol, "000002");
    assert_eq!(decisions[1].symbol, "000003");
    assert_eq!(decisions[2].symbol, "000001");

    assert!(matches!(decisions[0].side, OrderSide::Buy));
    assert!(matches!(decisions[1].side, OrderSide::Sell));
    assert!(matches!(decisions[2].side, OrderSide::Buy));

    assert_eq!(decisions[0].quantity, 0.5);
    assert_eq!(decisions[1].quantity, 0.2);
    assert_eq!(decisions[2].quantity, 0.25);
}
