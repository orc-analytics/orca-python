# 🐳 Orca Python SDK

The Orca Python SDK enables developers to define and register Python-based algorithms into the
[Orca](https://www.github.com/Predixus/orca) framework.

Orca exists to make it seamless to build scalable, production-grade ML or analytics pipelines on
timeseries data.

## 🚀 Getting Started

Before using this SDK, you should install the Orca CLI and start Orca Core.

1. Install the Orca CLI
   Ensure that Docker is installed on your system.

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/Predixus/orca/main/install-cli.sh | bash
```

**Windows**

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

5. Start building out your algorithms

Write a file defining your algorithms and what windows trigger them:

```python
# main.py
from orca_python import Processor

proc = Processor("ml")

@proc.algorithm("MyAlgo", "1.0.0", "MyWindow", "1.0.0")
def my_algorithm() -> dict:
return {"result": 42}

if __name__ == "__main__":
proc.Register()
proc.Start()
```

Then run your python file to register it with orca-core:

```bash
 ORCASERVER=grpc://localhost:32770 HOST=172.18.0.1 python main.py
```

Replace the contents of `ORCASERVER` and `HOST` with the output of `orca status`.

6. Emit a window to orcacore
   TBD

Check out more examples [here](./examples/).

## 🧱 Key Concepts

Processor: A container for algorithms, exposing them to the Orca Core service.

Algorithm: A Python function decorated and registered for DAG execution.

Window: A temporal trigger used to activate algorithms.

## ⚠️ Naming Rules

Algorithm and Window names must be in PascalCase.

Versions must follow semantic versioning (e.g., 1.0.0).

Dependencies must be declared only after their algorithm is registered.

Algorithms cannot depend on others from a different window type (enforced by Orca Core).

## 👥 Community

GitHub Issues: https://github.com/predixus/orca-python/issues

Discussions: Coming soon!

## 📄 License

This SDK is part of the Orca ecosystem, but licensed under the MIT License.

See the full license terms (here)[./LICENSE].

Built with ❤️ by Predixus
