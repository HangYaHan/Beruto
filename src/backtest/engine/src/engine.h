#pragma once

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <vector>
#include <stdexcept>

#include "account.h"

class ChronoEngine
{
public:
    explicit ChronoEngine(double initial_cash);
    pybind11::array_t<double> run(const pybind11::array_t<double> &prices,
                                  const pybind11::array_t<double> &signals);

private:
    Account account_;
};
