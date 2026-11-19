# OpenID Connect relying party

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `RelyingParty(binding, config)`.
Package dependencies: `oauth` from the same workspace revision.

`discover` fetches and validates metadata and JWKS against explicitly configured issuer/endpoints. `begin_authentication` atomically creates an OAuth challenge and OIDC nonce context; `accept_callback` admits the exchange. A required consumer of OAuth's completion Stream verifies the ID token and commits its typed identity result, context consumption, and checkpoint together. There is no finishing call or application poller.

The core exposes `completions` (Pending/Verified/Refused/Unknown outcome type),
`status`, `outcome`, and `discovery_status`. Terminal completion events retain the
original authorization ID and owner. `outcome` never advances work. Validated
metadata/JWKS use versioned Documents; nonce context uses KV; result Tables retain
terminal evidence. Identity results describe the accepted authentication event;
applications enforce identity expiry and their current session policy when using
those claims. Native maintenance refuses expired pending authentications.

Applications explicitly authorize the core and its `configuration`, `jwks`, and
`token` effects, then activate its flows. The OAuth protected-use capability is
granted only to OIDC validation. Optional `Http` and `Publication` exports add
routes and authorized status delivery when selected; import alone grants nothing.

## Initial profile

Authorization-code flow and RS256-signed ID tokens only; no implicit/hybrid flow, JWE, UserInfo, dynamic client registration, or logout. Endpoint changes require configuration review. The pure validator returns RefreshKeysRequired for an unknown key. The identity dataflow permits one bounded JWKS refresh under the original input/effect ID, then revalidates. Other validation failures are terminal refusals. Network access is explicit in the dataflow; the validator stays pure.

## Consumption and testing

Declare this repository at an exact revision with subdirectory `packages/oidc`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build oidc` and `just test oidc` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html), [Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html).
