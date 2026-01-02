# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]
## [v0.11.0] - 02-01-2026

### Added
- A stubbed out `registry` module within the package that the Orca CLI generates type stubs for.
    This module will contain the algorithms, window types and metadata present within Orca core.
    The LSP that the user uses must be pointed towards the stubs generated from the CLI for this
    to be effective - typically via the `stubs` argument.

## [v0.10.0] - 27-09-2025
- Bumped Orca version

## [v0.9.0] - 27-09-2025

### Changed

- How the processor address is provided to combine address and port, with a robust regex handling of the address.

### Added

- Additional optional env var to register with Orca core a different port to what is exposed internally


## [v0.8.0] - 23-09-2025

### Added

- Integrated support for more robust metadata handling

## [v0.7.14] - 15-09-2025

## [v0.7.12] - 15-09-2025

### Added

- Server reflection

## [v0.7.10] - 10-09-2025

### Fixed

- Updated the orca core version

## [v0.7.8] - 10-09-2025

### Fixed

- Issue in the OrcaCore service name

## [v0.7.7] - 10-09-2025

### Changed

- The version of Orca core to use.

## [v0.7.6] - 10-09-2025

### Fixed

- Fixed gRPC connection to ORCA CORE as SSL instead of insecure, when in production

## [v0.7.5] - 09-09-2025

### Fixed

- Improper exception handling on lack of environment variables, and environment variable name change.

## [v0.7.4] - 29-06-2025

### Fixed

- Return type handling

## [v0.7.3] - 29-06-2025

### Fixed

- `time_from` & `time_to` message copying

## [v0.7.2] - 29-06-2025

### Added

- Usability changes to `ExecutionParams` where window can either be a protobuf or a `Window` class

## [v0.7.1] - 29-06-2025

### Fixed

- `time_from` and `time_to` types in the window definition

## [v0.7.0] - 29-06-2025

### Changed

- Orca core to get latest protobuf definitions

## [v0.6.1] - 26-06-2025

### Added

- None result type

## [v0.6.0] - 26-06-2025

### Added

- Explicit return types to algorithms

## [v0.5.0] - 23-06-2025

### Changed

- Stricter typing to algorithm function definitions

## [v0.4.0] - 23-06-2025

### Changed

- The way algorithms specify how they are triggered, to use a class based `WindowType`

## [v0.3.0] - 23-06-2025

### Added

- Metadata into the window emitter

## [v0.2.0] - 18-05-2025

### Added

- The ability to trigger windows
- A full E2E example of triggering and running algorithms

## [v0.1.0] - 15-05-2025

### Added

- Initial implementation that accepts windows and farms the window off to the relevant processors
- Now handling results properly.
- Properly handled the attaching of the gRPC server.
- Added license.
- Updated documentation to the core components.

### Changed

### Removed

[unreleased]: https://github.com/Predixus/Orca/compare/v0.10.0...HEAD
[v0.10.0]: https://github.com/Predixus/Orca/compare/v0.9.0...v0.10.0
[v0.9.0]: https://github.com/Predixus/Orca/compare/v0.8.0...v0.9.0
[v0.8.0]: https://github.com/Predixus/Orca/compare/v0.7.14...v0.8.0
[v0.7.14]: https://github.com/Predixus/Orca/compare/v0.7.13...v0.7.14
[v0.7.13]: https://github.com/Predixus/Orca/compare/v0.7.12...v0.7.13
[v0.7.12]: https://github.com/Predixus/Orca/compare/v0.7.11...v0.7.12
[v0.7.11]: https://github.com/Predixus/Orca/compare/v0.7.10...v0.7.11
[v0.7.10]: https://github.com/Predixus/Orca/compare/v0.7.9...v0.7.10
[v0.7.9]: https://github.com/Predixus/Orca/compare/v0.7.8...v0.7.9
[v0.7.8]: https://github.com/Predixus/Orca/compare/v0.7.7...v0.7.8
[v0.7.7]: https://github.com/Predixus/Orca/compare/v0.7.6...v0.7.7
[v0.7.6]: https://github.com/Predixus/Orca/compare/v0.7.5...v0.7.6
[v0.7.5]: https://github.com/Predixus/Orca/compare/v0.7.4...v0.7.5
[v0.7.4]: https://github.com/Predixus/Orca/compare/v0.7.3...v0.7.4
[v0.7.3]: https://github.com/Predixus/Orca/compare/v0.7.2...v0.7.3
[v0.7.2]: https://github.com/Predixus/Orca/compare/v0.7.1...v0.7.2
[v0.7.1]: https://github.com/Predixus/Orca/compare/v0.7.0...v0.7.1
[v0.7.0]: https://github.com/Predixus/Orca/compare/v0.6.1...v0.7.0
[v0.6.1]: https://github.com/Predixus/Orca/compare/v0.6.0...v0.6.1
[v0.6.0]: https://github.com/Predixus/Orca/compare/v0.5.0...v0.6.0
[v0.5.0]: https://github.com/Predixus/Orca/compare/v0.4.0...v0.5.0
[v0.4.0]: https://github.com/Predixus/Orca/compare/v0.3.0...v0.4.0
[v0.3.0]: https://github.com/Predixus/Orca/compare/v0.2.0...v0.3.0
[v0.2.0]: https://github.com/Predixus/Orca/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/Predixus/Orca/compare/v0.1.0...v0.1.0
