"""Selection rules of the adaptive policy P_A1: year mapping, validation segment, close-set choice and selection
stability (N5 spec 5.2-5.4, P4-P7). Pure functions; no simulation, files or journal."""
import numpy as np
from alpha_lab import inference
from alpha_lab.features import xnys_month_end
from alpha_lab.metrics import UTILITY_PENALTY

CANDIDATES = ('H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4')
FALLBACK = 'H1_252_3'
TOLERANCE = 0.001
PENALTY = 1.5
FIRST_YEAR = 2014
LAST_YEAR = 2022

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
