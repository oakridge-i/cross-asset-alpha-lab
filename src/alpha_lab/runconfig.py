"""Run window and scenario of a simulation (moved unchanged from engine.py, which re-exports them, so that the P_A1
provider can build its validation runs without importing the engine)."""
from dataclasses import dataclass
from alpha_lab.normalize import finite_number

GRID = {'cost': (0, 0.001, 0.002, 0.005), 'lag': (1, 2), 'reserve': (0, 0.01, 0.02), 'proxy_pay_days': (0, 10, 30)}


@dataclass(frozen=True)
class Scenario:
    cost: float = 0.001
    lag: int = 1
    reserve: float = 0.01
    proxy_pay_days: int = 10

    def __post_init__(self):
        for name, allowed in GRID.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f'{name} must be one of {allowed}: {getattr(self, name)!r}')


@dataclass(frozen=True)
class RunConfig:
    start_session: str
    end_session: str
    decision_sessions: tuple[str, ...] | None = None
    scenario: Scenario = Scenario()
    initial_cash: float = 100000.0

    def __post_init__(self):
        if not (finite_number(self.initial_cash) and self.initial_cash > 0):
            raise ValueError(f'initial_cash must be a finite number > 0: {self.initial_cash!r}')
        object.__setattr__(self, 'initial_cash', float(self.initial_cash))
