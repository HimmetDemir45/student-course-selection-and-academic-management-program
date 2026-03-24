# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 8: production deploy (SSH/ECS) in `release.yml`, Codecov + Bandit SARIF + CycloneDX SBOM in CI, structlog JSON logging, enrollment `select_for_update` + rate limits, GitHub canary workflow, SLO/observability docs.

### Changed

- Enrollment POST uses atomic row lock and shared service `enrollment_atomic`.

## [1.0.0] - YYYY-MM-DD

### Added

- Initial production-ready baseline (Django + MySQL, CI/CD, security hardening; Phase 7 release/runbooks + `X-Request-ID`).

[Unreleased]: https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/HimmetDemir45/student-course-selection-and-academic-management-program/releases/tag/v1.0.0
