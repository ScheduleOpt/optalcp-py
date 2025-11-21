# OptalCP Python API

This package provides a Python interface to [OptalCP solver](https://optalcp.com).
The name of the package is `optalcp`.

To use this package, you need the OptalCP binary on your system.
You can use the [optalcp-bin-preview](https://github.com/ScheduleOpt/optalcp-py-bin-preview) package, which provides a preview version.
The preview version solves all problems but reports only objective values, not values of the decision variables.

Usually, there's no need to install `optalcp` directly.
It is automatically installed with [optalcp-bin-preview](https://github.com/ScheduleOpt/optalcp-py-bin-preview) or `optalcp-bin` package.

## Installation

```bash
# Install preview edition (public, no authentication required)
pip install git+https://github.com/ScheduleOpt/optalcp-py-bin-preview@latest

# This automatically installs the optalcp API package as a dependency
```

The preview edition solves all problems but reports only objective values (no solution details).

## Full and Academic Editions

For full functionality with solution details:

- **Full edition** (`optalcp-bin`): Commercial license, requires GitHub authentication
- **Academic edition** (`optalcp-bin-academic`): **Free for academic use**, requires GitHub authentication

Contact [ScheduleOpt](https://optalcp.com) for licensing options. Academic licenses are provided free of charge for qualified academic institutions.

## Documentation

The documentation for the Python API can be found on the [OptalCP web page](https://optalcp.com/docs/api).
