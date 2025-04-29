import re
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

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
        LOGGER.debug("Flushing all algorithm registrations and dependencies")
        self._algorithms: Dict[str, Algorithm] = {}
        self._dependencies: Dict[str, List[Algorithm]] = {}
        self._dependencyFns: Dict[str, List[AlgorithmFn]] = {}
        self._window_triggers: Dict[str, List[Algorithm]] = {}

    def _add_algorithm(self, name: str, algorithm: Algorithm) -> None:
        if name in self._algorithms:
            LOGGER.error(f"Attempted to register duplicate algorithm: {name}")
            raise ValueError(f"Algorithm {name} already exists")
        LOGGER.info(f"Registering algorithm: {name} (window: {algorithm.window_name}_{algorithm.window_version})")
        self._algorithms[name] = algorithm

    def _add_dependency(self, algorithm: str, dependency: AlgorithmFn) -> None:
        LOGGER.debug(f"Adding dependency for algorithm: {algorithm}")
        dependencyAlgo = None
        for algo in self._algorithms.values():
            if algo.exec_fn == dependency:
                dependencyAlgo = algo
                break
        
        if not dependencyAlgo:
            LOGGER.error(f"Failed to find registered algorithm for dependency: {dependency.__name__}")
            raise ValueError(f"Dependency {dependency.__name__} not found in registered algorithms")

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
        self._max_workers = max_workers

    def ExecuteDagPart(
        self, ExecutionRequest: pb.ExecutionRequest, context
    ) -> pb.ExecutionResult:
        LOGGER.info(f"Received DAG execution request for task: {ExecutionRequest.task_id}")
        try:
            # TODO: Implement actual execution logic
            LOGGER.warning("ExecuteDagPart implementation is a stub - not actually executing anything")
            return pb.ExecutionResult(
                task_id="0", status=pb.ResultStatus.RESULT_STATUS_SUCEEDED
            )
        except Exception as e:
            LOGGER.error(f"DAG execution failed: {str(e)}", exc_info=True)
            raise

    def HealthCheck(
        self, HealthCheckRequest: pb.HealthCheckRequest, context
    ) -> pb.HealthCheckResponse:
        LOGGER.debug("Received health check request")
        return pb.HealthCheckResponse(
            status=pb.HealthCheckResponse(status=pb.HealthCheckResponse.STATUS_SERVING)
        )
    

    def Register(self):
        LOGGER.info(f"Preparing to register processor '{self._name}' with Orca Core")
        LOGGER.debug(f"Building registration request with {len(_algorithmsSingleton._algorithms)} algorithms")
        registration_request = pb.ProcessorRegistration()
        registration_request.name = self._name
        registration_request.runtime = self._runtime
        registration_request.connection_str = f"dns://localhost:{envs.PORT}"

        for _, algorithm in _algorithmsSingleton._algorithms.items():
            LOGGER.debug(f"Adding algorithm to registration: {algorithm.name}_{algorithm.version}")
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
        """Start the gRPC server and wait for termination."""
        try:
            LOGGER.info(f"Starting Orca Processor '{self._name}' with Python {self._runtime}")
            LOGGER.info(f"Initializing gRPC server with {self._max_workers} workers")
            
            server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self._max_workers),
                options=[
                    ('grpc.max_send_message_length', 50 * 1024 * 1024),     # 50MB
                    ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
                ]
            )
            
            # Add our servicer to the server
            service_pb2_grpc.add_OrcaProcessorServicer_to_server(self, server)
            
            # Add the server port
            port = server.add_insecure_port(f"[::]:{envs.PORT}")
            if port == 0:
                raise RuntimeError(f"Failed to bind to port {envs.PORT}")
            
            LOGGER.info(f"Server listening on port {envs.PORT}")
            
            # Start the server
            server.start()
            LOGGER.info("Server started successfully")
            
            # Setup graceful shutdown
            import signal
            def handle_shutdown(signum, frame):
                LOGGER.info("Received shutdown signal, stopping server...")
                server.stop(grace=5)  # 5 seconds grace period
            
            signal.signal(signal.SIGTERM, handle_shutdown)
            signal.signal(signal.SIGINT, handle_shutdown)
            
            # Wait for termination
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
        window_name: str,
        window_version: str,
        depends_on: List[Callable[..., Any]] = [],
    ) -> Callable[[T], T]:
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
                LOGGER.debug(f"Executing algorithm {name}_{version}")
                try:
                    # setup ready for the algo
                    # TODO
                    LOGGER.debug(f"Algorithm {name}_{version} setup complete")

                    # run the algo
                    LOGGER.info(f"Running algorithm {name}_{version}")
                    result = algo(*args, **kwargs)
                    LOGGER.debug(f"Algorithm {name}_{version} execution complete")

                    # tear down
                    # TODO
                    return result
                except Exception as e:
                    LOGGER.error(f"Algorithm {name}_{version} failed: {str(e)}", exc_info=True)
                    raise

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
