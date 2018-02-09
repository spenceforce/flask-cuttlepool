# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com)
and this project adheres to [Semantic Versioning](http://semver.org).

## [Unreleased]
### Added
- Convenience method for committing transactions on the connection on the
  application context.

## [0.2.0] - 2018-01-30
### Added
- Import `PoolConnection` for simple, uniform import from `flask_cuttlepool`.
  ([#4](https://github.com/smitchell556/flask-cuttlepool/pull/4))
- Support for multiple Flask applications. Connection pools are created per
  application.
- Decorators for attaching `ping()` and `normalize_connection()` methods to
  connection pools.
- Support for multiple pools per Flask app object.
### Changed
- Upgrade minimum version of `cuttlepool` to 0.6.0.
- Get all configuration options starting with `CUTTLEPOOL_` from `app.config`
  instead of explicitly passing them to `__init__()` or `init_app()`.
### Removed
- Custom exceptions.

## 0.1.0 - 2018-01-15
### Added
- Initial Flask-CuttlePool code.

[Unreleased]: https://github.com/smitchell556/flask-cuttlepool/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/smitchell556/flask-cuttlepool/compare/v0.1.0...v0.2.0
