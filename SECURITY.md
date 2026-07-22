# Security policy

## Reporting a vulnerability

Report vulnerabilities privately via
[GitHub Security Advisories](https://github.com/geisten/geist-home-assistant/security/advisories/new).
Do not open public issues for security reports. You should receive an initial
response within 7 days.

Issues in the inference engine or the normative `dynamic-tools-v1` protocol
belong to [`geisten/geisten`](https://github.com/geisten/geisten/security).

## Supported versions

Only the latest published release (including beta prereleases) receives
security fixes.

## Scope and security model

- The integration is the sole policy and execution boundary: the Geist
  runtime receives no Home Assistant credentials and cannot call Home
  Assistant directly.
- Transport is a local Unix socket only; there is no network endpoint.
- Every proposed tool call is revalidated against the current Assist
  exposure immediately before execution.

Reports that break any of these guarantees — credential leakage to the
runtime, execution of a non-exposed entity or non-offered service, policy
bypass through frame manipulation — are in scope, as are supply-chain issues
in the release and app-image pipeline (see
[docs/SUPPLY_CHAIN.md](docs/SUPPLY_CHAIN.md)).
