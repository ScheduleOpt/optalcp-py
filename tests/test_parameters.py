"""
Test WorkerParameters and Parameters classes
"""

import asyncio
import optalcp as cp
import io
import ast
from pathlib import Path
from dataclasses import fields

def test_worker_parameters():
    """Test WorkerParameters class."""
    # Test constructor:
    wp = cp.WorkerParameters(cumulPropagationLevel=3, searchType='FDS')
    assert wp.cumulPropagationLevel == 3
    assert wp.searchType == 'FDS'
    # Test setting/getting attributes:
    wp.noOverlapPropagationLevel = 4
    assert wp.noOverlapPropagationLevel == 4

def test_parameters1():
    """Test Parameters class with global parameters only."""
    params = cp.Parameters(timeLimit=120, nbWorkers=2)
    assert params.timeLimit == 120
    assert params.nbWorkers == 2
    assert len(params.workers) == 0  # No per-worker overrides

def test_parameters2():
    """Test Parameters class with per-worker overrides."""
    params = cp.Parameters(timeLimit=60, searchType='LNS', nbWorkers=3)
    params.workers = [
        cp.WorkerParameters(searchType='LNS'),
        cp.WorkerParameters(searchType='LNS'),
        cp.WorkerParameters(searchType="FDS")
    ]
    assert params.timeLimit == 60
    assert params.searchType == 'LNS'
    assert params.nbWorkers == 3
    assert len(params.workers) == 3
    assert params.workers[0].searchType == 'LNS'
    assert params.workers[1].searchType == 'LNS'
    assert params.workers[2].searchType == 'FDS'

def test_parameters_solve():
    """Test solving a model with Parameters."""
    model = cp.Model(name="test_parameters")
    x = model.interval_var(length=10, name="x")
    model.minimize(x.start())

    # Redirect log into a string buffer so we can verify that parameters were set:
    buffer = io.StringIO()

    params = cp.Parameters(solutionLimit=1, nbWorkers=2)
    params.workers.append(cp.WorkerParameters(searchType='LNS'))
    params.workers.append(cp.WorkerParameters(searchType='FDS', _lnsPortionMultiplier=1.5))
    solver = cp.Solver()
    solver.output_stream = buffer
    result = asyncio.run(solver.solve(model, params))

    assert result.nb_solutions > 0, "Should find at least one solution"
    assert "SolutionLimit = 1" in buffer.getvalue(), "Log should show TimeLimit parameter set"
    assert "NbWorkers = 2" in buffer.getvalue(), "Log should show NbWorkers parameter set"
    assert "Worker 0: SearchType = LNS" in buffer.getvalue(), "Log should show Worker 0 SearchType"
    assert "Worker 1: SearchType = FDS" in buffer.getvalue(), "Log should show Worker 1 SearchType"
    assert "Worker 1: LNSPortionMultiplier = 1.5" in buffer.getvalue(), "Log should show Worker 1 LNSPortionMultiplier"

def test_py_file_structure():
    """Test that the .py file has the correct structure."""
    py_path = Path(cp.__file__).parent / "_parameters.py"

    with open(py_path, 'r') as f:
        content = f.read()

    # Parse the .py file
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        assert False, f"Failed to parse .py file: {e}"

    # Find class definitions
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    class_names = [cls.name for cls in classes]

    assert "WorkerParameters" in class_names, "WorkerParameters class should be in .py file"
    assert "Parameters" in class_names, "Parameters class should be in .py file"

def test_py_worker_parameters_fields():
    """Test that WorkerParameters has all expected fields."""
    # Get field names from actual WorkerParameters class
    py_fields = {f.name for f in fields(cp.WorkerParameters) if not f.name.startswith('_')}

    # Check that we have a reasonable number of fields
    assert len(py_fields) > 10, f"WorkerParameters should have many fields, found {len(py_fields)}"

def test_py_parameters_fields():
    """Test that Parameters has all expected fields."""
    # Get field names from actual Parameters class
    py_fields = {f.name for f in fields(cp.Parameters) if not f.name.startswith('_')}

    # Check that we have a reasonable number of fields
    assert len(py_fields) > 20, f"Parameters should have many fields, found {len(py_fields)}"

    # Check that some key fields exist
    assert 'timeLimit' in py_fields, "Parameters should have timeLimit field"
    assert 'nbWorkers' in py_fields, "Parameters should have nbWorkers field"
    assert 'searchType' in py_fields, "Parameters should have searchType field"

def test_py_field_has_docstrings():
    """Test that fields in .py file have docstrings."""
    py_path = Path(cp.__file__).parent / "_parameters.py"

    with open(py_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    # Find WorkerParameters class
    worker_params_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "WorkerParameters":
            worker_params_class = node
            break

    assert worker_params_class is not None, "WorkerParameters class not found in .py"

    # Count fields with docstrings
    fields_with_docs = 0
    total_fields = 0

    for i, item in enumerate(worker_params_class.body):
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            field_name = item.target.id
            # Skip private fields
            if field_name.startswith('_'):
                continue
            total_fields += 1
            # Check if next item is a docstring (Expr with Constant/Str value)
            if i + 1 < len(worker_params_class.body):
                next_item = worker_params_class.body[i + 1]
                if isinstance(next_item, ast.Expr):
                    if isinstance(next_item.value, ast.Constant) and isinstance(next_item.value.value, str):
                        fields_with_docs += 1

    # At least some fields should have docstrings
    assert fields_with_docs > 0, "No fields have docstrings in .py"
    # Most fields should have docstrings (at least 90%)
    ratio = fields_with_docs / total_fields if total_fields > 0 else 0
    assert ratio > 0.9, f"Only {fields_with_docs}/{total_fields} fields have docstrings (expected >90%)"

def test_py_type_annotations():
    """Test that fields in .py file have proper type annotations."""
    py_path = Path(cp.__file__).parent / "_parameters.py"

    with open(py_path, 'r') as f:
        content = f.read()

    tree = ast.parse(content)

    # Find WorkerParameters class
    worker_params_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "WorkerParameters":
            worker_params_class = node
            break

    # Check a few specific fields have correct types
    field_types = {}
    for item in worker_params_class.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            field_name = item.target.id
            # Get the annotation as a string representation
            # Modern Python 3.10+ uses BinOp with BitOr for X | None
            if isinstance(item.annotation, ast.BinOp):
                if isinstance(item.annotation.op, ast.BitOr):
                    # Check if right side is None
                    if isinstance(item.annotation.right, ast.Constant) and item.annotation.right.value is None:
                        field_types[field_name] = "Optional"
            # Also handle old-style Optional[X] for compatibility
            elif isinstance(item.annotation, ast.Subscript):
                if isinstance(item.annotation.value, ast.Name) and item.annotation.value.id == "Optional":
                    field_types[field_name] = "Optional"

    # Some known fields should be Optional (using | None syntax)
    assert field_types.get("searchType") == "Optional", "searchType should be X | None"
    assert field_types.get("randomSeed") == "Optional", "randomSeed should be int | None"
    assert field_types.get("noOverlapPropagationLevel") == "Optional", "noOverlapPropagationLevel should be int | None"