"""
Integer and boolean variable classes for OptalCP Python API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._constants import IntVarMax, _PresenceStatus
from ._expressions import BoolExpr, IntExpr, _ElementProps

if TYPE_CHECKING:
    from ._model import Model


class IntVar(IntExpr):
    r"""
    Integer variable represents an unknown (integer) value that solver has to find.

    The value of the integer variable can be constrained using arithmetic operators (`+`, `-`, `*`, `//`) and comparison operators (`<`, `<=`, `==`, `!=`, `>`, `>=`).

    OptalCP solver focuses on scheduling problems and concentrates on :class:`IntervalVar` variables.
    Therefore, interval variables should be the primary choice for modeling in OptalCP.
    However, integer variables can be used for other purposes, such as counting or indexing.
    In particular, integer variables can be helpful for cumulative expressions with variable heights; see :meth:`Model.pulse`, :meth:`Model.step_at_start`, :meth:`Model.step_at_end`, and :meth:`Model.step_at`.

    The integer variable can be optional.
    In this case, the solver can make the variable absent, which is usually interpreted as the fact that the solver does not use the variable at all.
    Functions :meth:`Model.presence` and :meth:`IntExpr.presence` can constrain the presence of the variable.

    Integer variables can be created using the function :meth:`Model.int_var`.

    ## Example

    In the following example we create three integer variables `x`, `y` and `z`.
    Variables `x` and `y` are present, but variable `z` is optional.
    Each variable has a different range of possible values.

    .. code-block:: python

        import optalcp as cp

        model = cp.Model()
        x = model.int_var(name="x", min=1, max=3)
        y = model.int_var(name="y", min=0, max=100)
        z = model.int_var(name="z", min=10, max=20, optional=True)
    """

    def __init__(self, model: Model, props: _ElementProps, ref_id: int | None = None):
        # Don't call super().__init__ - we're creating from props directly
        self._model = model
        self._props = props
        self._arg = None
        if ref_id is not None:
            # Loading from JSON - use existing ref_id
            self._arg = {'ref': ref_id}
        else:
            # Variables always get a reference ID
            self._force_ref()

    def is_optional(self) -> bool:
        r"""
        Returns `True` if the integer variable was created as *optional*.

        :rtype: bool
        :returns: True if the integer variable is optional

        ## Details

        Optional integer variable can be *absent* in the solution, i.e., it can be omitted.

        **Note:** This function checks the presence status of the variable in the model
        (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")
            y = model.int_var(min=0, max=10, optional=True, name="y")

            print(x.is_optional())  # False
            print(y.is_optional())  # True

        .. seealso::

            - :meth:`IntVar.is_present`, :meth:`IntVar.is_absent`.
            - :meth:`IntVar.make_optional`, :meth:`IntVar.make_present`, :meth:`IntVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        r"""
        Returns `True` if the integer variable was created *present* (and therefore cannot be *absent* in the solution).

        :rtype: bool
        :returns: True if the integer variable is present

        ## Details

        **Note:** This function returns the presence status of the variable in the
        model (before the solve), not in the solution. In particular, for an
        optional integer variable, this function returns `False`, even though there
        could be a solution in which the variable is *present*.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")
            y = model.int_var(min=0, max=10, optional=True, name="y")

            print(x.is_present())  # True
            print(y.is_present())  # False (optional variable)

        .. seealso::

            - :meth:`IntVar.is_optional`, :meth:`IntVar.is_absent`.
            - :meth:`IntVar.make_optional`, :meth:`IntVar.make_present`, :meth:`IntVar.make_absent`.
        """
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        r"""
        Returns `True` if the integer variable was created *absent* (and therefore cannot be *present* in the solution).

        :rtype: bool
        :returns: True if the integer variable is absent

        ## Details

        **Note:** This function checks the presence status of the variable in the model
        (before the solve), not in the solution. In particular, for an optional
        integer variable, this function returns `False`, even though there could be
        a solution in which the variable is *absent*.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")
            x.make_absent()

            print(x.is_absent())  # True

        .. seealso::

            - :meth:`IntVar.is_optional`, :meth:`IntVar.is_present`.
            - :meth:`IntVar.make_optional`, :meth:`IntVar.make_present`, :meth:`IntVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Absent

    def get_min(self) -> int | None:
        r"""
        Returns minimum value assigned to the integer variable.

        :rtype: int | None
        :returns: The minimum value, or None if absent

        ## Details

        Returns the minimum value assigned to the integer variable during its
        construction by :meth:`Model.int_var` or later by
        function :meth:`IntVar.set_min` or function :meth:`IntVar.set_range`.

        If the variable is absent, the function returns `None`.

        **Note:** This function returns the minimum value of the variable in the
        model (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=5, max=10, name="x")

            print(x.get_min())  # 5

            x.set_min(7)
            print(x.get_min())  # 7

        .. seealso::

            - :meth:`IntVar.get_max`.
            - :meth:`IntVar.set_min`, :meth:`IntVar.set_max`, :meth:`IntVar.set_range`.
        """
        if self.is_absent():
            return None
        return self._props.get('min', 0)

    def get_max(self) -> int | None:
        r"""
        Returns maximum value assigned to the integer variable.

        :rtype: int | None
        :returns: The maximum value, or None if absent

        ## Details

        Returns the maximum value assigned to the integer variable during its
        construction by :meth:`Model.int_var` or later by
        function :meth:`IntVar.set_max` or function :meth:`IntVar.set_range`.

        If the variable is absent, the function returns `None`.

        **Note:** This function returns the maximum value of the variable in the
        model (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=5, max=10, name="x")

            print(x.get_max())  # 10

            x.set_max(8)
            print(x.get_max())  # 8

        .. seealso::

            - :meth:`IntVar.get_min`.
            - :meth:`IntVar.set_min`, :meth:`IntVar.set_max`, :meth:`IntVar.set_range`.
        """
        if self.is_absent():
            return None
        return self._props.get('max', IntVarMax)

    def make_optional(self) -> None:
        r"""
        Makes the integer variable optional.

        Optional integer variable can be *absent* in the solution, i.e., can be
        omitted. It is equivalent to setting `optional=True` in :meth:`Model.int_var`.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")

            print(x.is_optional())  # False
            x.make_optional()
            print(x.is_optional())  # True

        .. seealso::

            - :meth:`IntVar.make_present`, :meth:`IntVar.make_absent`.
            - :meth:`IntVar.is_optional`, :meth:`IntVar.is_present`, :meth:`IntVar.is_absent`.
        """
        self._props['status'] = _PresenceStatus.Optional

    def make_absent(self) -> None:
        r"""
        Makes the integer variable absent.

        Absent integer variable cannot be *present* in the solution, i.e., it will
        be omitted in the solution (and everything that depends on it).

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")

            print(x.is_absent())  # False
            x.make_absent()
            print(x.is_absent())  # True

        .. seealso::

            - :meth:`IntVar.make_optional`, :meth:`IntVar.make_present`.
            - :meth:`IntVar.is_optional`, :meth:`IntVar.is_present`, :meth:`IntVar.is_absent`.
        """
        self._props['status'] = _PresenceStatus.Absent

    def make_present(self) -> None:
        r"""
        Makes the integer variable present.

        The present integer variable cannot be *absent* in the solution, i.e.,
        cannot be omitted.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, optional=True, name="x")

            print(x.is_present())  # False (optional)
            x.make_present()
            print(x.is_present())  # True

        .. seealso::

            - :meth:`IntVar.make_optional`, :meth:`IntVar.make_absent`.
            - :meth:`IntVar.is_optional`, :meth:`IntVar.is_present`, :meth:`IntVar.is_absent`.
        """
        self._props.pop('status', None)

    def set_min(self, min_val: int) -> None:
        r"""
        Sets the minimum value of the integer variable to the given value.

        :param min_val: The minimum value to set
        :type min_val: int

        ## Details

        It overwrites any previous minimum value limit given at variable creation by
        :meth:`Model.int_var` or later by
        :meth:`IntVar.set_min` or :meth:`IntVar.set_range`.
        This function does not change the maximum value.

        Note that the value of the integer variable must be in the range :const:`IntVarMin` to :const:`IntVarMax`.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")

            print(x.get_min())  # 0
            x.set_min(5)
            print(x.get_min())  # 5

        .. seealso::

            - :meth:`IntVar.set_max`, :meth:`IntVar.set_range`.
            - :meth:`IntVar.get_min`, :meth:`IntVar.get_max`.
        """
        self._props['min'] = int(min_val)

    def set_max(self, max_val: int) -> None:
        r"""
        Sets the maximum value of the integer variable to the given value.

        :param max_val: The maximum value to set
        :type max_val: int

        ## Details

        It overwrites any previous maximum value limit given at variable creation by
        :meth:`Model.int_var` or later by
        :meth:`IntVar.set_max` or :meth:`IntVar.set_range`.
        This function does not change the minimum value.

        Note that the value of the integer variable must be in the range :const:`IntVarMin` to :const:`IntVarMax`.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=10, name="x")

            print(x.get_max())  # 10
            x.set_max(5)
            print(x.get_max())  # 5

        .. seealso::

            - :meth:`IntVar.set_min`, :meth:`IntVar.set_range`.
            - :meth:`IntVar.get_min`, :meth:`IntVar.get_max`.
        """
        self._props['max'] = int(max_val)

    def set_range(self, min_val: int, max_val: int) -> None:
        r"""
        Sets the value of the integer variable to the given range.

        :param min_val: The minimum value to set
        :type min_val: int
        :param max_val: The maximum value to set
        :type max_val: int

        ## Details

        It overwrites any previous value limits given at variable creation by
        :meth:`Model.int_var` or later by
        :meth:`IntVar.set_min`, :meth:`IntVar.set_max` or :meth:`IntVar.set_range`.

        The call:
        .. code-block:: python

            int_var.set_range(min_val, max_val)

        is equivalent to:
        .. code-block:: python

            int_var.set_min(min_val)
            int_var.set_max(max_val)

        Note that the value of the integer variable must be in the range :const:`IntVarMin` to :const:`IntVarMax`.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.int_var(min=0, max=100, name="x")

            print(x.get_min(), x.get_max())  # 0 100
            x.set_range(10, 20)
            print(x.get_min(), x.get_max())  # 10 20

        .. seealso::

            - :meth:`IntVar.set_min`, :meth:`IntVar.set_max`.
            - :meth:`IntVar.get_min`, :meth:`IntVar.get_max`.
        """
        self._props['min'] = int(min_val)
        self._props['max'] = int(max_val)


class BoolVar(BoolExpr):
    r"""
    Boolean variable represents an unknown truth value (`True` or `False`) that the solver must find.

    Boolean variables are useful for modeling decisions, choices, or logical conditions in your problem. For example, you can use boolean variables to represent whether a machine is used, whether a task is assigned to a particular worker, or whether a constraint should be enforced.

    Boolean variables can be created using the function :meth:`Model.bool_var`.
    By default, boolean variables are *present* (not optional).
    To create an optional boolean variable, specify `optional=True` in the arguments of the function.

    ### Logical operators

    Boolean variables support the following logical operators:

    - `~x` for logical NOT
    - `x | y` for logical OR
    - `x & y` for logical AND

    These operators can be used to create complex boolean expressions and constraints.

    ### Boolean variables as integer expressions

    Class `BoolVar` derives from :class:`BoolExpr`, which derives from :class:`IntExpr`.
    Therefore, boolean variables can be used as integer expressions:
    *True* is equal to *1*, *False* is equal to *0*, and *absent* remains *absent*.

    This is useful for counting how many conditions are satisfied or for weighted sums.

    ### Optional boolean variables

    A boolean variable can be optional. In this case, the solver can decide to make the variable *absent*, which means the variable doesn't participate in the solution. When a boolean variable is absent, its value is neither `True` nor `False` — it is *absent*.

    Most expressions that depend on an absent variable are also *absent*. For example, if `x` is an absent boolean variable, then `~x`, `x | y`, and `x & y` are all *absent*, regardless of the value of `y`. However, some functions handle absent values specially, such as :meth:`IntExpr.presence` or :meth:`Model.sum`.

    When a boolean expression is added as a constraint using :meth:`Model.enforce`, the constraint requires that the expression is not `False` in the solution. The expression can be `True` or *absent*. This means that constraints involving optional variables are automatically satisfied when the underlying variables are absent.

    Functions :meth:`Model.presence` and :meth:`IntExpr.presence` can constrain the presence of the variable.

    ## Example

    In the following example, we create two boolean variables representing whether to use each of two machines. We require that at least one machine is used, but not both:

    .. code-block:: python

        import optalcp as cp

        model = cp.Model()
        use_machine_a = model.bool_var(name="use_machine_a")
        use_machine_b = model.bool_var(name="use_machine_b")

        # Constraint: must use at least one machine
        model.enforce(use_machine_a | use_machine_b)

        # Constraint: cannot use both machines (exclusive choice)
        model.enforce(~(use_machine_a & use_machine_b))

        result = model.solve()

    ## Example

    Boolean variables can be used in arithmetic expressions by treating `True` as 1 and `False` as 0:

    .. code-block:: python

        import optalcp as cp

        model = cp.Model()
        options = [model.bool_var(name=f"option_{i}") for i in range(5)]

        # Constraint: select exactly 2 options
        model.enforce(model.sum(options) == 2)

        result = model.solve()

    .. seealso::

        - :meth:`Model.bool_var` to create boolean variables.
        - :class:`BoolExpr` for boolean expressions and their operations.
        - :class:`IntVar` for integer decision variables.
        - :class:`IntervalVar` for the primary variable type for scheduling problems.
    """

    def __init__(self, model: Model, props: _ElementProps, ref_id: int | None = None):
        self._model = model
        self._props = props
        self._arg = None
        if ref_id is not None:
            # Loading from JSON - use existing ref_id
            self._arg = {'ref': ref_id}
        else:
            self._force_ref()

    def is_optional(self) -> bool:
        r"""
        Returns `True` if the boolean variable was created as *optional*.

        :rtype: bool
        :returns: True if the boolean variable is optional

        ## Details

        Optional boolean variable can be *absent* in the solution, i.e., it can be omitted.

        **Note:** This function checks the presence status of the variable in the model
        (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")
            y = model.bool_var(optional=True, name="y")

            print(x.is_optional())  # False
            print(y.is_optional())  # True

        .. seealso::

            - :meth:`BoolVar.is_present`, :meth:`BoolVar.is_absent`.
            - :meth:`BoolVar.make_optional`, :meth:`BoolVar.make_present`, :meth:`BoolVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Optional

    def is_present(self) -> bool:
        r"""
        Returns `True` if the boolean variable was created *present* (and therefore cannot be *absent* in the solution).

        :rtype: bool
        :returns: True if the boolean variable is present

        ## Details

        **Note:** This function returns the presence status of the variable in the
        model (before the solve), not in the solution. In particular, for an
        optional boolean variable, this function returns `False`, even though there
        could be a solution in which the variable is *present*.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")
            y = model.bool_var(optional=True, name="y")

            print(x.is_present())  # True
            print(y.is_present())  # False (optional variable)

        .. seealso::

            - :meth:`BoolVar.is_optional`, :meth:`BoolVar.is_absent`.
            - :meth:`BoolVar.make_optional`, :meth:`BoolVar.make_present`, :meth:`BoolVar.make_absent`.
        """
        status = self._props.get('status')
        return status is None or status == _PresenceStatus.Present

    def is_absent(self) -> bool:
        r"""
        Returns `True` if the boolean variable was created *absent* (and therefore cannot be *present* in the solution).

        :rtype: bool
        :returns: True if the boolean variable is absent

        ## Details

        **Note:** This function checks the presence status of the variable in the model
        (before the solve), not in the solution. In particular, for an optional
        boolean variable, this function returns `False`, even though there could be
        a solution in which the variable is *absent*.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")
            x.make_absent()

            print(x.is_absent())  # True

        .. seealso::

            - :meth:`BoolVar.is_optional`, :meth:`BoolVar.is_present`.
            - :meth:`BoolVar.make_optional`, :meth:`BoolVar.make_present`, :meth:`BoolVar.make_absent`.
        """
        return self._props.get('status') == _PresenceStatus.Absent

    def get_min(self) -> bool | None:
        r"""
        Returns minimum value assigned to the boolean variable.

        :rtype: bool | None
        :returns: The minimum value (False or True), or None if absent

        ## Details

        Returns the minimum value assigned to the boolean variable during its
        construction by :meth:`Model.bool_var` or later by
        function :meth:`BoolVar.set_min` or function :meth:`BoolVar.set_range`.

        If the variable is absent, the function returns `None`.
        For a free boolean variable (not constrained), returns `False`.
        If `set_min(True)` was called, the variable is fixed to `True`.

        **Note:** This function returns the minimum value of the variable in the
        model (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.get_min())  # False (default minimum)

            x.set_min(True)
            print(x.get_min())  # True (variable is now fixed to True)

        .. seealso::

            - :meth:`BoolVar.get_max`.
            - :meth:`BoolVar.set_min`, :meth:`BoolVar.set_max`, :meth:`BoolVar.set_range`.
        """
        if self.is_absent():
            return None
        return self._props.get('min', 0) > 0

    def get_max(self) -> bool | None:
        r"""
        Returns maximum value assigned to the boolean variable.

        :rtype: bool | None
        :returns: The maximum value (True or False), or None if absent

        ## Details

        Returns the maximum value assigned to the boolean variable during its
        construction by :meth:`Model.bool_var` or later by
        function :meth:`BoolVar.set_max` or function :meth:`BoolVar.set_range`.

        If the variable is absent, the function returns `None`.
        For a free boolean variable (not constrained), returns `True`.
        If `set_max(False)` was called, the variable is fixed to `False`.

        **Note:** This function returns the maximum value of the variable in the
        model (before the solve), not in the solution.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.get_max())  # True (default maximum)

            x.set_max(False)
            print(x.get_max())  # False (variable is now fixed to False)

        .. seealso::

            - :meth:`BoolVar.get_min`.
            - :meth:`BoolVar.set_min`, :meth:`BoolVar.set_max`, :meth:`BoolVar.set_range`.
        """
        if self.is_absent():
            return None
        return self._props.get('max', 1) > 0

    def make_optional(self) -> None:
        r"""
        Makes the boolean variable optional.

        Optional boolean variable can be *absent* in the solution, i.e., can be
        omitted. It is equivalent to setting `optional=True` in :meth:`Model.bool_var`.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.is_optional())  # False
            x.make_optional()
            print(x.is_optional())  # True

        .. seealso::

            - :meth:`BoolVar.make_present`, :meth:`BoolVar.make_absent`.
            - :meth:`BoolVar.is_optional`, :meth:`BoolVar.is_present`, :meth:`BoolVar.is_absent`.
        """
        self._props['status'] = _PresenceStatus.Optional

    def make_absent(self) -> None:
        r"""
        Makes the boolean variable absent.

        Absent boolean variable cannot be *present* in the solution, i.e., it will
        be omitted in the solution (and everything that depends on it).

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.is_absent())  # False
            x.make_absent()
            print(x.is_absent())  # True

        .. seealso::

            - :meth:`BoolVar.make_optional`, :meth:`BoolVar.make_present`.
            - :meth:`BoolVar.is_optional`, :meth:`BoolVar.is_present`, :meth:`BoolVar.is_absent`.
        """
        self._props['status'] = _PresenceStatus.Absent

    def make_present(self) -> None:
        r"""
        Makes the boolean variable present.

        The present boolean variable cannot be *absent* in the solution, i.e.,
        cannot be omitted.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(optional=True, name="x")

            print(x.is_present())  # False (optional)
            x.make_present()
            print(x.is_present())  # True

        .. seealso::

            - :meth:`BoolVar.make_optional`, :meth:`BoolVar.make_absent`.
            - :meth:`BoolVar.is_optional`, :meth:`BoolVar.is_present`, :meth:`BoolVar.is_absent`.
        """
        self._props.pop('status', None)

    def set_min(self, min_val: bool) -> None:
        r"""
        Sets the minimum value of the boolean variable to the given value.

        :param min_val: The minimum value to set (True or False)
        :type min_val: bool

        ## Details

        It overwrites any previous minimum value limit given at variable creation by
        :meth:`Model.bool_var` or later by
        :meth:`BoolVar.set_min` or :meth:`BoolVar.set_range`.
        This function does not change the maximum value.

        Setting `set_min(True)` fixes the variable to `True` (since maximum is `True` by default).
        Setting `set_min(False)` has no effect on a free variable (since minimum is `False` by default).

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.get_min())  # False
            x.set_min(True)
            print(x.get_min())  # True (variable is now fixed to True)

        .. seealso::

            - :meth:`BoolVar.set_max`, :meth:`BoolVar.set_range`.
            - :meth:`BoolVar.get_min`, :meth:`BoolVar.get_max`.
        """
        self._props['min'] = bool(min_val)

    def set_max(self, max_val: bool) -> None:
        r"""
        Sets the maximum value of the boolean variable to the given value.

        :param max_val: The maximum value to set (True or False)
        :type max_val: bool

        ## Details

        It overwrites any previous maximum value limit given at variable creation by
        :meth:`Model.bool_var` or later by
        :meth:`BoolVar.set_max` or :meth:`BoolVar.set_range`.
        This function does not change the minimum value.

        Setting `set_max(False)` fixes the variable to `False` (since minimum is `False` by default).
        Setting `set_max(True)` has no effect on a free variable (since maximum is `True` by default).

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            print(x.get_max())  # True
            x.set_max(False)
            print(x.get_max())  # False (variable is now fixed to False)

        .. seealso::

            - :meth:`BoolVar.set_min`, :meth:`BoolVar.set_range`.
            - :meth:`BoolVar.get_min`, :meth:`BoolVar.get_max`.
        """
        self._props['max'] = bool(max_val)

    def set_range(self, min_val: bool, max_val: bool) -> None:
        r"""
        Sets the value of the boolean variable to the given range.

        :param min_val: The minimum value to set (True or False)
        :type min_val: bool
        :param max_val: The maximum value to set (True or False)
        :type max_val: bool

        ## Details

        It overwrites any previous value limits given at variable creation by
        :meth:`Model.bool_var` or later by
        :meth:`BoolVar.set_min`, :meth:`BoolVar.set_max` or :meth:`BoolVar.set_range`.

        The call:
        .. code-block:: python

            bool_var.set_range(min_val, max_val)

        is equivalent to:
        .. code-block:: python

            bool_var.set_min(min_val)
            bool_var.set_max(max_val)

        Use `set_range(True, True)` to fix the variable to `True`.
        Use `set_range(False, False)` to fix the variable to `False`.
        Use `set_range(False, True)` to leave the variable free.

        ## Example

        .. code-block:: python

            import optalcp as cp

            model = cp.Model()
            x = model.bool_var(name="x")

            # Fix variable to True
            x.set_range(True, True)
            print(x.get_min(), x.get_max())  # True True

        .. seealso::

            - :meth:`BoolVar.set_min`, :meth:`BoolVar.set_max`.
            - :meth:`BoolVar.get_min`, :meth:`BoolVar.get_max`.
        """
        self._props['min'] = bool(min_val)
        self._props['max'] = bool(max_val)
