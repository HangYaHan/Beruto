#include <pybind11/pybind11.h>
#include "engine.h"

namespace py = pybind11;

PYBIND11_MODULE(Beruto_core, m)
{
    py::class_<ChronoEngine>(m, "ChronoEngine", R"pbdoc(Core execution engine with T+1 handling.)pbdoc")
        .def(py::init<double>(), py::arg("initial_cash"))
        .def("run", &ChronoEngine::run, py::arg("prices"), py::arg("signals"),
             R"pbdoc(Run backtest and return equity curve as numpy array.)pbdoc");
}
