import re
import sys
import logging
from typing import Any, Dict, List, TypeVar, Callable, TypeAlias
from concurrent import futures
from dataclasses import dataclass

import grpc
import service_pb2 as pb
import service_pb2_grpc

from orca_python import envs
from orca_python.exceptions import InvalidDependency, InvalidAlgorithmArgument

# Regex patterns for validation
ALGORITHM_NAME = r"^[A-Z][a-zA-Z0-9]*$"
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
WINDOW_NAME = r"^[A-Z][a-zA-Z0-9]*$"

AlgorithmFn: TypeAlias = Callable[..., Any]

T = TypeVar("T", bound=AlgorithmFn)

LOGGER = logging.getLogger(__name__)


@dataclass
class Algorithm:
    name: str
    version: str
    window_name: str
    window_version: str
    exec_fn: AlgorithmFn
    processor: str
    runtime: str

    @property
    def full_name(self) -> str:
        return f"{self.name}_{self.version}"

    @property
    def full_window_name(self) -> str:
        return f"{self.window_name}_{self.window_version}"


class Algorithms:
    def __init__(self) -> None:
        self._flush()

    def _flush(self) -> None:
        self._algorithms: Dict[str, Algorithm] = {}
        self._dependencies: Dict[str, List[Algorithm]] = {}
        self._dependencyFns: Dict[str, List[AlgorithmFn]] = {}
        self._window_triggers: Dict[str, List[Algorithm]] = {}

    def _add_algorithm(self, name: str, algorithm: Algorithm) -> None:
        if name in self._algorithms:
            raise ValueError(f"Algorithm {name} already exists")
        self._algorithms[name] = algorithm

    def _add_dependency(self, algorithm: str, dependency: AlgorithmFn) -> None:
        for algo in self._algorithms.values():
            if algo.exec_fn == dependency:
                dependencyAlgo = algo
                break

        if algorithm not in self._dependencyFns:
            self._dependencyFns[algorithm] = [dependency]
            self._dependencies[algorithm] = [dependencyAlgo]
        else:
            self._dependencyFns[algorithm].append(dependency)
            self._dependencies[algorithm].append(dependencyAlgo)

    def _add_window_trigger(self, window: str, algorithm: Algorithm) -> None:
        if window not in self._window_triggers:
            self._window_triggers[window] = [algorithm]
        else:
            self._window_triggers[window].append(algorithm)

    def _has_algorithm_fn(self, algorithm_fn: AlgorithmFn) -> bool:
        for algorithm in self._algorithms.values():
            if algorithm.exec_fn == algorithm_fn:
                return True
        return False


# stores all the algorithms
_algorithmsSingleton = Algorithms()


# the orca processor
class Processor(service_pb2_grpc.OrcaProcessorServicer):
    def __init__(self, name: str, max_workers: int = 10):
        super().__init__()
        self._name = name
        self._connstr = f"localhost:{envs.PORT}"
        self._runtime = sys.version

    def ExecuteDagPart(
        self, ExecutionRequest: pb.ExecutionRequest, context
    ) -> pb.ExecutionResult:
        return pb.ExecutionResult(
            task_id="0", status=pb.ResultStatus.RESULT_STATUS_SUCEEDED
        )

    def HealthCheck(
        self, HealthCheckRequest: pb.HealthCheckRequest, context
    ) -> pb.HealthCheckResponse:
        return pb.HealthCheckResponse(
            status=pb.HealthCheckResponse(status=pb.HealthCheckResponse.STATUS_SERVING)
        )
    

    def Register(self):
        registration_request = pb.ProcessorRegistration()
        registration_request.name = self._name
        registration_request.runtime = self._runtime
        registration_request.connection_str = f"dns://localhost:{envs.PORT}"

        for _, algorithm in _algorithmsSingleton._algorithms.items():
            algo_msg = registration_request.supported_algorithms.add()
            algo_msg.name = algorithm.name
            algo_msg.version = algorithm.version
            
            # Add window type
            algo_msg.window_type.name = algorithm.window_name
            algo_msg.window_type.version = algorithm.window_version

            # Add dependencies if they exist
            if algorithm.full_name in _algorithmsSingleton._dependencies:
                for dep in _algorithmsSingleton._dependencies[algorithm.full_name]:
                    dep_msg = algo_msg.dependencies.add()
                    dep_msg.name = dep.name
                    dep_msg.version = dep.version
                    dep_msg.processor_name = dep.processor
                    dep_msg.processor_runtime = dep.runtime

        with grpc.insecure_channel(envs.ORCASERVER) as channel:
            stub = service_pb2_grpc.OrcaCoreStub(channel)
            response = stub.RegisterProcessor(registration_request)
            LOGGER.info(f"Algorithm registration response recieved: {response}")

    def Start(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        service_pb2_grpc.add_OrcaProcessorServicer_to_server(Processor(), server)
        server.add_insecure_port("[::]:" + envs.PORT)
        server.start()
        server.wait_for_termination()

    def algorithm(
        self,
        name: str,
        version: str,
        window_name: str,
        window_version: str,
        depends_on: List[Callable[..., Any]] = [],
    ) -> Callable[[Algorithm], Any]:
        """
        Register a function as an Orca Algorithm

        Args:
            name: Name of the algorithm
            version: The algorithm version
            window_trigger: The window that triggers the Algorithm or DAG
            window_version: The version of the triggering window
            depends_on: List of algorithms whose results the algorithm depends on

        Returns:
            Wrapper around the algorithm.

        Raises:
            ValueError:
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

        if not re.match(WINDOW_NAME, window_name):
            raise InvalidAlgorithmArgument(
                f"Window name '{window_name}' must be in PascalCase"
            )

        if not re.match(SEMVER_PATTERN, window_version):
            raise InvalidAlgorithmArgument(
                f"Window version '{window_version}' must follow basic semantic "
                "versioning (e.g., '1.0.0') without release portions"
            )

        def inner(algo: T) -> T:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # setup ready for the algo
                # TODO

                # run the algo
                result = algo(*args, **kwargs)

                # tear down
                # TODO
                return result

            algorithm = Algorithm(
                name=name,
                version=version,
                window_name=window_name,
                window_version=window_version,
                exec_fn=wrapper,
                processor=self._name,
                runtime=sys.version
            )

            _algorithmsSingleton._add_algorithm(algorithm.full_name, algorithm)
            _algorithmsSingleton._add_window_trigger(algorithm.full_window_name, algorithm)

            for dependency in depends_on:
                if not _algorithmsSingleton._has_algorithm_fn(dependency):
                    message = (
                        f"Cannot add function `{dependency.__name__}` to dependency stack. All dependencies must "
                        "be decorated with `@algorithm` before they can be used as dependencies."
                    )
                    raise InvalidDependency(message)
                _algorithmsSingleton._add_dependency(algorithm.full_name, dependency)

            # TODO: check for circular dependencies. It's not easy to create one in python as the function
            # needs to be defined before a dependency can be created, and you can only register depencenies
            # once. But when dependencies are grabbed from a server, circular dependencies will be possible

            return wrapper  # type: ignore

        return inner
