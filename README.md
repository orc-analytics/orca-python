# 🐳 Orca Python SDK

The Orca Python SDK enables developers to define and register Python-based algorithms into the
[Orca](https://www.github.com/orc-analytics/orca) framework.

Orca exists to make it seamless to build scalable, production-grade ML or analytics pipelines on
timeseries data.

## 🚀 Getting Started

Before using this SDK, you should install the Orca CLI and start Orca Core.

1. Install the Orca CLI
   Ensure that Docker is installed on your system.

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/orc-analytics/orca/main/install-cli.sh | bash
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
pip install orca-python
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
 ORCA_CORE=grpc://localhost:32770 PROCESSOR_ADDRESS=172.18.0.1:8080 python main.py
```

Replace the contents of `ORCA_CORE` and `PROCESSOR_ADDRESS` with the output of `orca status`.

6. Emit a window to orcacore

Check out more examples [here](./examples/).

7. Sync local registry of algorithms to Orca Core

When building algorithms that depend on the result of algorithms in other proccessors it's neccessary to reference these algorithms as python objects in the `depends_on` argument of the `algorithm` decorator function.

To do this, sync your python project with Orca Core:

```bash
orca sync
```

Run this command at the root level of your python project. This will generate a `.orca` folder that contains type stubs for the algorithms stored in other processors.

Then, configure the settings of your language server and/or linter to include these type stubs. E.g. for pyright, you would include these settings in your `pyrightconfig.json` file at the root of your python project:
```json
{
  "stubPath": ".orca",
}
```
Now, when importing modules from `orca_python.registry.algorithms` you will see algorithms configured by remote processors.

For example:
```python
from orca_python.registry.algorithms import <my_remote_algorithm>
```

This stubbed algorithm can be used as an algorithm in the `depends_on` argument of the `algorithm` decorator function.

```python
from orca_python import Processor
from orca_python.registry.window_types import every_30_seconds
from orca_python.registry.algorithms import my_remote_algorithm

proc = Processor("ml")

@proc.algorithm(
    "MyAlgo",
    "1.0.0",
    every_30_seconds,
    depends_on=[my_remote_algorithm]
)
def my_algorithm(params: ExecutionParams) -> StructResult:
    ...
```

## Configuration 

Some configuration is required to register a process then start accepting processing requests. If using the internal orca stack for development (via `orca start`), then simply initialise the repository with an `orca.json` file:

```bash
orca init
```

You can additionally provide these environment variables to override, or set, certain configurations:

- `ORCA_CORE` - the address to reach the Orca-core service
- `PROCESSOR_ADDRESS` - the address needed by Orca-core to reach the processor, of format `<address>:<port>`
- `PROCESSOR_EXTERNAL_PORT` - an optional alternative port that should be used by Orca-core to contact the processor. Useful in scenarios like deploying the processor behind a managed service.
- `ENV` - when set to `production` the processor will serve using TLS

## 🧱 Key Concepts

Checkout the Orca [docs](https://orc-a.io/docs) for info on how Orca works.

## 👥 Community

GitHub Issues: https://github.com/orc-analytics/orca-python/issues

Discussions: Coming soon!

## 📄 License

This SDK is part of the Orca ecosystem, but licensed under the MIT License.

See the full license terms (here)[./LICENSE].
