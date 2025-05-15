# 🐳 Orca Python SDK

The Orca Python SDK enables developers to define and register Python-based algorithms into the
[Orca](https://www.github.com/Predixus/orca) framework. With built-in gRPC communication, algorithm versioning, and dependency resolution,
this SDK makes it seamless to build scalable, production-grade ML or analytics pipelines on
timeseries data.

## 🚀 Getting Started

Before using this SDK, you must install the Orca CLI and start Orca Core.

1. Install the Orca CLI
   Ensure that Docker is installed on your system.

## Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Predixus/orca/main/install-cli.sh | bash
```

## Windows

Use WSL (Windows Subsystem for Linux) and run the above command inside your WSL shell.

Once installed, follow the instructions in the Orca documentation to start the Orca Core service.

2. Start the Orca Server

```bash
orca start
```

3. Print out the server details

```bash
orca status
```

4. Install the Orca sdk into your python project:

```bash
pip install orca-time
```

## 🧪 Example Usage

Here’s a basic example of using the SDK:

```python
from orca_python import Processor

proc = Processor("ml_v2")

@proc.algorithm("MyAlgo", "1.0.0", "MyWindow", "1.0.0")
def my_algorithm() -> dict:
return {"result": 42}

if __name__ == "__main__":
proc.Register()
proc.Start()
```

Want to build a full dependency DAG? Check out [examples](./examples/) for a multi-layered trading strategy.

## 📚 Full Orca documentation

## 🧠 What This SDK Does

This SDK lets you:

Define algorithms.

Register them with the Orca Core service.

Handle dependencies across algorithms in a DAG.

Receive structured input and emit structured output.

Stream execution results to orca core.

## 🧱 Key Concepts

Processor: A container for algorithms, exposing them to the Orca Core service.

Algorithm: A Python function decorated and registered for DAG execution.

Window: A temporal trigger used to activate algorithms.

## ⚠️ Naming Rules

Algorithm and Window names must be in PascalCase.

Versions must follow semantic versioning (e.g., 1.0.0).

Dependencies must be declared only after their algorithm is registered.

Algorithms cannot depend on others from a different window type (enforced by Orca Core).

## 💡 Advanced Features

Support for float values, numeric arrays, and dictionaries as return types.

Custom struct serialization fallback for complex objects.

Health check endpoint for readiness probes.

Graceful shutdown on signals (SIGINT, SIGTERM).

## 👥 Community

GitHub Issues: https://github.com/predixus/orca-python/issues

Discussions: Coming soon!

## 📄 License

This SDK is part of the Orca ecosystem, but licensed under the MIT License.

See the full license terms (here)[./LICENSE].

Built with ❤️ by Predixus
