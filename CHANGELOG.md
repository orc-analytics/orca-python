# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v0.7.4] - 29-06-2025

## Fixed

- Return type handling

## [v0.7.3] - 29-06-2025

## Fixed

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

[unreleased]: https://github.com/Predixus/Orca/compare/v0.7.4...HEAD
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
