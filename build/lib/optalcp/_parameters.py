"""
Solver parameters.

Parameters control solver behavior including time limits, search strategies,
number of workers, and worker-specific settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Literal


def _parse_infinities(obj: dict[str, Any]) -> None:
    """Convert JSON infinity strings to Python float values."""
    for key in obj:
        if obj[key] == 'Infinity':
            obj[key] = float('inf')
        elif obj[key] == '-Infinity':
            obj[key] = float('-inf')


@dataclass(slots=True)
class WorkerParameters:
    r"""
    WorkerParameters specify the behavior of each worker separately.
    It is part of the :class:`Parameters` object.

    If a parameter is not listed here, then it can be set only globally (in :class:`Parameters`), not per worker.  For example, *timeLimit* or *logPeriod* are
    global parameters.
    """

    searchType: Literal['LNS', 'FDS', 'FDSLB', 'SetTimes'] | None = None
    r"""
    Type of search to use

    Possible values are:

    *  `LNS`: Large Neighborhood Search
    *  `FDS`: Failure-Directed Search
    *  `FDSLB`: Failure-Directed Searching working on lower bound
    *  `SetTimes`: Depth-first set-times search (not restarted)

    The default value is `LNS`.
    """

    randomSeed: int | None = None
    r"""
    Random seed

    The solver breaks ties randomly using a pseudorandom number generator. This parameter sets the seed of the generator.

    Note that when :attr:`Parameters.nbWorkers` is more than 1 then there is also another source of randomness: the time it takes for a message to pass from one worker to another. Therefore with 1 worker the solver is deterministic (random behavior depends only on random seed). With more workers the solver is not deterministic.

    Even with the same random seed, the solver may behave differently on different platforms. This can be due to different implementations of certain functions such as `std::sort`.

    The parameter takes an integer value.

    The default value is `1`.
    """

    _workerFailLimit: int | None = None
    _workerBranchLimit: int | None = None
    _workerSolutionLimit: int | None = None
    _workerLNSStepLimit: int | None = None
    _workerRestartLimit: int | None = None
    noOverlapPropagationLevel: int | None = None
    r"""
    How much to propagate noOverlap constraints

    This parameter controls the amount of propagation done for noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..4`.

    The default value is `2`.
    """

    cumulPropagationLevel: int | None = None
    r"""
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for cumulative constraints (e.g., `cumul <= limit`) when used with a sum of :meth:`Model.pulse` pulses.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..3`.

    The default value is `1`.
    """

    reservoirPropagationLevel: int | None = None
    r"""
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for cumulative constraints (e.g., `cumul <= limit`, `cumul >= limit`) when used together with steps (:meth:`Model.step_at_start`, :meth:`Model.step_at_end`, :meth:`Model.step_at`).
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..2`.

    The default value is `1`.
    """

    positionPropagationLevel: int | None = None
    r"""
    How much to propagate position expressions on noOverlap constraints

    This parameter controls the amount of propagation done for position expressions on noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    However, more propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..3`.

    The default value is `2`.
    """

    integralPropagationLevel: int | None = None
    r"""
    How much to propagate integral expression

    This parameter controls the amount of propagation done for :meth:`Model.integral` expressions.
    In particular, it controls whether the propagation also affects the minimum and the maximum length of the associated interval variable:

    * `1`: The length is updated only once during initial constraint propagation.
    * `2`: The length is updated every time the expression is propagated.

    The parameter takes an integer value in range `1..2`.

    The default value is `1`.
    """

    _packPropagationLevel: int | None = None
    _itvMappingPropagationLevel: int | None = None
    searchTraceLevel: int | None = None
    r"""
    Level of search trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the search.
    The trace contains information about every choice taken by the solver.
    The higher the value, the more information is printed.

    The parameter takes an integer value in range `0..5`.

    The default value is `0`.
    """

    propagationTraceLevel: int | None = None
    r"""
    Level of propagation trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the propagation,
    that is a line for every domain change.
    The higher the value, the more information is printed.

    The parameter takes an integer value in range `0..5`.

    The default value is `0`.
    """

    fdsInitialRating: float | None = None
    r"""
    Initial rating for newly created choices

    Default rating for newly created choices. Both left and right branches get the same rating.
    Choice is initially permuted so that bigger domain change is the left branch.

    The parameter takes a floating point value in range `0.0..2.0`.

    The default value is `0.5`.
    """

    fdsReductionWeight: float | None = None
    r"""
    Weight of the reduction factor in rating computation

    When computing the local rating of a branch, multiply reduction factor by the given weight.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `1`.
    """

    fdsRatingAverageLength: int | None = None
    r"""
    Length of average rating computed for choices

    For the computation of rating of a branch. Arithmetic average is used until the branch
    is taken at least FDSRatingAverageLength times. After that exponential moving average
    is used with parameter alpha = 1 - 1 / FDSRatingAverageLength.

    The parameter takes an integer value in range `0..254`.

    The default value is `25`.
    """

    fdsFixedAlpha: float | None = None
    r"""
    When non-zero, alpha factor for rating updates

    When this parameter is set to a non-zero, parameter FDSRatingAverageLength is ignored.
    Instead, the rating of a branch is computed as an exponential moving average with the given parameter alpha.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0`.
    """

    fdsRatingAverageComparison: Literal['Off', 'Global', 'Depth'] | None = None
    r"""
    Whether to compare the local rating with the average

    Possible values are:

     * `Off` (the default): No comparison is done.
     * `Global`: Compare with the global average.
     * `Depth`: Compare with the average on the current search depth

    Arithmetic average is used for global and depth averages.

    The default value is `Off`.
    """

    fdsReductionFactor: Literal['Normal', 'Zero', 'Random'] | None = None
    r"""
    Reduction factor R for rating computation

    Possible values are:

     * `Normal` (the default): Normal reduction factor.
     * `Zero`: Factor is not used (it is 0 all the time).
     * `Random`: A random number in the range [0,1] is used instead.

    The default value is `Normal`.
    """

    fdsReuseClosing: bool | None = None
    r"""
    Whether always reuse closing choice

    Most of the time, FDS reuses closing choice automatically. This parameter enforces it all the time.

    The default value is `False`.
    """

    fdsUniformChoiceStep: bool | None = None
    r"""
    Whether all initial choices have the same step length

    When set, then initial choices generated on interval variables will have the same step size.

    The default value is `True`.
    """

    fdsLengthStepRatio: float | None = None
    r"""
    Choice step relative to average length

    Ratio of initial choice step size to the minimum length of interval variable. When FDSUniformChoiceStep is set, this ratio is used to compute global choice step using the average of interval var length. When FDSUniformChoiceStep is not set, this ratio is used to compute the choice step for every interval var individually.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `0.699999988079071`.
    """

    fdsMaxInitialChoicesPerVariable: int | None = None
    r"""
    Maximum number of choices generated initially per a variable

    Initial domains are often very large (e.g., `0..IntervalMax`). Therefore initial
    number of generated choices is limited: only choices near startMin are kept.

    The parameter takes an integer value in range `2..2147483647`.

    The default value is `90`.
    """

    fdsAdditionalStepRatio: float | None = None
    r"""
    Domain split ratio when run out of choices

    When all choices are decided, and a greedy algorithm cannot find a solution, then
    more choices are generated by splitting domains into the specified number of pieces.

    The parameter takes a floating point value in range `2.0..Infinity`.

    The default value is `7`.
    """

    fdsPresenceStatusChoices: bool | None = None
    r"""
    Whether to generate choices on presence status

    Choices on start time also include a choice on presence status. Therefore, dedicated choices on presence status only are not mandatory.

    The default value is `True`.
    """

    fdsMaxInitialLengthChoices: int | None = None
    r"""
    Maximum number of initial choices on length of an interval variable

    When non-zero, this parameter limits the number of initial choices generated on length of an interval variable.
    When zero (the default), no choices on length are generated.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `0`.
    """

    fdsMinLengthChoiceStep: int | None = None
    r"""
    Maximum step when generating initial choices for length of an interval variable

    Steps between choices for length of an interval variable are never bigger than the specified value.

    The parameter takes an integer value in range `1..1073741823`.

    The default value is `1073741823`.
    """

    fdsMinIntVarChoiceStep: int | None = None
    r"""
    Minimum step when generating choices for integer variables.

    Steps between choices for integer variables are never smaller than the specified value.

    The parameter takes an integer value in range `1..1073741823`.

    The default value is `1073741823`.
    """

    fdsEventTimeInfluence: float | None = None
    r"""
    Influence of event time to initial choice rating

    When non-zero, the initial choice rating is influenced by the date of the choice.
    This way, very first choices in the search should be taken chronologically.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0`.
    """

    fdsBothFailRewardFactor: float | None = None
    r"""
    How much to improve rating when both branches fail immediately

    This parameter sets a bonus reward for a choice when both left and right branches fail immediately.
    Current rating of both branches is multiplied by the specified value.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0.98`.
    """

    fdsEpsilon: float | None = None
    r"""
    How often to chose a choice randomly

    Probability that a choice is taken randomly. A randomly selected choice is not added to the search tree automatically. Instead, the choice is tried, its rating is updated,
    but it is added to the search tree only if one of the branches fails.
    The mechanism is similar to strong branching.

    The parameter takes a floating point value in range `0.0..0.99999`.

    The default value is `0.1`.
    """

    fdsStrongBranchingSize: int | None = None
    r"""
    Number of choices to try in strong branching

    Strong branching means that instead of taking a choice with the best rating,
    we take the specified number (FDSStrongBranchingSize) of best choices,
    try them in dry-run mode, measure their local rating, and
    then chose the one with the best local rating.

    The parameter takes an integer value.

    The default value is `10`.
    """

    fdsStrongBranchingDepth: int | None = None
    r"""
    Up-to what search depth apply strong branching

    Strong branching is typically used in the root node. This parameter controls
    the maximum search depth when strong branching is used.

    The parameter takes an integer value.

    The default value is `6`.
    """

    fdsStrongBranchingCriterion: Literal['Both', 'Left', 'Right'] | None = None
    r"""
    How to choose the best choice in strong branching

    Possible values are:

    * `Both`: Choose the the choice with best combined rating.
    * `Left` (the default): Choose the choice with the best rating of the left branch.
    * `Right`: Choose the choice with the best rating of the right branch.

    The default value is `Left`.
    """

    fdsInitialRestartLimit: int | None = None
    r"""
    Fail limit for the first restart

    Failure-directed search is periodically restarted: explored part of the current search tree is turned into a no-good constraint, and the search starts again in the root node.
    This parameter specifies the size of the very first search tree (measured in number of failures).

    The parameter takes an integer value in range `1..9223372036854775807`.

    The default value is `100`.
    """

    fdsRestartStrategy: Literal['Geometric', 'Nested', 'Luby'] | None = None
    r"""
    Restart strategy to use

    This parameter specifies how the restart limit (maximum number of failures) changes from restart to restart.
    Possible values are:

    * `Geometric` (the default): After each restart, restart limit is multiplied by :attr:`Parameters.fdsRestartGrowthFactor`.
    * `Nested`: Similar to `Geometric` but the limit is changed back to :attr:`Parameters.fdsInitialRestartLimit` each time a new maximum limit is reached.
    * `Luby`: Luby restart strategy is used. Parameter :attr:`Parameters.fdsRestartGrowthFactor` is ignored.

    The default value is `Geometric`.
    """

    fdsRestartGrowthFactor: float | None = None
    r"""
    Growth factor for fail limit after each restart

    After each restart, the fail limit for the restart is multiplied by the specified factor.
    This parameter is ignored when :attr:`Parameters.fdsRestartStrategy` is `Luby`.

    The parameter takes a floating point value in range `1.0..Infinity`.

    The default value is `1.15`.
    """

    fdsMaxCounterAfterRestart: int | None = None
    r"""
    Truncate choice use counts after a restart to this value

    The idea is that ratings learned in the previous restart are less valid in the new restart.
    Using this parameter, it is possible to truncate use counts on choices so that new local ratings will have bigger weights (when FDSFixedAlpha is not used).

    The parameter takes an integer value.

    The default value is `255`.
    """

    fdsMaxCounterAfterSolution: int | None = None
    r"""
    Truncate choice use counts after a solution is found

    Similar to :attr:`Parameters.fdsMaxCounterAfterRestart`, this parameter allows truncating use counts on choices when a solution is found.

    The parameter takes an integer value.

    The default value is `255`.
    """

    fdsResetRestartsAfterSolution: bool | None = None
    r"""
    Reset restart size after a solution is found (ignored in Luby)

    When this parameter is set (the default), then restart limit is set back to :attr:`Parameters.fdsInitialRestartLimit` when a solution is found.

    The default value is `True`.
    """

    fdsUseNogoods: bool | None = None
    r"""
    Whether to use or not nogood constraints

    By default, no-good constraint is generated after each restart. This parameter allows to turn no-good constraints off.

    The default value is `True`.
    """

    _fdsFreezeRatingsAfterProof: bool | None = None
    _fdsContinueAfterProof: bool | None = None
    _fdsRepeatLimit: int | None = None
    _fdsCompletelyRandom: bool | None = None
    fdsBranchOnObjective: bool | None = None
    r"""
    Whether to generate choices for objective expression/variable

    This option controls the generation of choices on the objective. It works regardless of the objective is given by an expression or a variable.

    The default value is `False`.
    """

    _fdsImproveNogoods: bool | None = None
    fdsBranchOrdering: Literal['FailureFirst', 'FailureLast', 'Random'] | None = None
    r"""
    Controls which side of a choice is explored first (considering the rating).

    This option can take the following values:

    * `FailureFirst`: Explore the failure side first.
    * `FailureLast`: Explore the failure side last.
    * `Random`: Explore either side randomly.

    The default value is `FailureFirst`.
    """

    _fdsDiveBySetTimes: bool | None = None
    fdsLBStrategy: Literal['Minimum', 'Random', 'Split'] | None = None
    r"""
    A strategy to choose objective cuts during FDSLB search.

    Possible values are:

    * `Minimum`: Always change the cut by the minimum amount.
    * `Random`: At each restart, randomly choose a value in range LB..UB. The default.
    * `Split`: Always split the current range LB..UB in half.

    The default value is `Random`.
    """

    fdsLBResetRatings: bool | None = None
    r"""
    Whether to reset ratings when a new LB is proved

    When this parameter is on, and FDSLB proves a new lower bound, then all ratings are reset to default values.

    The default value is `False`.
    """

    _lnsFirstFailLimit: int | None = None
    _lnsFailLimitGrowthFactor: float | None = None
    _lnsFailLimitCoefficient: float | None = None
    _lnsIterationsAfterFirstSolution: int | None = None
    _lnsAggressiveDominance: bool | None = None
    _lnsSameSolutionPeriod: int | None = None
    _lnsTier1Size: int | None = None
    _lnsTier2Size: int | None = None
    _lnsTier3Size: int | None = None
    _lnsTier2Effort: float | None = None
    _lnsTier3Effort: float | None = None
    _lnsStepFailLimitFactor: float | None = None
    _lnsApplyCutProbability: float | None = None
    _lnsSmallStructureLimit: int | None = None
    _lnsResourceOptimization: bool | None = None
    _lnsRestoreAbsentIntervals: bool | None = None
    _lnsRestoreIntervalLengths: bool | None = None
    _lnsRestoreIntVarValues: bool | None = None
    lnsUseWarmStartOnly: bool | None = None
    r"""
    Use only the user-provided warm start as the initial solution in LNS

    When this parameter is on, the solver will use only the user-specified warm start solution for the initial solution phase in LNS. If no warm start is provided, the solver will search for its own initial solution as usual.

    The default value is `False`.
    """

    _lnsHeuristicsEpsilon: float | None = None
    _lnsHeuristicsAlpha: float | None = None
    _lnsHeuristicsTemperature: float | None = None
    _lnsHeuristicsUniform: bool | None = None
    _lnsHeuristicsInitialQ: float | None = None
    _lnsPortionEpsilon: float | None = None
    _lnsPortionAlpha: float | None = None
    _lnsPortionTemperature: float | None = None
    _lnsPortionUniform: bool | None = None
    _lnsPortionInitialQ: float | None = None
    _lnsPortionHandicapLimit: float | None = None
    _lnsPortionHandicapValue: float | None = None
    _lnsPortionHandicapInitialQ: float | None = None
    _lnsNeighborhoodStrategy: int | None = None
    _lnsNeighborhoodEpsilon: float | None = None
    _lnsNeighborhoodAlpha: float | None = None
    _lnsNeighborhoodTemperature: float | None = None
    _lnsNeighborhoodUniform: bool | None = None
    _lnsNeighborhoodInitialQ: float | None = None
    _lnsDivingLimit: int | None = None
    _lnsDivingFailLimitRatio: float | None = None
    _lnsLearningRun: bool | None = None
    _lnsStayOnObjective: bool | None = None
    _lnsFDS: bool | None = None
    _lnsFreezeIntervalsBeforeFragment: bool | None = None
    _lnsRelaxSlack: float | None = None
    _lnsPortionMultiplier: float | None = None
    simpleLBWorker: int | None = None
    r"""
    Which worker computes simple lower bound

    Simple lower bound is a bound such that infeasibility of a better objective can be proved by propagation only (without the search). The given worker computes simple lower bound before it starts the normal search. If a worker with the given number doesn't exist, then the lower bound is not computed.

    The parameter takes an integer value in range `-1..2147483647`.

    The default value is `0`.
    """

    simpleLBMaxIterations: int | None = None
    r"""
    Maximum number of feasibility checks

    Simple lower bound is computed by binary search for the best objective value that is not infeasible by propagation. This parameter limits the maximum number of iterations of the binary search. When the value is 0, then simple lower bound is not computed at all.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `2147483647`.
    """

    simpleLBShavingRounds: int | None = None
    r"""
    Number of shaving rounds

    When non-zero, the solver shaves on variable domains to improve the lower bound. This parameter controls the number of shaving rounds.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `0`.
    """

    _debugTraceLevel: int | None = None
    _memoryTraceLevel: int | None = None
    _propagationDetailTraceLevel: int | None = None
    _setTimesTraceLevel: int | None = None
    _communicationTraceLevel: int | None = None
    _conversionTraceLevel: int | None = None
    _expressionBuilderTraceLevel: int | None = None
    _memorizationTraceLevel: int | None = None
    _searchDetailTraceLevel: int | None = None
    _fdsTraceLevel: int | None = None
    _shavingTraceLevel: int | None = None
    _fdsRatingsTraceLevel: int | None = None
    _lnsTraceLevel: int | None = None
    _heuristicReplayTraceLevel: int | None = None
    _allowSetTimesProofs: bool | None = None
    _setTimesAggressiveDominance: bool | None = None
    _setTimesExtendsCoef: float | None = None
    _setTimesHeightStrategy: Literal['FromMax', 'FromMin', 'Random'] | None = None
    _setTimesItvMappingStrategy: Literal['FromMax', 'FromMin', 'Random'] | None = None
    _setTimesInitDensity: float | None = None
    _setTimesDensityLength: int | None = None
    _setTimesDensityReliabilityThreshold: int | None = None
    _setTimesNbExtendsFactor: float | None = None
    _discreteLowCapacityLimit: int | None = None
    _lnsTrainingObjectiveLimit: float | None = None
    _posAbsentRelated: bool | None = None
    _defaultCallbackBlockSize: int | None = None
    _useReservoirPegging: bool | None = None
    _useTimeNet: bool | None = None
    _timeNetVarsToPreprocess: int | None = None
    _timeNetSubPriorityBits: int | None = None


    def _to_dict(self) -> dict[str, Any]:
        """Convert set parameters to a dictionary for JSON serialization."""
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}

    def _from_dict(self, data: dict[str, Any]) -> None:
        """Restore parameters from dictionary created by _to_dict()."""
        _parse_infinities(data)
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass(slots=True)
class Parameters:
    r"""
    Parameters specify how the solver should behave.  For example, the
    number of workers (threads) to use, the time limit, etc.

    Parameters can be passed to the solver functions :meth:`Model.solve`
    and :meth:`Solver.solve`.

    ## Example

    In the following example, we are using the *TimeLimit* parameter to specify
    that the solver should stop after 5 minutes. We also specify that the solver
    should use 4 threads. Finally, we specify that the solver should use
    *FDS* search (in all threads).

    .. code-block:: python

        import optalcp as cp

        params = cp.Parameters(
            timeLimit = 300,  # In seconds, i.e. 5 minutes
            nbWorkers = 4,    # Use 4 threads
            searchType = "FDS"
        )
        result = my_model.solve(params)

    ### Worker-specific parameters

    Some parameters can be specified differently for each worker.  For example,
    some workers may use *LNS* search while others use *FDS* search.  To specify
    worker-specific parameters, use the *workers* parameter and pass an array
    of :class:`WorkerParameters`.

    Not all parameters can be specified per worker. For example, *TimeLimit* is a
    global parameter. See :class:`WorkerParameters` for the list of parameters
    that can be specified per worker.

    If a parameter is not set specifically for a worker, the global value is used.

    ## Example

    In the following example, we are going to use 4 workers; two of them will run
    *FDS* search and the remaining two will run *LNS* search.  In addition, workers
    that use *FDS* search will use increased propagation levels.

    .. code-block:: python

        import optalcp as cp

        # Parameters for a worker that uses FDS search.
        # FDS works best with increased propagation levels, so set them:
        fds_worker = cp.WorkerParameters(
            searchType = "FDS",
            noOverlapPropagationLevel = 4,
            cumulPropagationLevel = 3,
            reservoirPropagationLevel = 2
        )
        # Global parameters:
        params = cp.Parameters(
            timeLimit = 60,      # In seconds, i.e. 1 minute
            searchType = "LNS",  # The default search type. It is not necessary, as "LNS" is the default value.
            nbWorkers = 4,       # Use 4 threads
            # The first two workers will use FDS search.
            # The remaining two workers will use the defaults, i.e., LNS search with default propagation levels.
            workers = [fds_worker, fds_worker]
        )
        result = my_model.solve(params)

    .. seealso::

        - :class:`WorkerParameters` for worker-specific parameters.
    """

    color: Literal['Never', 'Auto', 'Always'] | None = None
    r"""
    Whether to colorize output to the terminal

    This parameter controls when terminal output is colorized. Possible values are:

    *  `Never`: don't colorize the output.
    *  `Auto`: colorize if the output is a supported terminal.
    *  `Always`: always colorize the output.

    The default value is `Auto`.
    """

    nbWorkers: int | None = None
    r"""
    Number of threads dedicated to search

    When this parameter is 0 (the default), the number of workers is determined the following way:

     * If environment variable `OPTALCP_NB_WORKERS` is set, its value is used.
     * Otherwise, all available cores are used.

    The parameter takes an integer value.

    The default value is `0`.
    """

    _nbHelpers: int | None = None
    searchType: Literal['LNS', 'FDS', 'FDSLB', 'SetTimes'] | None = None
    r"""
    Type of search to use

    Possible values are:

    *  `LNS`: Large Neighborhood Search
    *  `FDS`: Failure-Directed Search
    *  `FDSLB`: Failure-Directed Searching working on lower bound
    *  `SetTimes`: Depth-first set-times search (not restarted)

    The default value is `LNS`.
    """

    randomSeed: int | None = None
    r"""
    Random seed

    The solver breaks ties randomly using a pseudorandom number generator. This parameter sets the seed of the generator.

    Note that when :attr:`Parameters.nbWorkers` is more than 1 then there is also another source of randomness: the time it takes for a message to pass from one worker to another. Therefore with 1 worker the solver is deterministic (random behavior depends only on random seed). With more workers the solver is not deterministic.

    Even with the same random seed, the solver may behave differently on different platforms. This can be due to different implementations of certain functions such as `std::sort`.

    The parameter takes an integer value.

    The default value is `1`.
    """

    logLevel: int | None = None
    r"""
    Level of the log

    This parameter controls the amount of text the solver writes on standard output. The solver is completely silent when this option is set to 0.

    The parameter takes an integer value in range `0..3`.

    The default value is `2`.
    """

    warningLevel: int | None = None
    r"""
    Level of warnings

    This parameter controls the types of warnings the solver emits. When this parameter is set to 0 then no warnings are emitted.

    The parameter takes an integer value in range `0..3`.

    The default value is `2`.
    """

    logPeriod: float | None = None
    r"""
    How often to print log messages (in seconds)

    When :attr:`Parameters.logLevel` &ge; 2 then solver writes a log message every `logPeriod` seconds. The log message contains the current statistics about the solve: number of branches, number of fails, memory used, etc.

    The parameter takes a floating point value in range `0.01..Infinity`.

    The default value is `10`.
    """

    verifySolutions: bool | None = None
    r"""
    When on, the correctness of solutions is verified

    Verification is an independent algorithm that checks whether all constraints in the model are satisfied (or absent), and that objective value was computed correctly. Verification is a somewhat redundant process as all solutions should be correct. Its purpose is to double-check and detect bugs in the solver.

    The default value is `False`.
    """

    verifyExternalSolutions: bool | None = None
    r"""
    Whether to verify correctness of external solutions

    External solutions can be passed to the solver as a warm start via :meth:`Model.solve`, or using :meth:`Solver.send_solution` during the search. Normally, all external solutions are checked before they are used. However, the check may be time consuming, especially if too many external solutions are sent simultaneously. This parameter allows to turn the check off.

    The default value is `True`.
    """

    allocationBlockSize: int | None = None
    r"""
    The minimal amount of memory in kB for a single allocation

    The solver allocates memory in blocks. This parameter sets the minimal size of a block. Larger blocks mean a higher risk of wasting memory. However, larger blocks may also lead to better performance, particularly when the size matches the page size supported by the operating system.

    The value of this parameter must be a power of 2.

    The default value of 2048 means 2MB, which means that up to ~12MB can be wasted per worker in the worst case.

    The parameter takes an integer value in range `4..1073741824`.

    The default value is `2048`.
    """

    processExitTimeout: float | None = None
    r"""
    Timeout for solver process to exit after finishing

    After the solver finishes, wait up to this many seconds for the process to exit. If it doesn't exit in time, it is silently killed.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `3`.
    """

    timeLimit: float | None = None
    r"""
    Wall clock limit for execution in seconds

    Caps the total wall-clock time spent by the solver. The timer starts as soon as the solve begins, and it includes presolve, search, and verification. When the limit is reached, all workers stop cooperatively. Leave it at the default `Infinity` to run without a time bound.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `Infinity`.
    """

    solutionLimit: int | None = None
    r"""
    Stop the search after the given number of solutions

    Terminates the solve after the specified number of solutions have been found and reported. A common setting is `1` if you only care about the first feasible or optimal solution, but you can raise it to enumerate a handful of alternatives (e.g., for warm starts). The default `UInt64Max` means no limit.

    The parameter takes an integer value.

    The default value is `18446744073709551615`.
    """

    _workerFailLimit: int | None = None
    _workerBranchLimit: int | None = None
    _workerSolutionLimit: int | None = None
    _workerLNSStepLimit: int | None = None
    _workerRestartLimit: int | None = None
    absoluteGapTolerance: float | None = None
    r"""
    Stop the search when the gap is below the tolerance

    The search is stopped if the absolute difference between the current solution
    value and current lower/upper bound is not bigger than the specified value.

    This parameter works together with :attr:`Parameters.relativeGapTolerance` as an OR condition: the search stops when *either* the absolute gap or the relative gap is within tolerance.

    The parameter takes a floating point value.

    The default value is `0`.
    """

    relativeGapTolerance: float | None = None
    r"""
    Stop the search when the gap is below the tolerance

    The search is stopped if the relative difference between the current solution
    value and current lower/upper bound is not bigger than the specified value.

    This parameter works together with :attr:`Parameters.absoluteGapTolerance` as an OR condition: the search stops when *either* the absolute gap or the relative gap is within tolerance.

    The parameter takes a floating point value.

    The default value is `0.0001`.
    """

    _tagsFromNames: Literal['Never', 'Auto', 'Merge', 'Force'] | None = None
    noOverlapPropagationLevel: int | None = None
    r"""
    How much to propagate noOverlap constraints

    This parameter controls the amount of propagation done for noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..4`.

    The default value is `2`.
    """

    cumulPropagationLevel: int | None = None
    r"""
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for cumulative constraints (e.g., `cumul <= limit`) when used with a sum of :meth:`Model.pulse` pulses.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..3`.

    The default value is `1`.
    """

    reservoirPropagationLevel: int | None = None
    r"""
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for cumulative constraints (e.g., `cumul <= limit`, `cumul >= limit`) when used together with steps (:meth:`Model.step_at_start`, :meth:`Model.step_at_end`, :meth:`Model.step_at`).
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..2`.

    The default value is `1`.
    """

    positionPropagationLevel: int | None = None
    r"""
    How much to propagate position expressions on noOverlap constraints

    This parameter controls the amount of propagation done for position expressions on noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    However, more propagation doesn't necessarily mean better performance.
    FDS search (see :attr:`Parameters.searchType`) usually benefits from higher propagation levels.

    The parameter takes an integer value in range `1..3`.

    The default value is `2`.
    """

    integralPropagationLevel: int | None = None
    r"""
    How much to propagate integral expression

    This parameter controls the amount of propagation done for :meth:`Model.integral` expressions.
    In particular, it controls whether the propagation also affects the minimum and the maximum length of the associated interval variable:

    * `1`: The length is updated only once during initial constraint propagation.
    * `2`: The length is updated every time the expression is propagated.

    The parameter takes an integer value in range `1..2`.

    The default value is `1`.
    """

    usePrecedenceEnergy: int | None = None
    r"""
    Whether to use precedence energy propagation algorithm

    Precedence energy algorithm improves propagation of precedence constraints when an interval has multiple predecessors (or successors) which use the same resource (noOverlap or cumulative constraint). In this case, the predecessors (or successors) may be in disjunction. Precedence energy algorithm can leverage this information and propagate the precedence constraint more aggressively.

    The parameter takes an integer value: `0` to disable, `1` to enable.

    The default value is `0`.
    """

    _packPropagationLevel: int | None = None
    _itvMappingPropagationLevel: int | None = None
    searchTraceLevel: int | None = None
    r"""
    Level of search trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the search.
    The trace contains information about every choice taken by the solver.
    The higher the value, the more information is printed.

    The parameter takes an integer value in range `0..5`.

    The default value is `0`.
    """

    propagationTraceLevel: int | None = None
    r"""
    Level of propagation trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the propagation,
    that is a line for every domain change.
    The higher the value, the more information is printed.

    The parameter takes an integer value in range `0..5`.

    The default value is `0`.
    """

    infoTraceLevel: int | None = None
    r"""
    Level of information trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints various high-level information.
    The higher the value, the more information is printed.

    The parameter takes an integer value in range `0..5`.

    The default value is `0`.
    """

    fdsInitialRating: float | None = None
    r"""
    Initial rating for newly created choices

    Default rating for newly created choices. Both left and right branches get the same rating.
    Choice is initially permuted so that bigger domain change is the left branch.

    The parameter takes a floating point value in range `0.0..2.0`.

    The default value is `0.5`.
    """

    fdsReductionWeight: float | None = None
    r"""
    Weight of the reduction factor in rating computation

    When computing the local rating of a branch, multiply reduction factor by the given weight.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `1`.
    """

    fdsRatingAverageLength: int | None = None
    r"""
    Length of average rating computed for choices

    For the computation of rating of a branch. Arithmetic average is used until the branch
    is taken at least FDSRatingAverageLength times. After that exponential moving average
    is used with parameter alpha = 1 - 1 / FDSRatingAverageLength.

    The parameter takes an integer value in range `0..254`.

    The default value is `25`.
    """

    fdsFixedAlpha: float | None = None
    r"""
    When non-zero, alpha factor for rating updates

    When this parameter is set to a non-zero, parameter FDSRatingAverageLength is ignored.
    Instead, the rating of a branch is computed as an exponential moving average with the given parameter alpha.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0`.
    """

    fdsRatingAverageComparison: Literal['Off', 'Global', 'Depth'] | None = None
    r"""
    Whether to compare the local rating with the average

    Possible values are:

     * `Off` (the default): No comparison is done.
     * `Global`: Compare with the global average.
     * `Depth`: Compare with the average on the current search depth

    Arithmetic average is used for global and depth averages.

    The default value is `Off`.
    """

    fdsReductionFactor: Literal['Normal', 'Zero', 'Random'] | None = None
    r"""
    Reduction factor R for rating computation

    Possible values are:

     * `Normal` (the default): Normal reduction factor.
     * `Zero`: Factor is not used (it is 0 all the time).
     * `Random`: A random number in the range [0,1] is used instead.

    The default value is `Normal`.
    """

    fdsReuseClosing: bool | None = None
    r"""
    Whether always reuse closing choice

    Most of the time, FDS reuses closing choice automatically. This parameter enforces it all the time.

    The default value is `False`.
    """

    fdsUniformChoiceStep: bool | None = None
    r"""
    Whether all initial choices have the same step length

    When set, then initial choices generated on interval variables will have the same step size.

    The default value is `True`.
    """

    fdsLengthStepRatio: float | None = None
    r"""
    Choice step relative to average length

    Ratio of initial choice step size to the minimum length of interval variable. When FDSUniformChoiceStep is set, this ratio is used to compute global choice step using the average of interval var length. When FDSUniformChoiceStep is not set, this ratio is used to compute the choice step for every interval var individually.

    The parameter takes a floating point value in range `0.0..Infinity`.

    The default value is `0.699999988079071`.
    """

    fdsMaxInitialChoicesPerVariable: int | None = None
    r"""
    Maximum number of choices generated initially per a variable

    Initial domains are often very large (e.g., `0..IntervalMax`). Therefore initial
    number of generated choices is limited: only choices near startMin are kept.

    The parameter takes an integer value in range `2..2147483647`.

    The default value is `90`.
    """

    fdsAdditionalStepRatio: float | None = None
    r"""
    Domain split ratio when run out of choices

    When all choices are decided, and a greedy algorithm cannot find a solution, then
    more choices are generated by splitting domains into the specified number of pieces.

    The parameter takes a floating point value in range `2.0..Infinity`.

    The default value is `7`.
    """

    fdsPresenceStatusChoices: bool | None = None
    r"""
    Whether to generate choices on presence status

    Choices on start time also include a choice on presence status. Therefore, dedicated choices on presence status only are not mandatory.

    The default value is `True`.
    """

    fdsMaxInitialLengthChoices: int | None = None
    r"""
    Maximum number of initial choices on length of an interval variable

    When non-zero, this parameter limits the number of initial choices generated on length of an interval variable.
    When zero (the default), no choices on length are generated.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `0`.
    """

    fdsMinLengthChoiceStep: int | None = None
    r"""
    Maximum step when generating initial choices for length of an interval variable

    Steps between choices for length of an interval variable are never bigger than the specified value.

    The parameter takes an integer value in range `1..1073741823`.

    The default value is `1073741823`.
    """

    fdsMinIntVarChoiceStep: int | None = None
    r"""
    Minimum step when generating choices for integer variables.

    Steps between choices for integer variables are never smaller than the specified value.

    The parameter takes an integer value in range `1..1073741823`.

    The default value is `1073741823`.
    """

    fdsEventTimeInfluence: float | None = None
    r"""
    Influence of event time to initial choice rating

    When non-zero, the initial choice rating is influenced by the date of the choice.
    This way, very first choices in the search should be taken chronologically.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0`.
    """

    fdsBothFailRewardFactor: float | None = None
    r"""
    How much to improve rating when both branches fail immediately

    This parameter sets a bonus reward for a choice when both left and right branches fail immediately.
    Current rating of both branches is multiplied by the specified value.

    The parameter takes a floating point value in range `0..1`.

    The default value is `0.98`.
    """

    fdsEpsilon: float | None = None
    r"""
    How often to chose a choice randomly

    Probability that a choice is taken randomly. A randomly selected choice is not added to the search tree automatically. Instead, the choice is tried, its rating is updated,
    but it is added to the search tree only if one of the branches fails.
    The mechanism is similar to strong branching.

    The parameter takes a floating point value in range `0.0..0.99999`.

    The default value is `0.1`.
    """

    fdsStrongBranchingSize: int | None = None
    r"""
    Number of choices to try in strong branching

    Strong branching means that instead of taking a choice with the best rating,
    we take the specified number (FDSStrongBranchingSize) of best choices,
    try them in dry-run mode, measure their local rating, and
    then chose the one with the best local rating.

    The parameter takes an integer value.

    The default value is `10`.
    """

    fdsStrongBranchingDepth: int | None = None
    r"""
    Up-to what search depth apply strong branching

    Strong branching is typically used in the root node. This parameter controls
    the maximum search depth when strong branching is used.

    The parameter takes an integer value.

    The default value is `6`.
    """

    fdsStrongBranchingCriterion: Literal['Both', 'Left', 'Right'] | None = None
    r"""
    How to choose the best choice in strong branching

    Possible values are:

    * `Both`: Choose the the choice with best combined rating.
    * `Left` (the default): Choose the choice with the best rating of the left branch.
    * `Right`: Choose the choice with the best rating of the right branch.

    The default value is `Left`.
    """

    fdsInitialRestartLimit: int | None = None
    r"""
    Fail limit for the first restart

    Failure-directed search is periodically restarted: explored part of the current search tree is turned into a no-good constraint, and the search starts again in the root node.
    This parameter specifies the size of the very first search tree (measured in number of failures).

    The parameter takes an integer value in range `1..9223372036854775807`.

    The default value is `100`.
    """

    fdsRestartStrategy: Literal['Geometric', 'Nested', 'Luby'] | None = None
    r"""
    Restart strategy to use

    This parameter specifies how the restart limit (maximum number of failures) changes from restart to restart.
    Possible values are:

    * `Geometric` (the default): After each restart, restart limit is multiplied by :attr:`Parameters.fdsRestartGrowthFactor`.
    * `Nested`: Similar to `Geometric` but the limit is changed back to :attr:`Parameters.fdsInitialRestartLimit` each time a new maximum limit is reached.
    * `Luby`: Luby restart strategy is used. Parameter :attr:`Parameters.fdsRestartGrowthFactor` is ignored.

    The default value is `Geometric`.
    """

    fdsRestartGrowthFactor: float | None = None
    r"""
    Growth factor for fail limit after each restart

    After each restart, the fail limit for the restart is multiplied by the specified factor.
    This parameter is ignored when :attr:`Parameters.fdsRestartStrategy` is `Luby`.

    The parameter takes a floating point value in range `1.0..Infinity`.

    The default value is `1.15`.
    """

    fdsMaxCounterAfterRestart: int | None = None
    r"""
    Truncate choice use counts after a restart to this value

    The idea is that ratings learned in the previous restart are less valid in the new restart.
    Using this parameter, it is possible to truncate use counts on choices so that new local ratings will have bigger weights (when FDSFixedAlpha is not used).

    The parameter takes an integer value.

    The default value is `255`.
    """

    fdsMaxCounterAfterSolution: int | None = None
    r"""
    Truncate choice use counts after a solution is found

    Similar to :attr:`Parameters.fdsMaxCounterAfterRestart`, this parameter allows truncating use counts on choices when a solution is found.

    The parameter takes an integer value.

    The default value is `255`.
    """

    fdsResetRestartsAfterSolution: bool | None = None
    r"""
    Reset restart size after a solution is found (ignored in Luby)

    When this parameter is set (the default), then restart limit is set back to :attr:`Parameters.fdsInitialRestartLimit` when a solution is found.

    The default value is `True`.
    """

    fdsUseNogoods: bool | None = None
    r"""
    Whether to use or not nogood constraints

    By default, no-good constraint is generated after each restart. This parameter allows to turn no-good constraints off.

    The default value is `True`.
    """

    _fdsFreezeRatingsAfterProof: bool | None = None
    _fdsContinueAfterProof: bool | None = None
    _fdsRepeatLimit: int | None = None
    _fdsCompletelyRandom: bool | None = None
    fdsBranchOnObjective: bool | None = None
    r"""
    Whether to generate choices for objective expression/variable

    This option controls the generation of choices on the objective. It works regardless of the objective is given by an expression or a variable.

    The default value is `False`.
    """

    _fdsImproveNogoods: bool | None = None
    fdsBranchOrdering: Literal['FailureFirst', 'FailureLast', 'Random'] | None = None
    r"""
    Controls which side of a choice is explored first (considering the rating).

    This option can take the following values:

    * `FailureFirst`: Explore the failure side first.
    * `FailureLast`: Explore the failure side last.
    * `Random`: Explore either side randomly.

    The default value is `FailureFirst`.
    """

    _fdsDiveBySetTimes: bool | None = None
    fdsLBStrategy: Literal['Minimum', 'Random', 'Split'] | None = None
    r"""
    A strategy to choose objective cuts during FDSLB search.

    Possible values are:

    * `Minimum`: Always change the cut by the minimum amount.
    * `Random`: At each restart, randomly choose a value in range LB..UB. The default.
    * `Split`: Always split the current range LB..UB in half.

    The default value is `Random`.
    """

    fdsLBResetRatings: bool | None = None
    r"""
    Whether to reset ratings when a new LB is proved

    When this parameter is on, and FDSLB proves a new lower bound, then all ratings are reset to default values.

    The default value is `False`.
    """

    _lnsFirstFailLimit: int | None = None
    _lnsFailLimitGrowthFactor: float | None = None
    _lnsFailLimitCoefficient: float | None = None
    _lnsIterationsAfterFirstSolution: int | None = None
    _lnsAggressiveDominance: bool | None = None
    _lnsSameSolutionPeriod: int | None = None
    _lnsTier1Size: int | None = None
    _lnsTier2Size: int | None = None
    _lnsTier3Size: int | None = None
    _lnsTier2Effort: float | None = None
    _lnsTier3Effort: float | None = None
    _lnsStepFailLimitFactor: float | None = None
    _lnsApplyCutProbability: float | None = None
    _lnsSmallStructureLimit: int | None = None
    _lnsResourceOptimization: bool | None = None
    _lnsRestoreAbsentIntervals: bool | None = None
    _lnsRestoreIntervalLengths: bool | None = None
    _lnsRestoreIntVarValues: bool | None = None
    lnsUseWarmStartOnly: bool | None = None
    r"""
    Use only the user-provided warm start as the initial solution in LNS

    When this parameter is on, the solver will use only the user-specified warm start solution for the initial solution phase in LNS. If no warm start is provided, the solver will search for its own initial solution as usual.

    The default value is `False`.
    """

    _lnsHeuristicsEpsilon: float | None = None
    _lnsHeuristicsAlpha: float | None = None
    _lnsHeuristicsTemperature: float | None = None
    _lnsHeuristicsUniform: bool | None = None
    _lnsHeuristicsInitialQ: float | None = None
    _lnsPortionEpsilon: float | None = None
    _lnsPortionAlpha: float | None = None
    _lnsPortionTemperature: float | None = None
    _lnsPortionUniform: bool | None = None
    _lnsPortionInitialQ: float | None = None
    _lnsPortionHandicapLimit: float | None = None
    _lnsPortionHandicapValue: float | None = None
    _lnsPortionHandicapInitialQ: float | None = None
    _lnsNeighborhoodStrategy: int | None = None
    _lnsNeighborhoodEpsilon: float | None = None
    _lnsNeighborhoodAlpha: float | None = None
    _lnsNeighborhoodTemperature: float | None = None
    _lnsNeighborhoodUniform: bool | None = None
    _lnsNeighborhoodInitialQ: float | None = None
    _lnsDivingLimit: int | None = None
    _lnsDivingFailLimitRatio: float | None = None
    _lnsLearningRun: bool | None = None
    _lnsStayOnObjective: bool | None = None
    _lnsFDS: bool | None = None
    _lnsFreezeIntervalsBeforeFragment: bool | None = None
    _lnsRelaxSlack: float | None = None
    _lnsPortionMultiplier: float | None = None
    simpleLBWorker: int | None = None
    r"""
    Which worker computes simple lower bound

    Simple lower bound is a bound such that infeasibility of a better objective can be proved by propagation only (without the search). The given worker computes simple lower bound before it starts the normal search. If a worker with the given number doesn't exist, then the lower bound is not computed.

    The parameter takes an integer value in range `-1..2147483647`.

    The default value is `0`.
    """

    simpleLBMaxIterations: int | None = None
    r"""
    Maximum number of feasibility checks

    Simple lower bound is computed by binary search for the best objective value that is not infeasible by propagation. This parameter limits the maximum number of iterations of the binary search. When the value is 0, then simple lower bound is not computed at all.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `2147483647`.
    """

    simpleLBShavingRounds: int | None = None
    r"""
    Number of shaving rounds

    When non-zero, the solver shaves on variable domains to improve the lower bound. This parameter controls the number of shaving rounds.

    The parameter takes an integer value in range `0..2147483647`.

    The default value is `0`.
    """

    _debugTraceLevel: int | None = None
    _memoryTraceLevel: int | None = None
    _propagationDetailTraceLevel: int | None = None
    _setTimesTraceLevel: int | None = None
    _communicationTraceLevel: int | None = None
    _presolveTraceLevel: int | None = None
    _conversionTraceLevel: int | None = None
    _expressionBuilderTraceLevel: int | None = None
    _memorizationTraceLevel: int | None = None
    _searchDetailTraceLevel: int | None = None
    _fdsTraceLevel: int | None = None
    _shavingTraceLevel: int | None = None
    _fdsRatingsTraceLevel: int | None = None
    _lnsTraceLevel: int | None = None
    _heuristicReplayTraceLevel: int | None = None
    _allowSetTimesProofs: bool | None = None
    _setTimesAggressiveDominance: bool | None = None
    _setTimesExtendsCoef: float | None = None
    _setTimesHeightStrategy: Literal['FromMax', 'FromMin', 'Random'] | None = None
    _setTimesItvMappingStrategy: Literal['FromMax', 'FromMin', 'Random'] | None = None
    _setTimesInitDensity: float | None = None
    _setTimesDensityLength: int | None = None
    _setTimesDensityReliabilityThreshold: int | None = None
    _setTimesNbExtendsFactor: float | None = None
    _discreteLowCapacityLimit: int | None = None
    _lnsTrainingObjectiveLimit: float | None = None
    _posAbsentRelated: bool | None = None
    _defaultCallbackBlockSize: int | None = None
    _useReservoirPegging: bool | None = None
    _useTimeNet: bool | None = None
    _timeNetVarsToPreprocess: int | None = None
    _timeNetSubPriorityBits: int | None = None


    pythonStreamBufferSize: int = field(default=2*1024*1024)
    r"""
    Size of the buffer for streaming solver output to Python.

    The solver output (logs) is streamed to Python in chunks of this size (in bytes).
    The default value is 2 MB (2097152 bytes).

    This parameter is Python-specific and does not exist in other APIs.
    """

    workers: list[WorkerParameters] = field(default_factory=list)
    r"""
    Per-worker parameter overrides.

    Each worker can have its own parameters. If a parameter is not specified
    for a worker, then the global value is used.

    Note that parameter :attr:`Parameters.nbWorkers` specifies the number of
    workers regardless of the length of this list.

    .. seealso::

        - :class:`WorkerParameters` for the list of parameters that can be set per worker.
    """

    def _to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        result = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ('workers', 'pythonStreamBufferSize') and getattr(self, f.name) is not None}
        if len(self.workers) > 0:
            result['workers'] = [w._to_dict() for w in self.workers]
        return result

    def _from_dict(self, data: dict[str, Any]) -> None:
        """Restore parameters from dictionary created by _to_dict()."""
        _parse_infinities(data)

        # Handle workers separately
        if 'workers' in data:
            self.workers = []
            for worker_data in data['workers']:
                worker = WorkerParameters()
                worker._from_dict(worker_data)
                self.workers.append(worker)

        # Set all other fields from the data
        for key, value in data.items():
            if key != 'workers' and hasattr(self, key):
                setattr(self, key, value)

    # TODO: _to_dict can be documented function
    # TODO: the same with _from_dict (user can have parameters stored in a JSON file).
    # TODO: A copy function can be useful to create modified copies of existing parameters.
