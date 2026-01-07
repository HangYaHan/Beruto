#include "engine.h"
#include <pybind11/stl.h>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

ChronoEngine::ChronoEngine(double initial_cash) : account_{initial_cash, {}} {}

py::array_t<double> ChronoEngine::run(const py::array_t<double> &prices, const py::array_t<double> &signals)
{
    if (prices.ndim() != 2 || signals.ndim() != 2)
    {
        throw std::runtime_error("prices and signals must be 2D arrays");
    }
    if (prices.shape(0) != signals.shape(0) || prices.shape(1) != signals.shape(1))
    {
        throw std::runtime_error("prices and signals shapes must match");
    }
    const auto n_days = prices.shape(0);
    const auto n_stocks = prices.shape(1);

    auto p = prices.unchecked<2>();
    auto s = signals.unchecked<2>();

    std::vector<double> equity;
    equity.reserve(static_cast<size_t>(n_days));

    constexpr double commission = 0.0003;
    constexpr double slippage = 0.0003;

    for (py::ssize_t t = 0; t < n_days; ++t)
    {
        // Pre-market: unlock T+1
        for (auto &kv : account_.positions)
        {
            kv.second.sellable_shares = kv.second.total_shares;
        }

        for (py::ssize_t stock = 0; stock < n_stocks; ++stock)
        {
            const double price = p(t, stock);
            if (price <= 0.0 || !std::isfinite(price))
            {
                continue;
            }
            const double sig = s(t, stock);

            // Simple intent: sig > 0 buy; sig < 0 sell proportional to |sig|
            if (sig > 0.0)
            {
                const double intent_cash = account_.cash * std::min(sig, 1.0);
                const double target_shares = intent_cash / price;
                if (target_shares <= 0.0)
                {
                    continue;
                }
                const double notional = target_shares * price;
                const double cost = notional * (1.0 + commission + slippage);
                if (cost > account_.cash)
                {
                    continue;
                }
                auto &pos = account_.positions[static_cast<int>(stock)];
                const double new_total_shares = pos.total_shares + target_shares;
                const double new_cost = pos.avg_cost * pos.total_shares + notional;
                pos.total_shares = new_total_shares;
                pos.sellable_shares += target_shares * 0.0; // T+1: today buy not sellable
                pos.avg_cost = new_total_shares > 0.0 ? new_cost / new_total_shares : 0.0;
                account_.cash -= cost;
            }
            else if (sig < 0.0)
            {
                auto it = account_.positions.find(static_cast<int>(stock));
                if (it == account_.positions.end())
                {
                    continue;
                }
                auto &pos = it->second;
                const double sell_shares = std::min(pos.sellable_shares, pos.total_shares * std::min(-sig, 1.0));
                if (sell_shares <= 0.0)
                {
                    continue;
                }
                const double notional = sell_shares * price;
                const double proceeds = notional * (1.0 - commission - slippage);
                pos.total_shares -= sell_shares;
                pos.sellable_shares -= sell_shares;
                if (pos.total_shares <= 0.0)
                {
                    pos.total_shares = 0.0;
                    pos.sellable_shares = 0.0;
                    pos.avg_cost = 0.0;
                }
                account_.cash += proceeds;
            }
        }

        double equity_today = account_.cash;
        for (const auto &kv : account_.positions)
        {
            const int stock = kv.first;
            const double px = p(t, stock);
            if (px > 0.0 && std::isfinite(px))
            {
                equity_today += kv.second.total_shares * px;
            }
        }
        equity.push_back(equity_today);
    }

    return py::array_t<double>(equity.size(), equity.data());
}
