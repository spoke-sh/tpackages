# WebAuthn relying party

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `RelyingParty(binding, config, policy)`.
Package dependencies: None.

The four command dataflows `begin_registration`, `accept_registration`,
`begin_authentication`, and `accept_authentication` bind owner, browser, challenge,
origin, RP ID, and user handle. Registration stores a validated public key;
authentication verifies the signature and updates counters/backup state. Challenge
KV consumption, credential Table mutation, and a typed `completions` event commit
together. No background queue is needed for these local verification steps.

A versioned policy Document fences outstanding ceremonies. `configure_policy`
requires separate configuration authority and an expected revision; `policy_status`
exposes that revision to administrators. Application Policy guards authorize
ceremonies, and `can_read_credential` controls the `credential_metadata` View.
Optional `Http` supplies strict JSON/byte decoding and browser cookies; optional
`Publication` exposes safe credential metadata. Core selection installs neither.
Results do not create sessions.

## Initial profile

ES256/P-256, none attestation, HTTPS same-origin ceremonies, no authenticator extensions or attestation trust roots. Zero counters are valid; nonincreasing nonzero counters produce a policy signal or refusal according to configuration. Configuration requests user verification explicitly. Bounded native maintenance removes expired challenges, never credentials. Browser code uses navigator.credentials and converts base64url option strings to bytes; that browser transport is not a second verification implementation.

## Consumption and testing

Declare this repository at an exact revision with subdirectory `packages/webauthn`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build webauthn` and `just test webauthn` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [WebAuthn Level 3](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/).
