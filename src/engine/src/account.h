#pragma once

#include <unordered_map>

struct Position
{
    double total_shares{0.0};
    double sellable_shares{0.0};
    double avg_cost{0.0};
};

struct Account
{
    double cash{0.0};
    std::unordered_map<int, Position> positions;
};
