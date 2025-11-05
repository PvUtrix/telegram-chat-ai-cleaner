# Security Policy

## Supported Versions

We currently support the latest minor version. Please open an issue if you need backports.

## Reporting a Vulnerability

- Email: pvutrix@gmail.com
- Or open a private security advisory on the repository

Please include:
- A clear description of the issue and potential impact
- Steps to reproduce (PoC if applicable)
- Affected versions/commit hashes

We aim to respond within 7 days and will coordinate disclosure.

## Handling Sensitive Data

- Do not upload real chat data to issues or PRs. Use synthetic/redacted examples.
- Never commit `.env` or files under `data/`. These are ignored by default.
