# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import inspect
from typing import get_overloads, get_type_hints

# Add the optalcp package to the path
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'OptalCP'
copyright = '2025, Coenzyme'
author = 'Coenzyme'
release = '2025.11.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'myst_parser',  # Markdown support for .md files
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Nitpicky mode -----------------------------------------------------------
# Warn about all broken references
nitpicky = True

# Ignore references to internal classes that appear in type annotations
nitpick_ignore = [
    ('py:class', 'optalcp._expressions._Directive'),
    ('py:class', 'typing_extensions.TypedDict'),  # Base class for Parameters/WorkerParameters
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_show_sourcelink = False

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': False,
    'exclude-members': '__weakref__',
}

# Show typehints in signature, not as separate :param: descriptions
# This prevents __init__ params from appearing at class level
autodoc_typehints = 'signature'

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Custom docstring processing ---------------------------------------------

def convert_markdown_headings(app, what, name, obj, options, lines):
    """Convert markdown ## headings to RST format in docstrings."""
    i = 0
    while i < len(lines):
        line = lines[i]
        # Convert ### to RST underlined heading (smaller)
        if line.startswith('### '):
            heading = line[4:]
            lines[i] = heading
            lines.insert(i + 1, '~' * len(heading))
            i += 2
        # Convert ## to RST underlined heading
        elif line.startswith('## '):
            heading = line[3:]
            lines[i] = heading
            lines.insert(i + 1, '^' * len(heading))
            i += 2
        else:
            i += 1

def format_type_annotation(annotation) -> str:
    """Format a type annotation for display."""
    if annotation is inspect.Parameter.empty:
        return ''
    if hasattr(annotation, '__origin__'):
        # Handle generic types like tuple[int, int]
        origin = getattr(annotation, '__origin__', None)
        args = getattr(annotation, '__args__', ())
        if origin is tuple:
            args_str = ', '.join(format_type_annotation(a) for a in args)
            return f'tuple[{args_str}]'
        elif origin is type(None):
            return 'None'
    if hasattr(annotation, '__name__'):
        return annotation.__name__
    return str(annotation).replace('typing.', '').replace('optalcp._int_bool_var.', '').replace('optalcp._scheduling.', '')

def inject_overload_docstrings(app, what, name, obj, options, lines):
    """
    For overloaded functions, format each overload with its signature and docstring.
    """
    if what not in ('method', 'function'):
        return

    # Get the actual function
    func = obj.__func__ if hasattr(obj, '__func__') else obj

    # Get overloads for this function
    overloads = get_overloads(func)
    if not overloads:
        return

    # Clear existing lines and build new content
    lines.clear()

    for i, overload in enumerate(overloads):
        sig = inspect.signature(overload)

        # Build signature string
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            type_str = format_type_annotation(param.annotation)
            if type_str:
                params.append(f'{param_name}: {type_str}')
            else:
                params.append(param_name)

        sig_str = f"({', '.join(params)})"
        ret_str = format_type_annotation(sig.return_annotation)
        if ret_str:
            sig_str += f' -> {ret_str}'

        # Add overload header
        if i > 0:
            lines.append('')
        lines.append(f'**Overload {i+1}:** ``{sig_str}``')
        lines.append('')

        # Add docstring
        doc = inspect.getdoc(overload)
        if doc:
            lines.extend(doc.split('\n'))

def generate_overload_signatures(app, what, name, obj, options, signature, return_annotation):
    """
    For overloaded functions, use first overload's signature.
    """
    if what not in ('method', 'function'):
        return None

    func = obj.__func__ if hasattr(obj, '__func__') else obj
    overloads = get_overloads(func)
    if overloads:
        # Use first overload's signature
        first_overload = overloads[0]
        sig = inspect.signature(first_overload)
        return (str(sig), str(sig.return_annotation) if sig.return_annotation != inspect.Parameter.empty else None)
    return None

def skip_undocumented_init(app, what, name, obj, skip, options):
    """Skip __init__ methods that don't have real docstrings."""
    if name == '__init__':
        # Get the actual function if it's a bound method
        func = obj.__func__ if hasattr(obj, '__func__') else obj
        doc = getattr(func, '__doc__', None)
        # Skip if no docstring or just the default Python __init__ docstring
        if not doc or doc.startswith('Initialize self.'):
            return True
    return skip

def hide_undocumented_class_signature(app, what, name, obj, options, signature, return_annotation):
    """Hide class signature if __init__ has no docstring (internal constructor)."""
    if what == 'class':
        # Check if __init__ has a docstring
        init_method = getattr(obj, '__init__', None)
        if init_method:
            doc = getattr(init_method, '__doc__', None)
            if not doc or doc.startswith('Initialize self.'):
                # Return empty signature to hide internal constructor params
                return ('', None)
    return None

def setup(app):
    # First inject overload docstrings, then convert markdown
    app.connect('autodoc-process-docstring', inject_overload_docstrings)
    app.connect('autodoc-process-docstring', convert_markdown_headings)
    app.connect('autodoc-process-signature', generate_overload_signatures)
    app.connect('autodoc-process-signature', hide_undocumented_class_signature)
    app.connect('autodoc-skip-member', skip_undocumented_init)
