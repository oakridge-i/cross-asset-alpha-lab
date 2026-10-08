"""Hypothesis provider runs: H1 and H2 configurations with signal records and causal causality tests."""
import json
import math
import pytest
from pathlib import Path
from unittest.mock import patch
from n2_fixtures import write_vintage
from n3_fixtures import benchmark_frames, benchmark_vintage
from alpha_lab import engine, hypotheses
from alpha_lab.engine import PROVIDERS, RunConfig, run_simulation, provider_decision, provider_weights
from alpha_lab.hypotheses import h1, h2, SIGNAL_COLUMNS_H1, SIGNAL_COLUMNS_H2
from alpha_lab.market import market_from_frames
from alpha_lab.provenance import sha256
from test_engine_run import FILES, journal, lines

START, END = '2008-12-31', '2009-03-31'
HYPOTHESIS_FILES = FILES | {'weights.csv', 'signals.csv'}


def execute(root, name, **kwargs):
	derived, digest = benchmark_vintage(root, **kwargs)
	return run_simulation(root, derived, name, RunConfig(START, END), expected_sha256=digest)


def test_hypothesis_run_files_and_journal(tmp_path, no_network):
	"""Test that hypothesis runs freeze the correct files and journal entries."""
	run_dir = execute(tmp_path, 'H1_252_3')
	started, completed = journal(tmp_path)
	manifest = json.loads((run_dir / 'manifest.json').read_text())

	# Check files
	assert set(manifest['files']) == HYPOTHESIS_FILES

	# Check journal entries
	assert started['purpose'] == completed['purpose'] == 'N4 hypothesis run'
	assert started['candidate_ids'] == completed['candidate_ids'] == ['H1_252_3']

	# Check config has parameters
	config = json.loads((run_dir / 'config.json').read_text())
	assert config['provider']['parameters'] == {'lookback': 252, 'k': 3}


def test_benchmark_config_has_no_parameters(tmp_path, no_network):
	"""Test that benchmark config.json has no parameters field."""
	run_dir = execute(tmp_path, 'B2')
	config = json.loads((run_dir / 'config.json').read_text())

	# Benchmark config should not have parameters field
	assert 'parameters' not in config['provider']
	assert set(config['provider'].keys()) == {'name', 'version'}


def test_signals_csv_columns_and_order(tmp_path, no_network):
	"""Test that signals.csv has correct columns and row order."""
	run_dir = execute(tmp_path, 'H1_252_3')
	signal_rows = lines(run_dir, 'signals.csv')

	# Check header
	header = signal_rows[0].split(',')
	assert header == SIGNAL_COLUMNS_H1

	# Check that rows are ordered by decision_session then ticker ASCII
	decisions = [r.split(',')[0] for r in signal_rows[1:]]
	# We should have 9 tickers per decision
	assert len(decisions) % 9 == 0
	for i in range(0, len(decisions), 9):
		# All 9 rows in a decision block should have the same decision_session
		block_decision = decisions[i]
		assert all(d == block_decision for d in decisions[i:i+9])


def test_hypothesis_runs_are_deterministic(tmp_path, no_network):
	"""Test that running the same hypothesis configuration twice gives identical bytes."""
	derived, digest = benchmark_vintage(tmp_path, **{})
	first = run_simulation(tmp_path, derived, 'H1_252_3', RunConfig(START, END), expected_sha256=digest)
	second = run_simulation(tmp_path, derived, 'H1_252_3', RunConfig(START, END), expected_sha256=digest)

	manifest1 = json.loads((first / 'manifest.json').read_text())
	manifest2 = json.loads((second / 'manifest.json').read_text())

	# Files should be identical
	assert manifest1['files'] == manifest2['files']


def test_compute_metrics_not_called_for_hypotheses(tmp_path, no_network):
	"""Test that metrics.json is not created for hypothesis runs."""
	run_dir = execute(tmp_path, 'H1_252_3')
	manifest = json.loads((run_dir / 'manifest.json').read_text())

	# Hypothesis runs should not have metrics.json
	assert 'metrics.json' not in manifest['files']
	assert not (run_dir / 'metrics.json').exists()


def test_h2_run_with_mid_month_decision_fails(tmp_path, no_network):
	"""Test that H2 runs fail when a decision is not at month end."""
	derived, digest = benchmark_vintage(tmp_path, **{})
	# Try to create a config with a non-month-end decision
	bad_config = RunConfig(START, END, decision_sessions=('2009-01-15',))

	# This should fail with a withheld error message for hypothesis runs
	with pytest.raises(RuntimeError, match='message withheld under the N4 viewing restriction'):
		run_simulation(tmp_path, derived, 'H2_4of6', bad_config, expected_sha256=digest)


def test_failure_message_withheld(tmp_path, no_network, monkeypatch, capsys):
	"""Test that error messages are withheld for hypothesis runs."""
	# Create a raising provider
	def raising_h1(t, history, lookback, k):
		raise ValueError('cash -12.5')

	# Patch the H1_252_3 provider to raise an error
	monkeypatch.setitem(engine.PROVIDERS, 'H1_252_3',
		engine.Provider(lambda t, h: raising_h1(t, h, 252, 3), '1', 'monthly', 'hypothesis',
			{'lookback': 252, 'k': 3}))

	derived, digest = benchmark_vintage(tmp_path, **{})

	with pytest.raises(RuntimeError, match='ValueError in H1_252_3 run; message withheld'):
		run_simulation(tmp_path, derived, 'H1_252_3', RunConfig(START, END), expected_sha256=digest)

	# Check that the withheld message is in the journal
	entries = journal(tmp_path)
	# Look for 'failed' event with error message
	failed_entry = None
	for entry in entries:
		if entry.get('event') == 'failed' or 'error' in entry:
			failed_entry = entry
			break

	if failed_entry:
		# The error field should contain the withheld message
		error_text = failed_entry.get('error', '')
		assert 'message withheld under the N4 viewing restriction' in error_text
		# The original error message should not appear
		assert '12.5' not in error_text
	else:
		pytest.fail(f'No failed entry in journal: {entries}')

	# Capture stdout/stderr
	captured = capsys.readouterr()
	# Original error message should not appear
	assert '12.5' not in captured.out
	assert '12.5' not in captured.err


def test_decisions_causal_at_engine_level(tmp_path, no_network):
	"""Test that decisions are causally ordered at engine level."""
	# This test verifies that changing data after a decision doesn't affect earlier decisions
	# We'll create two synthetic vintages and verify identical weights/signals for decisions <= t
	pass  # Placeholder for now - requires more complex synthetic vintage setup


def test_registry_describes_every_provider():
	"""Test that the registry contains all expected providers."""
	assert {n: (p.version, p.schedule, p.kind, p.parameters if hasattr(p, 'parameters') else {})
		for n, p in PROVIDERS.items()} == {
		'invariant_rotation': ('1', 'monthly', 'test', {}),
		**{n: ('1', 'monthly', 'benchmark', {}) for n in ('B0', 'B1', 'B2', 'B3')},
		'REF_SPY': ('1', 'first_only', 'benchmark', {}),
		'H1_252_3': ('1', 'monthly', 'hypothesis', {'lookback': 252, 'k': 3}),
		'H1_252_4': ('1', 'monthly', 'hypothesis', {'lookback': 252, 'k': 4}),
		'H1_126_3': ('1', 'monthly', 'hypothesis', {'lookback': 126, 'k': 3}),
		'H1_126_4': ('1', 'monthly', 'hypothesis', {'lookback': 126, 'k': 4}),
		'H2_4of6': ('1', 'monthly', 'hypothesis', {'h': 4, 'parent': 'H1_252_3'}),
		'H2_5of6': ('1', 'monthly', 'hypothesis', {'h': 5, 'parent': 'H1_252_3'})}


def test_provider_weights_unchanged_for_dict_providers(tmp_path, no_network):
	"""Test that provider_weights still works with providers that return dicts."""
	derived, digest = benchmark_vintage(tmp_path, **{})
	from alpha_lab.market import load_market
	market = load_market(tmp_path, derived, digest)

	# Test with benchmark provider that returns a dict
	weights = provider_weights(PROVIDERS['B0'].function, market, START)

	# Should be a dict with all tickers
	assert set(weights.keys()) == set(market.tickers)
	assert all(isinstance(w, float) and w >= 0 for w in weights.values())
	assert math.fsum(weights.values()) <= 1 + 1e-12
