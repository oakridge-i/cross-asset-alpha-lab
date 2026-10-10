"""Selection rules of the adaptive policy P_A1: year mapping, validation segment, close-set choice and selection
stability (N5 spec 5.2-5.4, P4-P7), and the Policy provider that applies them. The rules are pure functions; the
provider receives the simulation function and the candidate providers from the engine registry and writes no files."""
import copy
import math
import numpy as np
from alpha_lab import inference
from alpha_lab.features import xnys_month_end
from alpha_lab.hypotheses import Decision
from alpha_lab.metrics import UTILITY_PENALTY, excess_series
from alpha_lab.normalize import calendar

CANDIDATES = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4')
FALLBACK = 'H1_252_3'
TOLERANCE = 0.001
PENALTY = 1.5
FIRST_YEAR = 2014
LAST_YEAR = 2022
HISTORY_YEARS = 5  # validation years 2 + context years 3 (spec 5.2 item 1)

assert PENALTY == UTILITY_PENALTY


def _check_year(year):
    if not FIRST_YEAR <= year <= LAST_YEAR:
        raise ValueError(f'selection year {year} is outside {FIRST_YEAR}..{LAST_YEAR}')


def selection_year(decision_session):
    """Selection year of a decision session 'YYYY-MM-DD' (P4).

    The year of the session, plus one when the session is the last XNYS session of December. This equals the year of
    the execution session under the one-session lag of the N5 scenario. Raises ValueError outside 2014..2022."""
    year = int(decision_session[:4])
    if decision_session == xnys_month_end(f'{year}-12'):
        year += 1
    _check_year(year)
    return year


def validation_segment(year):
    """Validation segment of selection year `year` (P5): last XNYS session of December year-3 to that of year-1."""
    _check_year(year)
    return xnys_month_end(f'{year - 3}-12'), xnys_month_end(f'{year - 1}-12')


def choose(utilities, order=CANDIDATES):
    """Apply the close-set rule (P6) and the fallback (P7) to {candidate: U}.

    Candidates are ranked by their position in `order`; a key not in `order` raises ValueError. With every U finite,
    the close set holds each candidate with U >= best - TOLERANCE and the first member is chosen. If any U is not
    finite, FALLBACK is chosen with a warning naming the candidates concerned."""
    unknown = [k for k in utilities if k not in order]
    if unknown:
        raise ValueError(f'candidates not in the preference order: {unknown}')
    ranked = [k for k in order if k in utilities]
    bad = [k for k in ranked if not np.isfinite(utilities[k])]
    if bad:
        warning = 'non-finite utility for ' + ', '.join(bad) + '; fallback to ' + FALLBACK
        return {'best': None, 'close': [], 'chosen': FALLBACK, 'fallback': True, 'warning': warning}
    best = max(utilities[k] for k in ranked)
    close = [k for k in ranked if utilities[k] >= best - TOLERANCE]
    return {'best': best, 'close': close, 'chosen': close[0], 'fallback': False, 'warning': None}


def stability(excess, replicates=1000, length=63, seed=20261007, order=CANDIDATES):
    """Selection frequencies under joint circular block resampling of the candidates' excess returns (5.4).

    One index matrix serves every candidate; each replicate recomputes every U and applies `choose`, so a
    non-finite U falls back as in the actual selection and is counted in `fallback_replicates`."""
    names = [k for k in order if k in excess]
    unknown = [k for k in excess if k not in order]
    if unknown:
        raise ValueError(f'candidates not in the preference order: {unknown}')
    series = {k: np.asarray(excess[k], dtype=float) for k in names}
    lengths = {len(v) for v in series.values()}
    if len(lengths) != 1:
        raise ValueError('excess series differ in length')
    n = lengths.pop()
    idx = inference.block_indices(n, length, replicates, seed)
    with np.errstate(invalid='ignore'):
        u = {k: inference.utility(v[idx]) for k, v in series.items()}
    counts = dict.fromkeys(names, 0)
    fallback = 0
    for r in range(replicates):
        result = choose({k: float(u[k][r]) for k in names}, order)
        counts[result['chosen']] += 1
        fallback += result['fallback']
    return {'frequency': {k: counts[k] / replicates for k in names}, 'fallback_replicates': fallback}


class Policy:
    """The P_A1 provider (N5 spec 5.2, 5.5; D025 items 4-7 and 15).

    `simulate(market, provider, start, end)` runs one validation account of `provider` on `market` from the session
    `start` to the session `end` in the main scenario and returns the engine Result (the registry injects an adapter
    around engine.simulate with RunConfig(start, end)); `providers` maps each candidate to its provider function.
    The history must hold every XNYS session from the first session of the fifth calendar year before the selection
    year through s_Y, and each validation account the 24 month-end decisions of its segment (D025 item 7). A decision
    at t uses the selection of selection_year(t), computed once per instance on the history truncated to the selection
    date s_Y; the weights are those of the chosen candidate at t on the history up to t, and its signal rows carry
    `selection_year` and `selected_config`."""

    def __init__(self, simulate, providers, candidates=CANDIDATES):
        candidates = tuple(candidates)
        if not candidates or len(set(candidates)) != len(candidates):
            raise ValueError(f'candidates must be non-empty and distinct: {list(candidates)}')
        if FALLBACK not in candidates:
            raise ValueError(f'the fallback {FALLBACK} must be a candidate')
        missing = [c for c in candidates if c not in providers]
        if missing:
            raise ValueError(f'no provider for candidates {missing}')
        self.candidates = candidates
        self._simulate = simulate
        self._providers = {c: providers[c] for c in candidates}
        self._selections = {}  # (year, manifest_sha256, s_Y) -> selection log entry; one instance per simulation

    def __call__(self, t, history):
        year = selection_year(t)
        chosen = self._select(year, history)['chosen']
        decision = self._providers[chosen](t, history)
        weights, signals = (decision.weights, decision.signals) if hasattr(decision, 'signals') else (decision, [])
        return Decision(weights, [{**row, 'selection_year': year, 'selected_config': chosen} for row in signals])

    def selection_log(self):
        """Copies of the computed selection entries, sorted by year."""
        return [copy.deepcopy(e) for e in sorted(self._selections.values(), key=lambda e: e['year'])]

    def _select(self, year, history):
        first, last = validation_segment(year)
        key = (year, history.manifest_sha256, last)
        if key in self._selections:
            return self._selections[key]
        required = calendar(f'{year - HISTORY_YEARS}-01-01', f'{year - HISTORY_YEARS}-01-31').sessions[0]
        if history.sessions[0] > required.date().isoformat() or last not in history.sessions:
            raise ValueError(f'selection year {year} needs the history from the first session of '
                             f'{year - HISTORY_YEARS} through the selection date {last}')
        truncated = history.history(last)  # nothing after the selection date reaches the selection
        start = required.date().isoformat()
        expected = [d.date().isoformat() for d in calendar(start, last).sessions]
        if [s for s in truncated.sessions if s >= start] != expected:
            raise ValueError(f'selection year {year} needs every XNYS session from the first session of '
                             f'{year - HISTORY_YEARS} through the selection date (D025 item 7)')
        month_ends = [xnys_month_end(f'{y}-{mo:02d}') for y in range(year - 3, year)
                      for mo in range(1, 13) if (y, mo) >= (year - 3, 12) and (y, mo) <= (year - 1, 11)]
        excess, sessions, decisions = {}, None, None
        for name in self.candidates:
            result = self._simulate(truncated, self._providers[name], first, last)
            if not result.invariants['passed']:
                raise ValueError(f'a run invariant failed in the validation account of {name} '
                                 f'for selection year {year}')
            if [d.get('decision_session') for d in result.decisions] != month_ends:
                raise ValueError(f'the validation account of {name} for selection year {year} does not hold the '
                                 f'{len(month_ends)} month-end decisions of its segment')
            series = excess_series(truncated, result)
            ordered = sorted(series)
            if sessions is None:
                sessions, decisions = ordered, len(result.decisions)
            elif ordered != sessions or len(result.decisions) != decisions:
                raise ValueError(f'validation accounts differ in their sessions or decisions for selection year '
                                 f'{year}: {name}')
            excess[name] = np.array([series[s] for s in ordered], dtype=float)
        with np.errstate(invalid='ignore', divide='ignore'):
            utilities = {name: float(inference.utility(excess[name])) for name in self.candidates}
        choice = choose(utilities, order=self.candidates)
        entry = {'year': year, 'selection_date': last, 'segment_start': first, 'segment_end': last,
                 'decisions': decisions, 'returns': len(sessions),
                 'utility': {k: u if math.isfinite(u) else None for k, u in utilities.items()},
                 'best_utility': None if choice['best'] is None else float(choice['best']),
                 'close_set': list(choice['close']), 'chosen': choice['chosen'], 'fallback': bool(choice['fallback']),
                 'warning': choice['warning'], 'stability': stability(excess, order=self.candidates)}
        self._selections[key] = entry
        return entry
