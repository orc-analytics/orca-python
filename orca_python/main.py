"""
Orca Python SDK

This SDK provides the `Processor` class, which integrates with the Orca gRPC service
to register, execute, and manage algorithms defined in Python. Algorithms can have dependencies
which are managed by Orca-core.
"""

import re
import sys
import asyncio
import logging
import datetime as dt
import traceback

from google.protobuf import json_format, timestamp_pb2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

import time
import types
import typing
from typing import (
    Any,
    Dict,
    List,
    Union,
    TypeVar,
    Callable,
    Iterable,
    Optional,
    Protocol,
    Generator,
    AsyncGenerator,
)
from inspect import signature
from concurrent import futures
from dataclasses import field, dataclass

import grpc
import service_pb2 as pb
import service_pb2_grpc
import google.protobuf.struct_pb2 as struct_pb2
from google.protobuf import json_format
from service_pb2_grpc import OrcaProcessorServicer

from orca_python import envs
from orca_python.exceptions import (
    InvalidDependency,
    InvalidWindowArgument,
    InvalidAlgorithmArgument,
    InvalidAlgorithmReturnType,
)

# Regex patterns for validation
ALGORITHM_NAME = r"^[A-Z][a-zA-Z0-9]*$"
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
WINDOW_NAME = r"^[A-Z][a-zA-Z0-9]*$"


LOGGER = logging.getLogger(__name__)


@dataclass
class WindowType:
    name: str
    version: str
    description: str

    def __post__init__(self) -> None:
        if not re.match(WINDOW_NAME, self.name):
            raise InvalidAlgorithmArgument(
                f"Window name '{self.name}' must be in PascalCase"
            )

        if not re.match(SEMVER_PATTERN, self.version):
            raise InvalidAlgorithmArgument(
                f"Window version '{self.version}' must follow basic semantic "
                "versioning (e.g., '1.0.0') without release portions"
            )


@dataclass
class StructResult:
    value: Dict[str, Any]

    def __init__(self, value: Dict[str, Any]) -> None:
        """
        Produce a struct/dictionary based result

        Args:
            value: The result to produce. e.g.: {'min': -1.1, 'median': 4.2, 'max': 5.0}
        """
        self.value = value


@dataclass
class ValueResult:
    value: float | int | bool

    def __init__(self, value: float | int | bool) -> None:
        """
        Produce a value result

        Args:
            value: The result to produce. E.g. 1.0
        """
        self.value = value


@dataclass
class ArrayResult:
    value: Iterable[float | int | bool]

    def __init__(self, value: Iterable[float | int | bool]) -> None:
        """
        Produce an array result

        Args:
            value: The result to produce. E.g. [1, 2, 3, 4, 5]
        """
        self.value = value


class NoneResult:
    """
    The `None` result type
    """

    value: None = None


returnResult = StructResult | ArrayResult | ValueResult | NoneResult


@dataclass
class Window:
    time_from: dt.datetime
    time_to: dt.datetime
    name: str
    version: str
    origin: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionParams:
    window: Window
    dependencies: Optional[Iterable[pb.AlgorithmResult]] = None

    def __init__(
        self,
        window: Window | pb.Window,
        dependencies: Optional[Iterable[pb.AlgorithmResult]] = None,
    ):
        if isinstance(window, Window):
            self.window = window
        elif isinstance(window, pb.Window):
            self.window = Window(
                time_from=window.time_from.ToDatetime(),
                time_to=window.time_to.ToDatetime(),
                name=window.window_type_name,
                version=window.window_type_version,
                origin=window.origin,
                metadata=json_format.MessageToDict(window.metadata),
            )
        else:
            raise InvalidWindowArgument(f"window of type {type(window)} not handled")
        self.dependencies = dependencies


class AlgorithmFn(Protocol):
    def __call__(
        self, params: ExecutionParams, *args: Any, **kwargs: Any
    ) -> returnResult: ...


T = TypeVar("T", bound=AlgorithmFn)


def EmitWindow(window: Window) -> None:
    """
    Emits a window to Orca-core.

    Raises:
        grpc.RpcError: If the emit fails.
    """
    LOGGER.info(f"Emitting window: {window}")

    _time_from = timestamp_pb2.Timestamp()
    _time_from.FromDatetime(window.time_from)

    _time_to = timestamp_pb2.Timestamp()
    _time_to.FromDatetime(window.time_to)

    window_pb = pb.Window()
    window_pb.time_to.CopyFrom(_time_to)
    window_pb.time_from.CopyFrom(_time_from)
    window_pb.window_type_name = window.name
    window_pb.window_type_version = window.version
    window_pb.origin = window.origin

    # parse out the metadata
    struct_value = struct_pb2.Struct()
    json_format.ParseDict(window.metadata, struct_value)
    window_pb.metadata = struct_value

    if envs.is_production:
        # secure channel with TLS
        with grpc.secure_channel(
            envs.ORCASERVER, grpc.ssl_channel_credentials()
        ) as channel:
            stub = service_pb2_grpc.OrcaCoreStub(channel)
            response = stub.EmitWindow(window_pb)
            LOGGER.info(f"Window emitted: {response}")
    else:
        # insecure channel for local development
        with grpc.insecure_channel(envs.ORCASERVER) as channel:
            stub = service_pb2_grpc.OrcaCoreStub(channel)
            response = stub.EmitWindow(window_pb)
            LOGGER.info(f"Window emitted: {response}")


@dataclass
class Algorithm:
    """
    Represents a registered algorithm with metadata and execution logic.

    Attributes:
        name (str): The name of the algorithm (PascalCase).
        version (str): Semantic version of the algorithm (e.g., "1.0.0").
        window_name (str): The window type name that triggers the algorithm.
        window_version (str): The version of the window type.
        exec_fn (AlgorithmFn): The execution function for the algorithm.
        processor (str): Name of the processor where it's registered.
        runtime (str): Python runtime used for execution.
    """

    name: str
    version: str
    window_name: str
    window_version: str
    window_description: str
    exec_fn: AlgorithmFn
    processor: str
    runtime: str
    result_type: returnResult

    @property
    def full_name(self) -> str:
        """Returns the full name as `name_version`."""
        return f"{self.name}_{self.version}"

    @property
    def full_window_name(self) -> str:
        """Returns the full window name as `window_name_window_version`."""
        return f"{self.window_name}_{self.window_version}"


class Algorithms:
    """
    Internal singleton managing all registered algorithms and their dependencies.
    """

    def __init__(self) -> None:
        self._flush()

    def _flush(self) -> None:
        """Clears all registered algorithms and dependencies."""
        LOGGER.debug("Flushing all algorithm registrations and dependencies")
        self._algorithms: Dict[str, Algorithm] = {}
        self._dependencies: Dict[str, List[Algorithm]] = {}
        self._dependencyFns: Dict[str, List[AlgorithmFn]] = {}
        self._window_triggers: Dict[str, List[Algorithm]] = {}

    def _add_algorithm(self, name: str, algorithm: Algorithm) -> None:
        """
        Registers a new algorithm.

        Args:
            name (str): Fully qualified algorithm name.
            algorithm (Algorithm): Algorithm metadata and logic.

        Raises:
            ValueError: If the algorithm name is already registered.
        """
        if name in self._algorithms:
            LOGGER.error(f"Attempted to register duplicate algorithm: {name}")
            raise ValueError(f"Algorithm {name} already exists")
        LOGGER.info(
            f"Registering algorithm: {name} (window: {algorithm.window_name}_{algorithm.window_version})"
        )
        self._algorithms[name] = algorithm

    def _add_dependency(self, algorithm: str, dependency: AlgorithmFn) -> None:
        """
        Adds a dependency to an algorithm.

        Args:
            algorithm (str): Target algorithm's full name.
            dependency (AlgorithmFn): Dependency function already registered.

        Raises:
            ValueError: If the dependency function is not registered.
        """
        LOGGER.debug(f"Adding dependency for algorithm: {algorithm}")
        dependencyAlgo = None
        for algo in self._algorithms.values():
            if algo.exec_fn == dependency:
                dependencyAlgo = algo
                break

        if not dependencyAlgo:
            dep_name = getattr(dependency, "__name__", "<unknown>")
            LOGGER.error(
                f"Failed to find registered algorithm for dependency: {dep_name}"
            )
            raise ValueError(f"Dependency {dep_name} not found in reg=ms")

        if algorithm not in self._dependencyFns:
            self._dependencyFns[algorithm] = [dependency]
            self._dependencies[algorithm] = [dependencyAlgo]
        else:
            self._dependencyFns[algorithm].append(dependency)
            self._dependencies[algorithm].append(dependencyAlgo)

    def _add_window_trigger(self, window: str, algorithm: Algorithm) -> None:
        """Associates an algorithm with a triggering window."""
        if window not in self._window_triggers:
            self._window_triggers[window] = [algorithm]
        else:
            self._window_triggers[window].append(algorithm)

    def _has_algorithm_fn(self, algorithm_fn: AlgorithmFn) -> bool:
        """
        Checks if a function is registered as an algorithm.

        Args:
            algorithm_fn (AlgorithmFn): The function to check.

        Returns:
            bool: True if the function is registered.
        """
        for algorithm in self._algorithms.values():
            if algorithm.exec_fn == algorithm_fn:
                return True
        return False


# the orca processor
class Processor(OrcaProcessorServicer):  # type: ignore
    """
    Orca gRPC Processor for algorithm registration and execution.

    This class implements the gRPC `OrcaProcessor` interface and handles
    the execution lifecycle of user-defined algorithms.

    Args:
        name (str): Unique name of the processor.
        max_workers (int): Max worker threads for execution (default: 10).
    """

    def __init__(self, name: str, max_workers: int = 10):
        super().__init__()
        self._name = name
        self._processorConnStr = (
            f"0.0.0.0:{envs.PORT}"  # attach the processor to all network interfaces.
        )
        self._orcaProcessorConnStr = f"{envs.HOST}:{envs.PORT}"  # tell orca-core to reference this processor by this address.
        self._runtime = sys.version
        self._max_workers = max_workers
        self._algorithmsSingleton: Algorithms = Algorithms()

    async def execute_algorithm(
        self,
        exec_id: str,
        algorithm: pb.Algorithm,
        params: ExecutionParams,
    ) -> pb.ExecutionResult:
        """
        Executes a single algorithm with resolved dependencies.

        Args:
            exec_id (str): Unique execution ID.
            algorithm (pb.Algorithm): The algorithm to execute.
            params (ExecutionParams): The execution params object, which contains the triggering window and dependency results.

        Returns:
            pb.ExecutionResult: The result of the execution.

        Raises:
            Exception: On algorithm execution or serialization error.
        """
        try:
            LOGGER.debug(f"Processing algorithm: {algorithm.name}_{algorithm.version}")
            algoName = f"{algorithm.name}_{algorithm.version}"
            algo = self._algorithmsSingleton._algorithms[algoName]

            # convert dependency results into a dict of name -> value
            dependency_values = {}
            if params.dependencies:
                for dep_result in params.dependencies:
                    # extract value based on which oneof field is set
                    dep_value = None
                    if dep_result.result.HasField("single_value"):
                        dep_value = dep_result.result.single_value
                    elif dep_result.result.HasField("float_values"):
                        dep_value = list(dep_result.result.float_values.values)
                    elif dep_result.result.HasField("struct_value"):
                        dep_value = json_format.MessageToDict(
                            dep_result.result.struct_value
                        )

                    dep_name = (
                        f"{dep_result.algorithm.name}_{dep_result.algorithm.version}"
                    )
                    dependency_values[dep_name] = dep_value

            # execute in thread pool since algo.exec_fn is synchronous
            loop = asyncio.get_event_loop()

            algoResult = await loop.run_in_executor(None, algo.exec_fn, params)

            # depending on algo result type, map to whatever instance
            if algo.result_type == StructResult:  # type: ignore
                struct_value = struct_pb2.Struct()
                json_format.ParseDict(algoResult.value, struct_value)

                resultPb = pb.Result(
                    status=pb.ResultStatus.RESULT_STATUS_SUCEEDED,
                    struct_value=struct_value,
                )

            elif algo.result_type == ValueResult:  # type: ignore
                # for single numeric values
                resultPb = pb.Result(
                    status=pb.ResultStatus.RESULT_STATUS_SUCEEDED,
                    single_value=algoResult.value,
                )
            elif algo.result_type == ArrayResult:  # type: ignore
                # for lists of numeric values
                float_array = pb.FloatArray(values=algoResult)
                resultPb = pb.Result(
                    status=pb.ResultStatus.RESULT_STATUS_SUCEEDED,
                    float_values=float_array.values,
                )
            else:
                LOGGER.error(
                    f"Algorithm {algo.name} {algo.version} has unhandled return type {algo.result_type}"
                )
                # create a handled failure result
                resultPb = pb.Result(
                    status=pb.ResultStatus.RESULT_STATUS_HANDLED_FAILED,
                )

            # create the algorithm result
            algoResultPb = pb.AlgorithmResult(
                algorithm=algorithm,  # Use the original algorithm object
                result=resultPb,
            )

            # create the execution result
            exec_result = pb.ExecutionResult(
                exec_id=exec_id, algorithm_result=algoResultPb
            )

            LOGGER.info(f"Completed algorithm: {algorithm.name}")
            return exec_result

        except Exception as algo_error:
            LOGGER.error(
                f"Algorithm {algorithm.name} failed: {str(algo_error)}",
                exc_info=True,
            )

            # create a failure result
            current_time = int(time.time())

            # create an error struct value with details
            error_struct = struct_pb2.Struct()
            json_format.ParseDict(
                {"error": str(algo_error), "stack_trace": traceback.format_exc()},
                error_struct,
            )

            # create the result with unhandled failed status and error info
            error_result = pb.Result(
                status=pb.ResultStatus.RESULT_STATUS_UNHANDLED_FAILED,
                struct_value=error_struct,
                timestamp=current_time,
            )

            # create the algorithm result
            algo_result = pb.AlgorithmResult(algorithm=algorithm, result=error_result)

            # create the execution result
            return pb.ExecutionResult(exec_id=exec_id, algorithm_result=algo_result)

    def ExecuteDagPart(
        self, executionRequest: pb.ExecutionRequest, context: grpc.ServicerContext
    ) -> Generator[pb.ExecutionResult, None, None]:
        """
        Executes part of a DAG (Directed Acyclic Graph) of algorithms.

        Args:
            executionRequest (pb.ExecutionRequest): The DAG execution request.
            context (grpc.ServicerContext): gRPC context for the request.

        Yields:
            pb.ExecutionResult: Execution results streamed as they complete.

        Raises:
            grpc.RpcError: If execution fails and an internal error must be raised.
        """

        LOGGER.info(
            (
                f"Received DAG execution request with {len(executionRequest.algorithms)} "
                f"algorithms and ExecId: {executionRequest.exec_id}"
            )
        )

        try:
            # create an event loop if it doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # create tasks for all algorithms
            tasks = [
                self.execute_algorithm(
                    executionRequest.exec_id,
                    algorithm,
                    ExecutionParams(
                        window=executionRequest.window,
                        dependencies=executionRequest.algorithm_results,
                    ),
                )
                for algorithm in executionRequest.algorithms
            ]

            # execute all tasks concurrently and yield results as they complete
            async def process_results() -> AsyncGenerator[pb.ExecutionResult, None]:
                for completed_task in asyncio.as_completed(tasks):
                    result = await completed_task
                    yield result

            # run async generator in the event loop
            async_gen = process_results()
            while True:
                try:
                    result = loop.run_until_complete(async_gen.__anext__())
                    yield result
                except StopAsyncIteration:
                    break

        # capture exceptions
        except Exception as e:
            LOGGER.error(f"DAG execution failed: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"DAG execution failed: {str(e)}")
            raise

        except Exception as e:
            LOGGER.error(f"DAG execution failed: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"DAG execution failed: {str(e)}")
            raise

    def HealthCheck(
        self, HealthCheckRequest: pb.HealthCheckRequest, context: grpc.ServicerContext
    ) -> pb.HealthCheckResponse:
        """
        Returns health status for the processor.

        Args:
            HealthCheckRequest (pb.HealthCheckRequest): Incoming request.
            context (grpc.ServicerContext): gRPC context.

        Returns:
            pb.HealthCheckResponse: Health status and optional metrics.
        """

        LOGGER.debug("Received health check request")
        return pb.HealthCheckResponse(
            status=pb.HealthCheckResponse.STATUS_SERVING,
            message="Processor is healthy",
            metrics=pb.ProcessorMetrics(
                active_tasks=0, memory_bytes=0, cpu_percent=0.0, uptime_seconds=0
            ),
        )

    def Register(self) -> None:
        """
        Registers all supported algorithms with the Orca Core service.

        Raises:
            grpc.RpcError: If registration fails.
        """
        LOGGER.info(f"Preparing to register processor '{self._name}' with Orca Core")
        LOGGER.debug(
            f"Building registration request with {len(self._algorithmsSingleton._algorithms)} algorithms"
        )
        registration_request = pb.ProcessorRegistration()
        registration_request.name = self._name
        registration_request.runtime = self._runtime
        registration_request.connection_str = self._orcaProcessorConnStr

        for _, algorithm in self._algorithmsSingleton._algorithms.items():
            LOGGER.debug(
                f"Adding algorithm to registration: {algorithm.name}_{algorithm.version}"
            )
            algo_msg = registration_request.supported_algorithms.add()
            algo_msg.name = algorithm.name
            algo_msg.version = algorithm.version

            # manage the return type of the algorithm
            if algorithm.result_type == ValueResult:  # type: ignore
                result_type_pb = pb.ResultType.VALUE
            elif algorithm.result_type == StructResult:  # type: ignore
                result_type_pb = pb.ResultType.STRUCT
            elif algorithm.result_type == ArrayResult:  # type: ignore
                result_type_pb = pb.ResultType.ARRAY
            elif algorithm.result_type == NoneResult:  # type: ignore
                result_type_pb = pb.ResultType.NONE
            else:
                raise InvalidAlgorithmReturnType(
                    f"Algorithm has return type {algorithm.result_type}, but expected one of `StructResult`, `ValueResult`, `ArrayResult`, `NoneResult`"
                )

            ## add the result type
            algo_msg.result_type = result_type_pb

            # Add window type
            algo_msg.window_type.name = algorithm.window_name
            algo_msg.window_type.version = algorithm.window_version
            algo_msg.window_type.description = algorithm.window_description

            # Add dependencies if they exist
            if algorithm.full_name in self._algorithmsSingleton._dependencies:
                for dep in self._algorithmsSingleton._dependencies[algorithm.full_name]:
                    dep_msg = algo_msg.dependencies.add()
                    dep_msg.name = dep.name
                    dep_msg.version = dep.version
                    dep_msg.processor_name = dep.processor
                    dep_msg.processor_runtime = dep.runtime

        if envs.is_production:
            # secure channel with TLS
            with grpc.secure_channel(
                envs.ORCASERVER, grpc.ssl_channel_credentials()
            ) as channel:
                stub = service_pb2_grpc.OrcaCoreStub(channel)
                response = stub.RegisterProcessor(registration_request)
                LOGGER.info(f"Algorithm registration response received: {response}")
        else:
            # insecure channel for local development
            with grpc.insecure_channel(envs.ORCASERVER) as channel:
                stub = service_pb2_grpc.OrcaCoreStub(channel)
                response = stub.RegisterProcessor(registration_request)
                LOGGER.info(f"Algorithm registration response received: {response}")

    def Start(self) -> None:
        """
        Starts the gRPC server and begins serving algorithm requests.

        This includes signal handling for graceful shutdown.

        Raises:
            Exception: On server startup failure.
        """
        try:
            LOGGER.info(
                f"Starting Orca Processor '{self._name}' with Python {self._runtime}"
            )
            LOGGER.info(f"Initialising gRPC server with {self._max_workers} workers")

            server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self._max_workers),
                options=[
                    ("grpc.max_send_message_length", 50 * 1024 * 1024),  # 50MB
                    ("grpc.max_receive_message_length", 50 * 1024 * 1024),  # 50MB
                ],
            )

            # add our servicer to the server
            service_pb2_grpc.add_OrcaProcessorServicer_to_server(self, server)

            # add the server port
            port = server.add_insecure_port(self._processorConnStr)
            if port == 0:
                raise RuntimeError(f"Failed to bind to port {envs.PORT}")

            LOGGER.info(f"Server listening on address {self._processorConnStr}")

            # start the server
            server.start()
            LOGGER.info("Server started successfully")

            # setup graceful shutdown
            import signal

            def handle_shutdown(signum: int, frame: Any) -> None:
                LOGGER.info("Received shutdown signal, stopping server...")
                server.stop(grace=5)  # 5 seconds grace period

            signal.signal(signal.SIGTERM, handle_shutdown)
            signal.signal(signal.SIGINT, handle_shutdown)

            # wait for termination
            LOGGER.info("Server is ready for requests")
            server.wait_for_termination()

        except Exception as e:
            LOGGER.error(f"Failed to start server: {str(e)}", exc_info=True)
            raise
        finally:
            LOGGER.info("Server shutdown complete")

    def algorithm(
        self,
        name: str,
        version: str,
        window_type: WindowType,
        depends_on: List[Callable[..., Any]] = [],
    ) -> Callable[[T], T]:
        """
        Decorator for registering a function as an Orca algorithm.

        Args:
            name (str): Algorithm name (PascalCase).
            version (str): Semantic version (e.g., "1.0.0").
            window_type (WindowType): Triggering window type
            depends_on (List[Callable]): List of dependent algorithm functions.
        Returns:
            Callable[[T], T]: The decorated function.

        Raises:
            InvalidAlgorithmArgument: If naming or version format is incorrect.
            InvalidDependency: If any dependency is unregistered.
        """
        if not re.match(ALGORITHM_NAME, name):
            raise InvalidAlgorithmArgument(
                f"Algorithm name '{name}' must be in PascalCase"
            )

        if not re.match(SEMVER_PATTERN, version):
            raise InvalidAlgorithmArgument(
                f"Version '{version}' must follow basic semantic "
                "versioning (e.g., '1.0.0') without release portions"
            )

        def inner(algo: T) -> T:
            def wrapper(
                params: ExecutionParams,
                *args: Any,
                **kwargs: Any,
            ) -> returnResult:
                LOGGER.debug(f"Executing algorithm {name}_{version}")
                try:
                    # setup ready for the algo
                    # pack the params into the kwargs - user can decide if they want it
                    kwargs["params"] = params
                    LOGGER.debug(f"Algorithm {name}_{version} setup complete")

                    # run the algo
                    LOGGER.info(f"Running algorithm {name}_{version}")
                    result = algo(*args, **kwargs)
                    LOGGER.debug(f"Algorithm {name}_{version} execution complete")

                    # tear down
                    # TODO
                    return result
                except Exception as e:
                    LOGGER.error(
                        f"Algorithm {name}_{version} failed: {str(e)}", exc_info=True
                    )
                    raise

            sig = signature(algo)
            returnType = sig.return_annotation
            if not is_type_in_union(returnType, returnResult):  # type: ignore
                raise InvalidAlgorithmReturnType(
                    f"Algorithm has return type {sig.return_annotation}, but expected one of `StructResult`, `ValueResult`, `ArrayResult`, `NoneResult`"
                )

            algorithm = Algorithm(
                name=name,
                version=version,
                window_name=window_type.name,
                window_version=window_type.version,
                window_description=window_type.description,
                exec_fn=wrapper,
                processor=self._name,
                runtime=sys.version,
                result_type=returnType,
            )

            self._algorithmsSingleton._add_algorithm(algorithm.full_name, algorithm)
            self._algorithmsSingleton._add_window_trigger(
                algorithm.full_window_name, algorithm
            )

            for dependency in depends_on:
                if not self._algorithmsSingleton._has_algorithm_fn(dependency):
                    message = (
                        f"Cannot add function `{dependency.__name__}` to dependency stack. All dependencies must "
                        "be decorated with `@algorithm` before they can be used as dependencies."
                    )
                    raise InvalidDependency(message)
                self._algorithmsSingleton._add_dependency(
                    algorithm.full_name, dependency
                )

            # TODO: check for circular dependencies. It's not easy to create one in python as the function
            # needs to be defined before a dependency can be created, and you can only register depencenies
            # once. But when dependencies are grabbed from a server, circular dependencies will be possible

            return wrapper  # type: ignore[return-value]

        return inner


def is_type_in_union(target_type, union_type):  # type: ignore
    """
    Check if target_type is contained within union_type.
    Works with both new syntax (int | float) and typing.Union.
    """
    try:
        # handle new union syntax (Python 3.10+) - types.UnionType
        if isinstance(union_type, types.UnionType):
            return target_type in union_type.__args__

        # handle typing.Union syntax
        origin = getattr(typing, "get_origin", lambda x: None)(union_type)
        if origin is Union:
            args = getattr(typing, "get_args", lambda x: ())(union_type)
            return target_type in args

        # handle single type (not a union)
        return target_type == union_type

    except (AttributeError, TypeError):
        return False
