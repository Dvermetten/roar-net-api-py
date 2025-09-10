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
        if self.logger.records is not None and len(self.logger.records) > 0:
            self.finished_runs.append(self.process_run())
            self.logger.records.clear()
        perflog.log(level=5, msg="inf")
        return

    def process_run(self):
        times, fvals = zip(*[entry.split(" ", 1) for entry in self.logger.records])
        times = [float(t) - float(times[0]) for t in times]
        fvals = [float(f) for f in fvals]
        return (times, fvals)

    def save_runs(self):
        records = []
        for idx, run in enumerate(self.finished_runs):
            for t, f in zip(run[0], run[1]):
                record = {
                    "index": idx,
                    "time": int(t * 1e6 + 1),
                    "fval": f
                }
                if self.algname is not None:
                    record["algname"] = self.algname
                records.append(record)

        # Determine fieldnames
        fieldnames = ["index", "time", "fval"]
        if self.algname is not None:
            fieldnames.append("algname")

        # Write to CSV
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record)

        return records

    def close(self):
        self.reset()
        global perflog
        if self.logger:
            perflog.removeHandler(self.logger)
        self.save_runs()
        return
