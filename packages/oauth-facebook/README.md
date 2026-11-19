# Facebook OAuth adapter

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `Client(binding, config, api_version)` and `Provider(api_version)`.
Package dependencies: `oauth` from the same workspace revision.

Versioned Facebook authorization and Graph token endpoints with comma-separated authorization scopes and a protected-query token exchange. The API version is explicit. S256 is always sent; the adapter never falls back to a state-only flow.

When a response omits its scope field, the returned scope set is conservatively
empty. Requested permissions are not asserted as granted after partial consent.

## Initial profile

Facebook Login authorization-code profile only. No long-lived token exchange, standard refresh grant, permission-deletion API, product resources, or identity assertion. Meta's SDK demonstrates PKCE, but the server-side deployment profile still needs provider qualification. Do not treat sending PKCE parameters as proof that a given deployment enforces them.

## Composition

The adapter forwards the shared core's `begin_authorization`, `accept_callback`,
`refresh`, `revoke`, and `set_enabled` command dataflows, `completions` Stream,
status/credential Views, and protected-use interface. Capability checks remain
provider-specific: exporting a command does not enable an unsupported grant.
The adapter owns no queue, challenge state, or scheduler. Optional `Http` reuses
the core binding; the default target contains only the core and a result consumer.
Shared command and HTTP suites run through this public adapter alongside its
provider cases. See the [core contract](../oauth/README.md).

## Consumption and testing

Declare this repository at an exact revision with subdirectory `packages/oauth-facebook`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build oauth-facebook` and `just test oauth-facebook` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [Manual login flow](https://developers.facebook.com/documentation/facebook-login/guides/advanced/manual-flow), [Meta SDK PKCE exchange](https://github.com/facebook/facebook-android-sdk/blob/main/facebook-common/src/main/java/com/facebook/login/LoginMethodHandler.kt).
