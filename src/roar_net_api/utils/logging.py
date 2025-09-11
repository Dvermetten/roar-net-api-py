# SPDX-FileCopyrightText: © 2025 Authors of the roar-net-api-py project <https://github.com/roar-net/roar-net-api-py/blob/main/AUTHORS>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Optional
import csv

perflog = logging.getLogger("PerformanceLogger")


class ListLogger(logging.Handler):
    def __init__(self, level=5):
        super().__init__(level=level)
        self.records = []
        self.level = level

    def emit(self, record):
        if record.levelno == self.level:
            self.records.append(self.format(record))


def get_logged_problem(problem_cls, sol_cls):
    class LoggedSolution(sol_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def objective_value(self) -> Optional[int]:
            val = super().objective_value()
            if val is not None:
                global perflog
                perflog.log(level=5, msg=f"{val}")
            return val

    class LoggedProblem(problem_cls):
        def empty_solution(self) -> LoggedSolution:
            sol = super().empty_solution()
            return LoggedSolution(*sol.__dict__.values())

        def random_solution(self) -> LoggedSolution:
            sol = super().random_solution()
            return LoggedSolution(*sol.__dict__.values())

    return LoggedProblem


class PerformanceLogger:
    def __init__(self, filename: Optional[str] = None, algname: Optional[str] = None):
        self.run_id: int = 0
        self.records: dict = {}
        self.finished_runs: list[tuple[list[float], list[float]]] = []
        self.filename = filename if filename is not None else "performance_log.csv"
        self.algname = algname
        self.logger = ListLogger()
        self.logger.setFormatter(logging.Formatter("%(created)f %(message)s"))
        global perflog
        perflog.addHandler(self.logger)
        perflog.setLevel(5)

    def reset(self):
        if self.logger.records is not None and len(self.logger.records) > 1:
            self.finished_runs += self.process_run()
            self.logger.records.clear()
        perflog.log(level=5, msg="inf")
        self.run_id += 1
        return

    def add_attribute(self, key: str, value):
        if self.logger.records is not None and len(self.logger.records) > 1:
            self.reset()
        if not hasattr(self, "attributes"):
            self.attributes = {}
        self.attributes[key] = value

    def process_run(self):
        times, fvals = zip(*[entry.split(" ", 1) for entry in self.logger.records])
        times = [float(t) - float(times[0]) for t in times]
        fvals = [float(f) for f in fvals]
        attributes = getattr(self, "attributes", {})
        records = []
        for t, f in zip(times, fvals):
            record = [self.run_id, int(t * 1e6) + 1, f, *attributes.values()]
            records.append(record)
        return records

    def save_runs(self):
        fieldnames = ["index", "time", "fval", *(getattr(self, "attributes", {}).keys())]
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.finished_runs:
                row = dict(zip(fieldnames, record))
                writer.writerow(row)

        return self.finished_runs

    def close(self):
        self.reset()
        global perflog
        if self.logger:
            perflog.removeHandler(self.logger)
        return self.save_runs()
