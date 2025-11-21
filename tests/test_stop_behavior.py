"""Test Solver.stop() behavior with graceful stop and force kill."""

import optalcp as cp
import asyncio
import pytest


@pytest.mark.asyncio
async def test_stop_graceful():
    """Test that first call to stop() sends graceful stop message."""
    model = cp.Model()

    # Create a simple model
    x = model.int_var(min=0, max=100, name='x')
    model.minimize(x)

    solver = cp.Solver()
    solver.output_stream = None  # Suppress output

    # Start solve in background
    solve_task = asyncio.create_task(
        solver.solve(model, params=cp.Parameters(timeLimit=10000))
    )

    # Let it run briefly
    await asyncio.sleep(0.1)

    # Call stop once - should send graceful stop
    solver.stop("Test graceful stop")

    # Wait for solve to complete
    result = await solve_task

    # Should have completed (may or may not have found solution)
    assert result is not None


@pytest.mark.asyncio
async def test_stop_force_kill():
    """Test that second call to stop() kills the process."""
    model = cp.Model()

    # Create a simple model
    x = model.int_var(min=0, max=100, name='x')
    model.minimize(x)

    solver = cp.Solver()
    solver.output_stream = None

    # Start solve in background
    solve_task = asyncio.create_task(
        solver.solve(model, params=cp.Parameters(timeLimit=10000))
    )

    # Let it run briefly
    await asyncio.sleep(0.1)

    # First call - graceful stop
    solver.stop("First stop")

    # Second call immediately - should kill
    solver.stop("Force kill")

    # Wait for solve to complete (may raise due to killed process)
    try:
        result = await solve_task
        # If it completes normally, that's fine
        assert result is not None
    except RuntimeError:
        # If it raises due to killed process, that's also expected
        pass


@pytest.mark.asyncio
async def test_stop_when_not_running():
    """Test that stop() is safe to call when solver is not running."""
    solver = cp.Solver()

    # Call stop when no solve is running - should not raise
    solver.stop("No process")

    # Call it multiple times - should be safe
    solver.stop("Still no process")


@pytest.mark.asyncio
async def test_stop_resets_between_solves():
    """Test that stop flag resets between solve() calls."""
    model = cp.Model()
    x = model.int_var(min=0, max=100, name='x')
    model.minimize(x)

    solver = cp.Solver()
    solver.output_stream = None

    # First solve
    task1 = asyncio.create_task(
        solver.solve(model, params=cp.Parameters(timeLimit=5000))
    )
    await asyncio.sleep(0.05)
    solver.stop("Stop first solve")
    await task1

    # Second solve - stop flag should be reset
    task2 = asyncio.create_task(
        solver.solve(model, params=cp.Parameters(timeLimit=5000))
    )
    await asyncio.sleep(0.05)

    # First call should send graceful stop (not kill)
    solver.stop("Stop second solve")

    result = await task2
    assert result is not None
