"""
Tests for Jupyter notebook compatibility (nested event loops).

This test verifies that cp.solve() works correctly both in regular Python
and in async contexts (like Jupyter notebooks) where an event loop is already running.
"""

import asyncio
import pytest
import optalcp as cp


def test_solve_without_event_loop():
    """Test that solve() works in regular Python without an event loop."""
    model = cp.Model(name="test_no_loop")
    x = model.interval_var(length=10, name="x")
    model.minimize(x.start())

    result = cp.solve(model)

    assert result.nb_solutions > 0
    assert result.objective_value == 0.0


def test_solve_with_running_event_loop():
    """Test that solve() works when called from within an async function (simulates Jupyter)."""

    async def solve_in_async_context():
        # This simulates Jupyter notebook environment where event loop is already running
        model = cp.Model(name="test_with_loop")
        x = model.interval_var(length=10, name="x")
        model.minimize(x.start())

        # This should work thanks to nest_asyncio
        result = cp.solve(model)

        assert result.nb_solutions > 0
        assert result.objective_value == 0.0
        return result

    # Run the async function
    result = asyncio.run(solve_in_async_context())
    assert result is not None


def test_solve_with_nested_event_loops():
    """Test that solve() works with deeply nested event loops."""

    async def level2():
        model = cp.Model(name="test_nested")
        x = model.interval_var(length=10, name="x")
        y = model.interval_var(length=20, name="y")
        x.end_before_start(y)
        model.minimize(y.end())

        # Should work even in nested async context
        result = cp.solve(model)

        assert result.nb_solutions > 0
        assert result.objective_value == 30.0
        return result

    async def level1():
        return await level2()

    result = asyncio.run(level1())
    assert result is not None


def test_solve_and_async_solver_both_work():
    """Test that both synchronous solve() and async Solver work in async context."""

    async def test_both_interfaces():
        model = cp.Model(name="test_both")
        x = model.interval_var(length=10, name="x")
        model.minimize(x.start())

        # Test synchronous solve()
        result1 = cp.solve(model)
        assert result1.nb_solutions > 0
        assert result1.objective_value == 0.0

        # Test async Solver
        solver = cp.Solver()
        solver.output_stream = None
        result2 = await solver.solve(model)
        assert result2.nb_solutions > 0
        assert result2.objective_value == 0.0

        return result1, result2

    result1, result2 = asyncio.run(test_both_interfaces())
    assert result1 is not None
    assert result2 is not None


def test_has_running_loop_helper():
    """Test the _has_running_loop() helper function directly."""
    from optalcp._solver import _has_running_loop

    # Outside async context - should be False
    assert not _has_running_loop()

    # Inside async context - should be True
    async def check_in_async():
        return _has_running_loop()

    result = asyncio.run(check_in_async())
    assert result is True


def test_multiple_consecutive_solves_in_async():
    """Test that multiple consecutive solve() calls work in async context."""

    async def solve_multiple():
        results = []

        for i in range(3):
            model = cp.Model(name=f"test_multiple_{i}")
            x = model.interval_var(length=10, name="x")
            model.minimize(x.start())

            result = cp.solve(model)
            assert result.nb_solutions > 0
            results.append(result)

        return results

    results = asyncio.run(solve_multiple())
    assert len(results) == 3
    assert all(r.objective_value == 0.0 for r in results)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
