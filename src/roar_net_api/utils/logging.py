import logging
from typing import Optional

class ListLogger(logging.Handler):
    def __init__(self, level=5):
        super().__init__(level=level)
        self.records = []
        self.level = level

    def emit(self, record):
        if record.levelno == self.level:
            self.records.append(self.format(record))

def get_logged_problem_solution(problem_cls, sol_cls):
    class LoggedSolution(sol_cls):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def objective_value(self) -> Optional[int]:
            val = super().objective_value()
            if val is not None:
                perflog.log(level=5, msg=f"{val}")
            return val

    class LoggedProblem(problem_cls):
        def empty_solution(self) -> LoggedSolution:
            sol = super().empty_solution()
            return LoggedSolution(*sol.__dict__.values())
        
        def random_solution(self) -> LoggedSolution:
            sol = super().random_solution()
            return LoggedSolution(*sol.__dict__.values())
    
    return LoggedProblem, LoggedSolution

def setup_logger(logger: Optional[ListLogger] = None):
    if logger is not None:
        logger.records.clear()
    else:
        global perflog
        perflog = logging.getLogger("PerformanceLogger")
        logger = ListLogger()
        logger.setFormatter(logging.Formatter('%(created)f %(message)s'))
        perflog.addHandler(logger)
        perflog.setLevel(5)
    perflog.log(level=5, msg="inf")
    return logger

def process_run(logger: ListLogger):
    times, fvals = zip(*[entry.split(' ', 1) for entry in logger.records])
    times = [float(t)-float(times[0]) for t in times] 
    fvals = [float(f) for f in fvals]
    return (times, fvals)

def close_logger(logger: ListLogger):
    global perflog
    perflog.removeHandler(logger)
    del logger
    #todo: finish writing json file with meta-data
    return