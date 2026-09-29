# Security Policy

## Reporting a vulnerability

**Please do not open a public issue.**

Report vulnerabilities privately through GitHub: **Security → Report a vulnerability** on this repository (private vulnerability reporting).

We aim to acknowledge reports within 7 days.

## Scope

In scope:
- The web app and API layer.
- The engine service.
- Upload handling.
- Authentication (once added).
- Anything that could expose user images, birth data or readings.

Out of scope:
- Third-party datasets and models (report those to their owners).
- Findings that need a malicious local administrator.

## Privacy by design

- Uploaded palm images are deleted after 24 hours unless the user explicitly opts in ([D-007](docs/DECISIONS.md)).
- Images are never sent to an LLM.
- Secrets are never committed. `.env*` files are git-ignored, and CI runs without secrets.
