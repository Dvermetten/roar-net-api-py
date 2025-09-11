# SPDX-FileCopyrightText: © 2025 Authors of the roar-net-api-py project <https://github.com/roar-net/roar-net-api-py/blob/main/AUTHORS>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Optional, Union, Type
import csv

from roar_net_api.types import (
    Problem,
    Solution,
)

perflog = logging.getLogger("PerformanceLogger")


class ListLogger(logging.Handler):
    def __init__(self, level: int = 5):
        super().__init__(level=level)
        self.records: list[str] = []
        self.level = level

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == self.level:
            self.records.append(self.format(record))


def get_logged_problem(
    problem_cls: Type[Problem[Any, Any, Solution]], sol_cls: Type[Solution]
) -> Type[Problem[Any, Any, Solution]]:
    def objective_value(self: Any) -> Optional[int]:
        val = sol_cls.objective_value(self)
        if val is not None:
            global perflog
            perflog.log(level=5, msg=f"{val}")
            return int(val)
        return None

    LoggedSolution = type(
        "LoggedSolution",
        (sol_cls,),
        {
            "objective_value": objective_value,
        },
    )

    # Dynamically create LoggedProblem using type()
    def empty_solution(self: Any) -> Solution:
        sol = problem_cls.empty_solution(self)
        return LoggedSolution(*sol.__dict__.values())

    def random_solution(self: Any) -> Solution:
        sol = problem_cls.random_solution(self)
        return LoggedSolution(*sol.__dict__.values())

    LoggedProblem = type(
        "LoggedProblem",
        (problem_cls,),
        {
            "empty_solution": empty_solution,
            "random_solution": random_solution,
        },
    )

    return LoggedProblem


class PerformanceLogger:
    def __init__(self, filename: Optional[str] = None, algname: Optional[str] = None):
        self.run_id: int = 0
        self.finished_runs: list[tuple[Union[int, float, str]]] = []
        self.filename = filename if filename is not None else "performance_log.csv"
        self.algname = algname
        self.logger = ListLogger()
        self.logger.setFormatter(logging.Formatter("%(created)f %(message)s"))
        global perflog
        perflog.addHandler(self.logger)
        perflog.setLevel(5)

    def reset(self) -> None:
        if self.logger.records is not None and len(self.logger.records) > 1:
            self.finished_runs += self.process_run()
            self.logger.records.clear()
        perflog.log(level=5, msg="inf")
        self.run_id += 1
        return

    def add_attribute(self, key: str, value: str) -> None:
        if self.logger.records is not None and len(self.logger.records) > 1:
            self.reset()
        if not hasattr(self, "attributes"):
            self.attributes = {}
        self.attributes[key] = value

    def process_run(self) -> list[tuple[Union[int, float, str]]]:
        times_tuple, fvals = zip(*[entry.split(" ", 1) for entry in self.logger.records])
        times = [float(t) - float(times_tuple[0]) for t in times_tuple]
        attributes = getattr(self, "attributes", {})
        records = []
        for t, f in zip(times, fvals):
            record = tuple([int(self.run_id), int(t * 1e6) + 1, float(f), *attributes.values()])
            records.append(record)
        return records

    def save_runs(self) -> list[tuple[Union[int, float, str]]]:
        fieldnames = ["index", "time", "fval", *(getattr(self, "attributes", {}).keys())]
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.finished_runs:
                row = dict(zip(fieldnames, record))
                writer.writerow(row)

        return self.finished_runs

    def close(self) -> list[tuple[Union[int, float, str]]]:
        self.reset()
        global perflog
        if self.logger:
            perflog.removeHandler(self.logger)
        return self.save_runs()
