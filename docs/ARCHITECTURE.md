# Architecture

## Ownership boundary

`geisten/geistlib` owns inference, model loading, the resident dynamic-tools
service, and the normative wire protocol. This repository owns all Home
Assistant behavior and distribution.

```text
Home Assistant Assist
  -> geist_conversation integration
       -> exposure snapshot + request-scoped tools
       -> Geist dynamic-tools-v1 runtime
       <- proposed tool calls / response
       -> policy revalidation
       -> Home Assistant service execution
```

The runtime receives no Home Assistant credential and cannot call Home
Assistant directly. The integration is the sole policy and execution boundary.
It rejects entities that are no longer exposed and never offers arbitrary
service-call tools.

## Repository coupling

The repositories are coupled through:

1. the `dynamic-tools-v1` protocol identifier and JSON framing;
2. golden request/response fixtures under `protocol/`;
3. immutable, checksum-verified Geist release artifacts used by the HA app.

They are not coupled by Git submodules, copied engine source, REST endpoints,
or a shared release cadence. A protocol change must first be additive or use a
new protocol identifier, update fixtures in both repositories, and pass the
contract suites before either consumer is released.

## Transport profiles

- HA Core/Container on Linux: a resident Geist process and a mode-0600
  Unix socket in the HA config directory.
- HA OS/Supervised: a protected HA app with an internal-only transport. No host
  ports, HA credentials, Docker socket, host namespaces, or `/config` mount.

## Decisions

- **Native HA LLM API (`homeassistant.helpers.llm`) is deliberately not
  adopted.** Exposure already delegates to HA's `async_should_expose`; the
  only duplication is the request-scoped tool build. Adopting `llm.AssistAPI`
  would trade the enum-constrained entity names and the double validation at
  the action boundary for HA's broader intent surface. Revisit only if the
  integration targets HA Core inclusion.
- **The zero-queue gate stays.** An immediate `busy` is honest for one
  resident model with worst-case 60 s turns; a queue would silently stall the
  second speaker instead. Revisit with the P6 latency evidence
  ([#16](https://github.com/geisten/geist-home-assistant/issues/16)) and the
  deterministic fast-path
  ([#14](https://github.com/geisten/geist-home-assistant/issues/14)).
- **Streaming arrives additively in `dynamic-tools-v1`**, never as a new
  protocol id: the engine advertises a `features` capability in
  `health.result`, opted-in requests receive `conversation.delta` frames, and
  the final `conversation.result` stays normative. Engine work:
  [geisten/geistlib#116](https://github.com/geisten/geistlib/issues/116); HA work:
  [#17](https://github.com/geisten/geist-home-assistant/issues/17). It is
  intentionally not part of engine release `v0.4.0`
  ([geisten/geistlib#87](https://github.com/geisten/geistlib/issues/87)) that
  unblocks P5.1.
- **`DataUpdateCoordinator` and `entry.runtime_data` are intentionally not
  used.** The integration keeps no `hass.data`, and the single diagnostic
  sensor polls one local health handshake; coordinator plumbing would change
  no behavior.
