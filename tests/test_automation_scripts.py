"""Tests for visualization scripts.

These tests verify that visualization scripts can be imported and have basic functionality.
They do not test chart generation (requires matplotlib display).
"""
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_path))


def test_visualization_imports():
    """Test that visualization modules can be imported."""
    try:
        from visualization import equity_curves
        from visualization import comparison_plots
        from visualization import risk_charts
        assert hasattr(equity_curves, 'main')
        assert hasattr(comparison_plots, 'main')
        assert hasattr(risk_charts, 'main')
    except ImportError as e:
        # matplotlib not installed is acceptable in CI
        if 'matplotlib' in str(e) or 'pandas' in str(e):
            import pytest
            pytest.skip(f"Visualization dependencies not installed: {e}")
        else:
            raise


def test_n6_runner_import():
    """Test that n6_runner can be imported."""
    import n6_runner
    assert hasattr(n6_runner, 'N6Runner')
    assert hasattr(n6_runner, 'main')


def test_n6_runner_scenario_definitions():
    """Test that N6 scenarios are properly defined."""
    import n6_runner
    
    assert hasattr(n6_runner, 'COST_SCENARIOS')
    assert hasattr(n6_runner, 'LAG_SCENARIOS')
    assert hasattr(n6_runner, 'HYPOTHESIS_PROVIDERS')
    
    # Verify protocol compliance
    assert 0.0 in n6_runner.COST_SCENARIOS  # 0 bps
    assert 0.001 in n6_runner.COST_SCENARIOS  # 10 bps
    assert 0.002 in n6_runner.COST_SCENARIOS  # 20 bps
    assert 0.005 in n6_runner.COST_SCENARIOS  # 50 bps
    
    assert 1 in n6_runner.LAG_SCENARIOS
    assert 2 in n6_runner.LAG_SCENARIOS
    
    # Verify hypothesis providers
    expected_providers = ['H1_252_3', 'H1_252_4', 'H1_126_3', 'H1_126_4', 'H2_4of6', 'H2_5of6']
    assert set(n6_runner.HYPOTHESIS_PROVIDERS) == set(expected_providers)


def test_n6_runner_dry_run():
    """Test N6Runner dry-run mode."""
    import n6_runner
    from pathlib import Path
    
    runner = n6_runner.N6Runner(
        root=Path('.'),
        vintage=Path('data/derived/20261006T172442-80ef993493'),
        dry_run=True
    )
    
    result = runner.run_simulation(
        provider='H1_252_3',
        start='2008-12-31',
        end='2022-12-30',
        cost=0.001,
        lag=1
    )
    
    assert result['status'] == 'dry_run'
    assert result['provider'] == 'H1_252_3'
    assert result['cost'] == 0.001
    assert result['lag'] == 1
    assert 'scenario_id' in result
