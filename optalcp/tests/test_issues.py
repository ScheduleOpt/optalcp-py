"""
Non-regression tests for specific issues.

This file contains tests for bugs that were discovered and fixed,
to prevent them from reoccurring.
"""

import optalcp as cp


def test_buffer_overflow_recovery():
    """
    Test that solver handles large JSON messages even with small buffer size.

    Regression test for LimitOverrunError on Windows when solver sends
    large JSON messages (e.g., solutions with many variables).

    This test:
    1. Creates a model with many variables to generate large JSON output
    2. Sets pythonStreamBufferSize to a very small value (1024 bytes)
    3. Verifies that the solver can still handle the large messages via recovery

    Before the fix (Option B recovery implementation), this would fail with:
        asyncio.exceptions.LimitOverrunError: Separator is not found, and chunk exceed the limit

    After the fix, the solver should recover from buffer overruns and continue.
    """
    # Create a model with many variables to generate large JSON
    model = cp.Model(name="buffer_test")

    # Create 200 interval variables - this will generate a large JSON message
    # when the solver sends back solution data
    tasks = []
    for i in range(200):
        task = model.interval_var(
            start=(0, 10000),
            end=(0, 10000),
            length=10,
            name=f"task_{i:03d}"
        )
        tasks.append(task)

    # Add some constraints to make it a valid problem
    for i in range(len(tasks) - 1):
        tasks[i].end_before_start(tasks[i + 1])

    # Minimize the end time of the last task
    model.minimize(tasks[-1].end())

    # Create parameters with a VERY small buffer size to force overflow
    params = cp.Parameters()
    params.pythonStreamBufferSize = 1024  # Only 1 KB - will definitely overflow
    params.timeLimit = 5  # Quick solve
    params.solutionLimit = 1  # Just need one solution

    # This should succeed even with tiny buffer, thanks to recovery logic
    result = cp.solve(model, params=params)

    # Verify we got a solution
    assert result.nb_solutions >= 1, "Should find at least one solution"
    assert len(result.solutions) > 0, "Should have solution data"

    # Verify solution makes sense (sequential tasks starting at 0)
    solution = result.solutions[0]
    assert solution.get_start(tasks[0]) == 0
    assert solution.get_start(tasks[1]) == 10
    assert solution.get_end(tasks[-1]) == 2000  # 200 tasks * 10 duration

    print(f"✓ Buffer overflow recovery test passed with {result.nb_solutions} solution(s)")