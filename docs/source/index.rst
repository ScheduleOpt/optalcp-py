Python API Reference
====================

This is the auto-generated API reference for the OptalCP Python library.

**New to OptalCP?** Start with the `Tutorial <../docs/Tutorial/intro>`_ for a hands-on introduction, or `Quick Start <../docs/Quick%20Start/>`_ for installation.

Key Classes
-----------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Class
     - Description
   * - :class:`Model`
     - Central class for building optimization models. Creates variables, constraints, and objectives.
   * - :class:`IntervalVar`
     - Interval (task) variable for scheduling. Has start, end, length, and optional presence.
   * - :class:`IntVar`
     - Integer decision variable with a domain.
   * - :class:`SequenceVar`
     - Ordered sequence of intervals for routing and sequencing problems.
   * - :class:`Solver`
     - Advanced solving with callbacks for solutions, bounds, and logs.
   * - :class:`Solution`
     - Access to variable values after solving.

Common Entry Points
-------------------

Creating a Model
^^^^^^^^^^^^^^^^

.. code-block:: python

   import optalcp as cp
   model = cp.Model()

See :class:`Model` for all factory methods: :meth:`~Model.int_var`, :meth:`~Model.interval_var`, :meth:`~Model.sequence_var`.

Solving
^^^^^^^

- **Simple:** :meth:`Model.solve` - returns :class:`SolveResult`
- **Advanced:** :class:`Solver` class with :meth:`~Solver.on_solution`, :meth:`~Solver.on_log` callbacks

Constraints
^^^^^^^^^^^

Most constraints are methods on :class:`Model`:

- Scheduling: :meth:`~Model.no_overlap`, :meth:`~Model.alternative`, :meth:`~Model.span`
- Precedence: :meth:`~Model.end_before_start`, :meth:`~Model.start_at_end`, etc.
- Resources: :meth:`~Model.pulse`, :meth:`~Model.step_at_start`, :meth:`~Model.cumul_le`
- Forbid: :meth:`~Model.forbid_start`, :meth:`~Model.forbid_end`, :meth:`~Model.forbid_extent`

Expressions
^^^^^^^^^^^

Expressions use operators. See :class:`IntExpr` for arithmetic (``+``, ``*``, ``<=``) and :class:`BoolExpr` for boolean logic (``&``, ``|``, ``~``).

Interval expressions: :meth:`~IntervalVar.start`, :meth:`~IntervalVar.end`, :meth:`~IntervalVar.length`, :meth:`~IntervalVar.presence`.

Parameters
^^^^^^^^^^

:class:`Parameters` controls solver behavior: ``timeLimit``, ``nbWorkers``, ``searchType``, ``logLevel``, etc.

Parse from command line: :func:`parse_parameters`, :func:`parse_known_parameters`.

Solution Access
^^^^^^^^^^^^^^^

:class:`Solution` methods: :meth:`~Solution.get_start`, :meth:`~Solution.get_end`, :meth:`~Solution.get_value`, :meth:`~Solution.is_absent`.

Model Export
^^^^^^^^^^^^

- :meth:`Model.export_model` / :meth:`Model.import_model` - JSON serialization
- :meth:`Model.print_model` - Human-readable format

Benchmarking
^^^^^^^^^^^^

:func:`benchmark` function with :class:`BenchmarkParameters`.

Learn More
----------

- `Tutorial <../docs/Tutorial/intro>`_ - Step-by-step guide building a complete scheduling model
- `Modeling Reference <../docs/Modeling/intervals>`_ - Detailed concept explanations
- `Solving Guide <../docs/Solving/basics>`_ - Understanding solve results and parameters
- `Examples <https://github.com/ScheduleOpt/optalcp-benchmarks>`_ - Complete benchmark implementations

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
