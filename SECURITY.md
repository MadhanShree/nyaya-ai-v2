# Security

Please do not commit API keys, passwords, uploaded legal documents, or other sensitive information to this repository.

## Reporting

For a suspected vulnerability, use a private GitHub security report if enabled for the repository. Do not publish credentials or exploitable details in a public issue.

## Application security model

NyayaAI treats uploaded document text as untrusted data, limits upload and question sizes, applies security headers, validates supported document types, avoids rendering model output as HTML, and keeps uploaded documents in bounded process memory.

The application is an information tool, not a legal advice service or a permanent legal records system.
