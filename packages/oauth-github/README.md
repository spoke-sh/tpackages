# GitHub OAuth adapter

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `Client(binding, config)` and `Provider()`.
Package dependencies: `oauth` from the same workspace revision.

GitHub.com authorization-code requests use the shared OAuth implementation. Responses use JSON, scopes are normalized from comma-separated token responses, and refresh is available only when the actual grant includes a refresh token. No identity lookup or product API calls are made.

## Initial profile

OAuth Apps on GitHub.com; no Enterprise endpoint rewriting, GitHub App installation authentication, device grant, or REST token-deletion API. Generic RFC 7009 revocation is refused.

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

Declare this repository at an exact revision with subdirectory `packages/oauth-github`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build oauth-github` and `just test oauth-github` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [GitHub authorization](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps).
