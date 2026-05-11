# IRT Security Overview

This directory contains security analysis, reports, and configurations for the IRT (Anket Sistemi) project.

## Project Structure
- `reports/security/`: Automated and manual scan results.
- `logs/security/`: Security-related logs (auth, access control).
- `scripts/security/`: Scripts for running security checks.
- `backend/security/`: Security policies and configurations.

## Current Security Status
- **Auth**: Secure hashing used.
- **CSRF**: Protected.
- **Rate Limiting**: Enabled for sensitive endpoints.
- **Secrets**: Managed via `.env` (excluded from Git).

## Planned Tests
- SAST (Manual/Semgrep)
- Dependency Audit (pip-audit)
- Secret Scanning (Gitleaks/Manual)
- Prompt Injection Testing
