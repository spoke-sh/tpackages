# Google OAuth adapter

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `Client(binding, config)` and `Provider()`.
Package dependencies: `oauth` from the same workspace revision.

Google authorization and token endpoints, optional refresh grants, and revocation compose the common OAuth client. Configuration can request consent/offline access. This obtains authorization; use `oidc` for verified identity.

## Initial profile

No service accounts, domain-wide delegation, resource API calls, or promise that every grant returns a refresh token. Additional returned scopes are refused; incremental authorization that widens the requested scope set is outside this profile.

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

Declare this repository at an exact revision with subdirectory `packages/oauth-google`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build oauth-google` and `just test oauth-google` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [Google web-server OAuth](https://developers.google.com/identity/protocols/oauth2/web-server), [Google's PKCE implementation](https://github.com/googleapis/google-auth-library-php/blob/main/src/OAuth2.php).
