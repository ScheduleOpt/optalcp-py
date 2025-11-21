"""
Solver parameters.

Parameters control solver behavior including time limits, search strategies,
number of workers, and worker-specific settings.
"""

from __future__ import annotations
from typing import Optional, Any, Literal # type: ignore[reportUnusedImport]
from dataclasses import dataclass, field, fields

@dataclass(slots=True)
class WorkerParameters:
    """
    WorkerParameters specify the behavior of each worker separately.
    It is part of the :class:`Parameters` object.

    If a parameter is not listed here, then it can be set only globally (in :class:`Parameters`}), not per worker.  For example, *timeLimit* or *logPeriod* are
    global parameters.
    """

    searchType: Literal['LNS', 'FDS', 'FDSLB', 'SetTimes'] | None = None
    """
    Type of search to use

    Possible values are: 

    *  `LNS`: Large Neighborhood Search
    *  `FDS`: Failure-Directed Search
    *  `FDSLB`: Failure-Directed Searching working on lower bound
    *  `SetTimes`: Depth-first set-times search (not restarted)

    """

    randomSeed: int | None = None
    """
    Random seed

    The solver breaks ties randomly using a pseudorandom number generator. This parameter sets the seed of the generator.

    Note that when {@link Parameters.nbWorkers} is more than 1 then there is also another source of randomness: the time it takes for a message to pass from one worker to another. Therefore with {@link Parameters.nbWorkers}=1 the solver is deterministic (random behavior depends only on random seed). With {@link Parameters.nbWorkers}>1 the solver is not deterministic.

    Even with the same random seed, the solver may behave differently on different platforms. This can be due to different implementations of certain functions such as `std::sort`.
    """

    _workerFailLimit: int | None = None
    _workerBranchLimit: int | None = None
    _workerSolutionLimit: int | None = None
    _workerLNSStepLimit: int | None = None
    _workerRestartLimit: int | None = None
    noOverlapPropagationLevel: int | None = None
    """
    How much to propagate noOverlap constraints

    This parameter controls the amount of propagation done for noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    cumulPropagationLevel: int | None = None
    """
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for {@link Model.cumulLe} constraint when used with a sum of {@link Model.pulse | pulses}.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    reservoirPropagationLevel: int | None = None
    """
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for {@link Model.cumulLe} and {@link Model.cumulGe} when used together with steps ({@link Model.stepAtStart}, {@link Model.stepAtEnd}, {@link Model.stepAt}).
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    positionPropagationLevel: int | None = None
    """
    How much to propagate position expressions on noOverlap constraints

    This parameter controls the amount of propagation done for position expressions on noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    However, more propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    stepFunctionSumPropagationLevel: int | None = None
    """
    How much to propagate stepFunctionSum expression

    This parameter controls the amount of propagation done for {@link Model.stepFunctionSum} expressions.
    In particular, it controls whether the propagation also affects the minimum and the maximum length of the associated interval variable:

    * `1`: The length is updated only once during initial constraint propagation.
    * `2`: The length is updated every time the expression is propagated.

    """

    packPropagationLevel: int | None = None
    """
    How much to propagate pack constraints

    This parameter controls the amount of propagation done for {@link Model.pack} constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    itvMappingPropagationLevel: int | None = None
    """
    How much to propagate itvMapping constraint

    This parameter controls the amount of propagation done for {@link Model.itvMapping} constraint.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    searchTraceLevel: int | None = None
    """
    Level of search trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the search.
    The trace contains information about every choice taken by the solver.
    The higher the value, the more information is printed.

    """

    propagationTraceLevel: int | None = None
    """
    Level of propagation trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the propagation,
    that is a line for every domain change.
    The higher the value, the more information is printed.

    """

    fdsInitialRating: float | None = None
    """
    Initial rating for newly created choices

    Default rating for newly created choices. Both left and right branches get the same rating.
    Choice is initially permuted so that bigger domain change is the left branch.
    """

    fdsReductionWeight: float | None = None
    """
    Weight of the reduction factor in rating computation

    When computing the local rating of a branch, multiply reduction factor by the given weight.
    """

    fdsRatingAverageLength: int | None = None
    """
    Length of average rating computed for choices

    For the computation of rating of a branch. Arithmetic average is used until the branch
    is taken at least FDSRatingAverageLength times. After that exponential moving average
    is used with parameter alpha = 1 - 1 / FDSRatingAverageLength.
    """

    fdsFixedAlpha: float | None = None
    """
    When non-zero, alpha factor for rating updates

    When this parameter is set to a non-zero, parameter FDSRatingAverageLength is ignored.
    Instead, the rating of a branch is computed as an exponential moving average with the given parameter alpha.
    """

    fdsRatingAverageComparison: Literal['Off', 'Global', 'Depth'] | None = None
    """
    Whether to compare the local rating with the average

    Possible values are:

     * `Off` (the default): No comparison is done.
     * `Global`: Compare with the global average.
     * `Depth`: Compare with the average on the current search depth

    Arithmetic average is used for global and depth averages.
    """

    fdsReductionFactor: Literal['Normal', 'Zero', 'Random'] | None = None
    """
    Reduction factor R for rating computation

    Possible values are:

     * `Normal` (the default): Normal reduction factor.
     * `Zero`: Factor is not used (it is 0 all the time).
     * `Random`: A random number in the range [0,1] is used instead.

    """

    fdsReuseClosing: bool | None = None
    """
    Whether always reuse closing choice

    Most of the time, FDS reuses closing choice automatically. This parameter enforces it all the time.
    """

    fdsUniformChoiceStep: bool | None = None
    """
    Whether all initial choices have the same step length

    When set, then initial choices generated on interval variables will have the same step size.
    """

    fdsLengthStepRatio: float | None = None
    """
    Choice step relative to average length

    Ratio of initial choice step size to the minimum length of interval variable.When FDSUniformChoiceStep is set, this ratio is used to compute global choice step using the average of interval var length.When FDSUniformChoiceStep is not set, this ratio is used to compute the choice step for every interval var individually.
    """

    fdsMaxInitialChoicesPerVariable: int | None = None
    """
    Maximum number of choices generated initially per a variable

    Initial domains are often very large (e.g., `0..IntervalMax`). Therefore initial
    number of generated choices is limited: only choices near startMin are kept.
    """

    fdsAdditionalStepRatio: float | None = None
    """
    Domain split ratio when run out of choices

    When all choices are decided, and a greedy algorithm cannot find a solution, then
    more choices are generated by splitting domains into the specified number of pieces.
    """

    fdsPresenceStatusChoices: bool | None = None
    """
    Whether to generate choices on presence status

    Choices on start time also include a choice on presence status. Therefore, dedicated choices on presence status only are not mandatory.
    """

    fdsMaxInitialLengthChoices: int | None = None
    """
    Maximum number of initial choices on length of an interval variable

    When non-zero, this parameter limits the number of initial choices generated on length of an interval variable.
    When zero (the default), no choices on length are generated.
    """

    fdsMinLengthChoiceStep: int | None = None
    """
    Maximum step when generating initial choices for length of an interval variable

    Steps between choices for length of an interval variable are never bigger than the specified value.

    """

    fdsMinIntVarChoiceStep: int | None = None
    """
    Minimum step when generating choices for integer variables.

    Steps between choices for integer variables are never smaller than the specified value.
    """

    fdsEventTimeInfluence: float | None = None
    """
    Influence of event time to initial choice rating

    When non-zero, the initial choice rating is influenced by the date of the choice.
    This way, very first choices in the search should be taken chronologically.
    """

    fdsBothFailRewardFactor: float | None = None
    """
    How much to improve rating when both branches fail immediately

    This parameter sets a bonus reward for a choice when both left and right branches fail immediately.
    Current rating of both branches is multiplied by the specified value.
    """

    fdsEpsilon: float | None = None
    """
    How often to chose a choice randomly

    Probability that a choice is taken randomly. A randomly selected choice is not added to the search tree automatically. Instead, the choice is tried, its rating is updated,
    but it is added to the search tree only if one of the branches fails.
    The mechanism is similar to strong branching.
    """

    fdsStrongBranchingSize: int | None = None
    """
    Number of choices to try in strong branching

    Strong branching means that instead of taking a choice with the best rating,
    we take the specified number (FDSStrongBranchingSize) of best choices,
    try them in dry-run mode, measure their local rating, and
    then chose the one with the best local rating.

    """

    fdsStrongBranchingDepth: int | None = None
    """
    Up-to what search depth apply strong branching

    Strong branching is typically used in the root node. This parameter controls
    the maximum search depth when strong branching is used.
    """

    fdsStrongBranchingCriterion: Literal['Both', 'Left', 'Right'] | None = None
    """
    How to choose the best choice in strong branching

    Possible values are:

    * `Both`: Choose the the choice with best combined rating.
    * `Left` (the default): Choose the choice with the best rating of the left branch.
    * `Right`: Choose the choice with the best rating of the right branch.

    """

    fdsInitialRestartLimit: int | None = None
    """
    Fail limit for the first restart

    Failure-directed search is periodically restarted: explored part of the current search tree is turned into a no-good constraint, and the search starts again in the root node.
    This parameter specifies the size of the very first search tree (measured in number of failures).
    """

    fdsRestartStrategy: Literal['Geometric', 'Nested', 'Luby'] | None = None
    """
    Restart strategy to use

    This parameter specifies how the restart limit (maximum number of failures) changes from restart to restart.
    Possible values are:

    * `Geometric` (the default): After each restart, restart limit is multiplied by {@link fdsRestartGrowthFactor}.
    * `Nested`: Similar to `Geometric` but the limit is changed back to {@link fdsInitialRestartLimit} each time a new maximum limit is reached.
    * `Luby`: Luby restart strategy is used. Parameter {@link fdsRestartGrowthFactor} is ignored.
    """

    fdsRestartGrowthFactor: float | None = None
    """
    Growth factor for fail limit after each restart

    After each restart, the fail limit for the restart is multiplied by the specified factor.
    This parameter is ignored when {@link fdsRestartStrategy} is `Luby`.
    """

    fdsMaxCounterAfterRestart: int | None = None
    """
    Truncate choice use counts after a restart to this value

    The idea is that ratings learned in the previous restart are less valid in the new restart.
    Using this parameter, it is possible to truncate use counts on choices so that new local ratings will have bigger weights (when FDSFixedAlpha is not used).
    """

    fdsMaxCounterAfterSolution: int | None = None
    """
    Truncate choice use counts after a solution is found

    Similar to `FDSMaxCounterAfterRestart`, this parameter allows truncating use counts on choices when a solution is found.
    """

    fdsResetRestartsAfterSolution: bool | None = None
    """
    Reset restart size after a solution is found (ignored in Luby)

    When this parameter is set (the default), then restart limit is set back to `FDSInitialRestartLimit` when a solution is found.
    """

    fdsUseNogoods: bool | None = None
    """
    Whether to use or not nogood constraints

    By default, no-good constraint is generated after each restart. This parameter allows to turn no-good constraints off.
    """

    _fdsFreezeRatingsAfterProof: bool | None = None
    _fdsContinueAfterProof: bool | None = None
    _fdsRepeatLimit: int | None = None
    _fdsCompletelyRandom: bool | None = None
    fdsBranchOnObjective: bool | None = None
    """
    Whether to generate choices for objective expression/variable

    This option controls the generation of choices on the objective. It works regardless of the objective is given by an expression or a variable.
    """

    _fdsImproveNogoods: bool | None = None
    fdsBranchOrdering: Literal['FailureFirst', 'FailureLast', 'Random'] | None = None
    """
    Controls which side of a choice is is explored first (considering the rating).

    This option can take the following values:

    * `FailureFirst`: Explore the failure side first.
    * `FailureLast`: Explore the failure side last.
    * `Random`: Explore either side randomly.
    """

    _fdsDiveBySetTimes: bool | None = None
    fdsLBStrategy: Literal['Minimum', 'Random', 'Split'] | None = None
    """
    A strategy to choose objective cuts during FDSLB search.

    Possible values are:

    * `Minimum`: Always change the cut by the minimum amount.
    * `Random`: At each restart, randomly choose a value in range LB..UB. The default.
    * `Split`: Always split the current range LB..UB in half.

    """

    fdsLBResetRatings: bool | None = None
    """
    Whether to reset ratings when a new LB is proved

    When this parameter is on, and FDSLB proves a new lower bound, then all ratings are reset to default values.
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
    """
    Use only the user-provided warm start as the initial solution in LNS

    When this parameter is on, the solver will use only the user-specified warm start solution for the initial solution phase in LNS. If no warm start is provided, the solver will search for its own initial solution as usual.
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
    """
    Which worker computes simple lower bound

    Simple lower bound is a bound such that infeasibility of a better objective can be proved by propagation only (without the search). The given worker computes simple lower bound before it starts the normal search. If a worker with the given number doesn't exist, then the lower bound is not computed.
    """

    simpleLBMaxIterations: int | None = None
    """
    Maximum number of feasibility checks

    Simple lower bound is computed by binary search for the best objective value that is not infeasible by propagation. This parameter limits the maximum number of iterations of the binary search. When the value is 0, then simple lower bound is not computed at all.
    """

    simpleLBShavingRounds: int | None = None
    """
    Number of shaving rounds

    When non-zero, the solver shaves on variable domains to improve the lower bound. This parameter controls the number of shaving rounds.
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
    _pOSAbsentRelated: bool | None = None
    _defaultCallbackBlockSize: int | None = None
    _useReservoirPegging: bool | None = None
    _useTimeNet: bool | None = None
    _timeNetVarsToPreprocess: int | None = None
    _timeNetSubPriorityBits: int | None = None


    def _to_dict(self) -> dict[str, Any]:
        """Convert set parameters to a dictionary for JSON serialization."""
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}

@dataclass(slots=True)
class Parameters:
    """
    Parameters specify how the solver should behave.  For example, the
    number of workers (threads) to use, the time limit, etc.

    Parameters can be passed to the solver using function :func:`solve`
    or by the constructor of the class :class:`Solver`.

    In the following example, we are using the *TimeLimit* parameter to specify
    that the solver should stop after 5 minutes. We also specify that the solver
    should use 4 threads. Finally, we specify that the solver should use
    *FDS* search (in all threads).

    ### Worker-specific parameters

    Some parameters can be specified differently for each worker.  For example,
    some workers may use *LNS* search while others use *FDS* search.  To specify
    worker-specific parameters, use the *workers* parameter and pass an array
    of :class:`WorkerParameters`.

    Not all parameters can be specified per worker. For example, *TimeLimit* is a
    global parameter. See :class:`WorkerParameters` for the list of parameters
    that can be specified per worker.

    If a parameter is not set specifically for a worker, the global value is used.

    In the following example, we are going to use 4 workers; two of them will run
    *FDS* search and the remaining two will run *LNS* search.  In addition, workers
    that use *FDS* search will use increased propagation levels.

    benchmarking (e.g., run the same model multiple times with different random
    seeds).

    .. seealso::

        - :meth:`WorkerParameters for worker-specific parameters.`.
        - :class:`BenchmarkParameters is an extension of Parameters to simplify`.
    """

    color: Literal['Never', 'Auto', 'Always'] | None = None
    """
    Whether to colorize output to the terminal

    This parameter controls when terminal output is colorized. Possible values are: 

    *  `never`: don't colorize the output.
    *  `auto`: colorize if the output is a supported terminal.
    *  `always`: always colorize the output.

    """

    nbWorkers: int | None = None
    """
    Number of threads dedicated to search

    When this parameter is 0 (the default), the number of workers is determined the following way:

     * If environment variable `OPTALCP_NB_WORKERS` is set, its value is used.
     * Otherwise, all available cores are used.


    """

    _nbHelpers: int | None = None
    searchType: Literal['LNS', 'FDS', 'FDSLB', 'SetTimes'] | None = None
    """
    Type of search to use

    Possible values are: 

    *  `LNS`: Large Neighborhood Search
    *  `FDS`: Failure-Directed Search
    *  `FDSLB`: Failure-Directed Searching working on lower bound
    *  `SetTimes`: Depth-first set-times search (not restarted)

    """

    randomSeed: int | None = None
    """
    Random seed

    The solver breaks ties randomly using a pseudorandom number generator. This parameter sets the seed of the generator.

    Note that when {@link Parameters.nbWorkers} is more than 1 then there is also another source of randomness: the time it takes for a message to pass from one worker to another. Therefore with {@link Parameters.nbWorkers}=1 the solver is deterministic (random behavior depends only on random seed). With {@link Parameters.nbWorkers}>1 the solver is not deterministic.

    Even with the same random seed, the solver may behave differently on different platforms. This can be due to different implementations of certain functions such as `std::sort`.
    """

    logLevel: int | None = None
    """
    Level of the log

    This parameter controls the amount of text the solver writes on standard output. The solver is completely silent when this option is set to 0.
    """

    warningLevel: int | None = None
    """
    Level of warnings

    This parameter controls the types of warnings the solver emits. When this parameter is set to 0 then no warnings are emitted. 
    """

    logPeriod: float | None = None
    """
    How often to print log messages (in seconds)

    When {@link logLevel} &ge; 2 then solver writes a log message every `logPeriod` seconds. The log message contains the current statistics about the solve: number of branches, number of fails, memory used, etc.

    """

    verifySolutions: bool | None = None
    """
    When on, the correctness of solutions is verified

    Verification is an independent algorithm that checks whether all constraints in the model are satisfied (or absent), and that objective value was computed correctly. Verification is a somewhat redundant process as all solutions should be correct. Its purpose is to double-check and detect bugs in the solver. 
    """

    verifyExternalSolutions: bool | None = None
    """
    Whether to verify corectness of external solutions

    External solutions can be passed to the solver as a `warmStart` before the search starts, or using `{@link Solver.sendSolution}` during the search. Normally, all external solutions are checked before they are used. However, the check may be time consuming, especially if too many external solutions are sent simultaneously. This parameter allows to turn the check off.
    """

    allocationBlockSize: int | None = None
    """
    The minimal amount of memory in kB for a single allocation

    The solver allocates memory in blocks. This parameter sets the minimal size of a block. Larger blocks mean a higher risk of wasting memory. However, larger blocks may also lead to better performance, particularly when the size matches the page size supported by the operating system.

    The value of this parameter must be a power of 2. 

    The default value is 2048 means 2MB, which means that up to ~12MB can be wasted per worker in the worst case.
    """

    timeLimit: float | None = None
    """
    Wall clock limit for execution

    Caps the total wall-clock time spent by the solver. The timer starts as soon as the solve begins, and it includes presolve, search, and verification. When the limit is reached, all workers stop cooperatively. Leave it at the default `Infinity` to run without a time bound.
    """

    solutionLimit: int | None = None
    """
    Stop the search after the given number of solutions

    Terminates the solve after the specified number of solutions have been found and reported. A common setting is 1 if you only care about the first feasible or optimal solution, but you can raise it to enumerate a handful of alternatives (e.g., for warm starts). The default `UInt64Max` means no limit.
    """

    _workerFailLimit: int | None = None
    _workerBranchLimit: int | None = None
    _workerSolutionLimit: int | None = None
    _workerLNSStepLimit: int | None = None
    _workerRestartLimit: int | None = None
    absoluteGapTolerance: float | None = None
    """
    Stop the search when the gap is below the tolerance

    The search is stopped if the absolute difference between the current solution
    value and current lower/upper bound is not bigger than the specified value.
    Note that parameters `AbsoluteGapTolerance` and `RelativeGapTolerance`
    are considered independently, i.e., the search stops if at least one of the conditions apply.
    """

    relativeGapTolerance: float | None = None
    """
    Stop the search when the gap is below the tolerance

    The search is stopped if the relative difference between the current solution
    value and current lower/upper bound is not bigger than the specified value.
    Note that parameters `AbsoluteGapTolerance` and `RelativeGapTolerance`
    are considered independently, i.e., the search stops if at least one of the conditions apply.
    """

    tagsFromNames: Literal['Never', 'Auto', 'Merge', 'Force'] | None = None
    """
    Whether to derive tags from names

    Tags can be derived from the prefix of names used in the model.
    The prefix stops with the first non-alpha character.
    Possible values are: 

    *  `never`: don't derive tags from names.
    *  `auto`: derive tags from names if no user tags are given (the default).
    *  `merge`: derive tag if there is a name but not a tag.
    *  `force`: ignore user-defined tags, use derived tags instead.

    """

    noOverlapPropagationLevel: int | None = None
    """
    How much to propagate noOverlap constraints

    This parameter controls the amount of propagation done for noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    cumulPropagationLevel: int | None = None
    """
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for {@link Model.cumulLe} constraint when used with a sum of {@link Model.pulse | pulses}.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    reservoirPropagationLevel: int | None = None
    """
    How much to propagate constraints on cumul functions

    This parameter controls the amount of propagation done for {@link Model.cumulLe} and {@link Model.cumulGe} when used together with steps ({@link Model.stepAtStart}, {@link Model.stepAtEnd}, {@link Model.stepAt}).
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    positionPropagationLevel: int | None = None
    """
    How much to propagate position expressions on noOverlap constraints

    This parameter controls the amount of propagation done for position expressions on noOverlap constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    However, more propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    stepFunctionSumPropagationLevel: int | None = None
    """
    How much to propagate stepFunctionSum expression

    This parameter controls the amount of propagation done for {@link Model.stepFunctionSum} expressions.
    In particular, it controls whether the propagation also affects the minimum and the maximum length of the associated interval variable:

    * `1`: The length is updated only once during initial constraint propagation.
    * `2`: The length is updated every time the expression is propagated.

    """

    usePrecedenceEnergy: int | None = None
    """
    Whether to use precedence energy propagation algorithm

    Precedence energy algorithm improves propagation of precedence constraints when an interval has multiple predecessors (or successors). which use the same resource (noOverlap or cumulative constraint). In this case, the predecessors (or successors) may be in disjunction. Precedence energy algorithm can leverage this information and propagate the precedence constraint more aggressively.


    """

    packPropagationLevel: int | None = None
    """
    How much to propagate pack constraints

    This parameter controls the amount of propagation done for {@link Model.pack} constraints.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    itvMappingPropagationLevel: int | None = None
    """
    How much to propagate itvMapping constraint

    This parameter controls the amount of propagation done for {@link Model.itvMapping} constraint.
    The bigger the value, the more algorithms are used for propagation.
    It means that more time is spent by the propagation, and possibly more values are removed from domains.
    More propagation doesn't necessarily mean better performance.
    FDS search (see {@link searchType}) usually benefits from higher propagation levels.

    """

    searchTraceLevel: int | None = None
    """
    Level of search trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the search.
    The trace contains information about every choice taken by the solver.
    The higher the value, the more information is printed.

    """

    propagationTraceLevel: int | None = None
    """
    Level of propagation trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints a trace of the propagation,
    that is a line for every domain change.
    The higher the value, the more information is printed.

    """

    infoTraceLevel: int | None = None
    """
    Level of information trace

    This parameter is available only in the development edition of the solver.

    When set to a value bigger than zero, the solver prints various high-level information.
    The higher the value, the more information is printed.

    """

    fdsInitialRating: float | None = None
    """
    Initial rating for newly created choices

    Default rating for newly created choices. Both left and right branches get the same rating.
    Choice is initially permuted so that bigger domain change is the left branch.
    """

    fdsReductionWeight: float | None = None
    """
    Weight of the reduction factor in rating computation

    When computing the local rating of a branch, multiply reduction factor by the given weight.
    """

    fdsRatingAverageLength: int | None = None
    """
    Length of average rating computed for choices

    For the computation of rating of a branch. Arithmetic average is used until the branch
    is taken at least FDSRatingAverageLength times. After that exponential moving average
    is used with parameter alpha = 1 - 1 / FDSRatingAverageLength.
    """

    fdsFixedAlpha: float | None = None
    """
    When non-zero, alpha factor for rating updates

    When this parameter is set to a non-zero, parameter FDSRatingAverageLength is ignored.
    Instead, the rating of a branch is computed as an exponential moving average with the given parameter alpha.
    """

    fdsRatingAverageComparison: Literal['Off', 'Global', 'Depth'] | None = None
    """
    Whether to compare the local rating with the average

    Possible values are:

     * `Off` (the default): No comparison is done.
     * `Global`: Compare with the global average.
     * `Depth`: Compare with the average on the current search depth

    Arithmetic average is used for global and depth averages.
    """

    fdsReductionFactor: Literal['Normal', 'Zero', 'Random'] | None = None
    """
    Reduction factor R for rating computation

    Possible values are:

     * `Normal` (the default): Normal reduction factor.
     * `Zero`: Factor is not used (it is 0 all the time).
     * `Random`: A random number in the range [0,1] is used instead.

    """

    fdsReuseClosing: bool | None = None
    """
    Whether always reuse closing choice

    Most of the time, FDS reuses closing choice automatically. This parameter enforces it all the time.
    """

    fdsUniformChoiceStep: bool | None = None
    """
    Whether all initial choices have the same step length

    When set, then initial choices generated on interval variables will have the same step size.
    """

    fdsLengthStepRatio: float | None = None
    """
    Choice step relative to average length

    Ratio of initial choice step size to the minimum length of interval variable.When FDSUniformChoiceStep is set, this ratio is used to compute global choice step using the average of interval var length.When FDSUniformChoiceStep is not set, this ratio is used to compute the choice step for every interval var individually.
    """

    fdsMaxInitialChoicesPerVariable: int | None = None
    """
    Maximum number of choices generated initially per a variable

    Initial domains are often very large (e.g., `0..IntervalMax`). Therefore initial
    number of generated choices is limited: only choices near startMin are kept.
    """

    fdsAdditionalStepRatio: float | None = None
    """
    Domain split ratio when run out of choices

    When all choices are decided, and a greedy algorithm cannot find a solution, then
    more choices are generated by splitting domains into the specified number of pieces.
    """

    fdsPresenceStatusChoices: bool | None = None
    """
    Whether to generate choices on presence status

    Choices on start time also include a choice on presence status. Therefore, dedicated choices on presence status only are not mandatory.
    """

    fdsMaxInitialLengthChoices: int | None = None
    """
    Maximum number of initial choices on length of an interval variable

    When non-zero, this parameter limits the number of initial choices generated on length of an interval variable.
    When zero (the default), no choices on length are generated.
    """

    fdsMinLengthChoiceStep: int | None = None
    """
    Maximum step when generating initial choices for length of an interval variable

    Steps between choices for length of an interval variable are never bigger than the specified value.

    """

    fdsMinIntVarChoiceStep: int | None = None
    """
    Minimum step when generating choices for integer variables.

    Steps between choices for integer variables are never smaller than the specified value.
    """

    fdsEventTimeInfluence: float | None = None
    """
    Influence of event time to initial choice rating

    When non-zero, the initial choice rating is influenced by the date of the choice.
    This way, very first choices in the search should be taken chronologically.
    """

    fdsBothFailRewardFactor: float | None = None
    """
    How much to improve rating when both branches fail immediately

    This parameter sets a bonus reward for a choice when both left and right branches fail immediately.
    Current rating of both branches is multiplied by the specified value.
    """

    fdsEpsilon: float | None = None
    """
    How often to chose a choice randomly

    Probability that a choice is taken randomly. A randomly selected choice is not added to the search tree automatically. Instead, the choice is tried, its rating is updated,
    but it is added to the search tree only if one of the branches fails.
    The mechanism is similar to strong branching.
    """

    fdsStrongBranchingSize: int | None = None
    """
    Number of choices to try in strong branching

    Strong branching means that instead of taking a choice with the best rating,
    we take the specified number (FDSStrongBranchingSize) of best choices,
    try them in dry-run mode, measure their local rating, and
    then chose the one with the best local rating.

    """

    fdsStrongBranchingDepth: int | None = None
    """
    Up-to what search depth apply strong branching

    Strong branching is typically used in the root node. This parameter controls
    the maximum search depth when strong branching is used.
    """

    fdsStrongBranchingCriterion: Literal['Both', 'Left', 'Right'] | None = None
    """
    How to choose the best choice in strong branching

    Possible values are:

    * `Both`: Choose the the choice with best combined rating.
    * `Left` (the default): Choose the choice with the best rating of the left branch.
    * `Right`: Choose the choice with the best rating of the right branch.

    """

    fdsInitialRestartLimit: int | None = None
    """
    Fail limit for the first restart

    Failure-directed search is periodically restarted: explored part of the current search tree is turned into a no-good constraint, and the search starts again in the root node.
    This parameter specifies the size of the very first search tree (measured in number of failures).
    """

    fdsRestartStrategy: Literal['Geometric', 'Nested', 'Luby'] | None = None
    """
    Restart strategy to use

    This parameter specifies how the restart limit (maximum number of failures) changes from restart to restart.
    Possible values are:

    * `Geometric` (the default): After each restart, restart limit is multiplied by {@link fdsRestartGrowthFactor}.
    * `Nested`: Similar to `Geometric` but the limit is changed back to {@link fdsInitialRestartLimit} each time a new maximum limit is reached.
    * `Luby`: Luby restart strategy is used. Parameter {@link fdsRestartGrowthFactor} is ignored.
    """

    fdsRestartGrowthFactor: float | None = None
    """
    Growth factor for fail limit after each restart

    After each restart, the fail limit for the restart is multiplied by the specified factor.
    This parameter is ignored when {@link fdsRestartStrategy} is `Luby`.
    """

    fdsMaxCounterAfterRestart: int | None = None
    """
    Truncate choice use counts after a restart to this value

    The idea is that ratings learned in the previous restart are less valid in the new restart.
    Using this parameter, it is possible to truncate use counts on choices so that new local ratings will have bigger weights (when FDSFixedAlpha is not used).
    """

    fdsMaxCounterAfterSolution: int | None = None
    """
    Truncate choice use counts after a solution is found

    Similar to `FDSMaxCounterAfterRestart`, this parameter allows truncating use counts on choices when a solution is found.
    """

    fdsResetRestartsAfterSolution: bool | None = None
    """
    Reset restart size after a solution is found (ignored in Luby)

    When this parameter is set (the default), then restart limit is set back to `FDSInitialRestartLimit` when a solution is found.
    """

    fdsUseNogoods: bool | None = None
    """
    Whether to use or not nogood constraints

    By default, no-good constraint is generated after each restart. This parameter allows to turn no-good constraints off.
    """

    _fdsFreezeRatingsAfterProof: bool | None = None
    _fdsContinueAfterProof: bool | None = None
    _fdsRepeatLimit: int | None = None
    _fdsCompletelyRandom: bool | None = None
    fdsBranchOnObjective: bool | None = None
    """
    Whether to generate choices for objective expression/variable

    This option controls the generation of choices on the objective. It works regardless of the objective is given by an expression or a variable.
    """

    _fdsImproveNogoods: bool | None = None
    fdsBranchOrdering: Literal['FailureFirst', 'FailureLast', 'Random'] | None = None
    """
    Controls which side of a choice is is explored first (considering the rating).

    This option can take the following values:

    * `FailureFirst`: Explore the failure side first.
    * `FailureLast`: Explore the failure side last.
    * `Random`: Explore either side randomly.
    """

    _fdsDiveBySetTimes: bool | None = None
    fdsLBStrategy: Literal['Minimum', 'Random', 'Split'] | None = None
    """
    A strategy to choose objective cuts during FDSLB search.

    Possible values are:

    * `Minimum`: Always change the cut by the minimum amount.
    * `Random`: At each restart, randomly choose a value in range LB..UB. The default.
    * `Split`: Always split the current range LB..UB in half.

    """

    fdsLBResetRatings: bool | None = None
    """
    Whether to reset ratings when a new LB is proved

    When this parameter is on, and FDSLB proves a new lower bound, then all ratings are reset to default values.
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
    """
    Use only the user-provided warm start as the initial solution in LNS

    When this parameter is on, the solver will use only the user-specified warm start solution for the initial solution phase in LNS. If no warm start is provided, the solver will search for its own initial solution as usual.
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
    """
    Which worker computes simple lower bound

    Simple lower bound is a bound such that infeasibility of a better objective can be proved by propagation only (without the search). The given worker computes simple lower bound before it starts the normal search. If a worker with the given number doesn't exist, then the lower bound is not computed.
    """

    simpleLBMaxIterations: int | None = None
    """
    Maximum number of feasibility checks

    Simple lower bound is computed by binary search for the best objective value that is not infeasible by propagation. This parameter limits the maximum number of iterations of the binary search. When the value is 0, then simple lower bound is not computed at all.
    """

    simpleLBShavingRounds: int | None = None
    """
    Number of shaving rounds

    When non-zero, the solver shaves on variable domains to improve the lower bound. This parameter controls the number of shaving rounds.
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
    _pOSAbsentRelated: bool | None = None
    _defaultCallbackBlockSize: int | None = None
    _useReservoirPegging: bool | None = None
    _useTimeNet: bool | None = None
    _timeNetVarsToPreprocess: int | None = None
    _timeNetSubPriorityBits: int | None = None


    pythonStreamBufferSize: int = field(default=2*1024*1024)
    workers: list[WorkerParameters] = field(default_factory=lambda: [])

    def _to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for JSON serialization."""
        result = {f.name: getattr(self, f.name) for f in fields(self) if f.name not in ('workers', 'pythonStreamBufferSize') and getattr(self, f.name) is not None}
        if len(self.workers) > 0:
            result['workers'] = [w._to_dict() for w in self.workers]
        return result

    # TODO: _to_dict can be documented function
    # TODO: A function / constructor from dict can be useful (user can have parameters stored in a JSON file).
    # TODO: A copy function can be useful to create modified copies of existing parameters.
