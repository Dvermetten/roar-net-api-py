import logging
from typing import Optional

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
        self.logger.setFormatter(logging.Formatter('%(created)f %(message)s'))
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
        times, fvals = zip(*[entry.split(' ', 1) for entry in self.logger.records])
        times = [float(t)-float(times[0]) for t in times]
        fvals = [float(f) for f in fvals]
        return (times, fvals)

    def save_runs(self):
        import pandas as pd
        df_records = pd.DataFrame(
            [
                {'index': idx, 'time': t, 'fval': f}
                for idx, run in enumerate(self.finished_runs)
                for t, f in zip(run[0], run[1])
            ]
        )
        # Transform time to int (in microseconds, starting at 1)
        df_records['time'] = (df_records['time']*1e6 + 1).astype(int)
        if self.algname is not None:
            df_records['algname'] = self.algname

        df_records.to_csv(self.filename, index=False, header=True)
        return

    def close(self):
        self.reset()
        global perflog
        if self.logger:
            perflog.removeHandler(self.logger)
        self.save_runs()
        return

    