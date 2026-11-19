# OAuth client core

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `Client(binding, provider, config)`.
Package dependencies: None.

Authorization-code requests with S256, browser/state/redirect binding, atomic one-use callbacks, protected token storage, refresh generation fencing, and explicit revocation. `begin_authorization` returns redirect data; `accept_callback` returns an operation ID. Separate code, refresh, and revocation Queue dataflows advance accepted work and append one terminal outcome to `completions`. `outcome` and `status` only observe progress. Applications own account linking and sessions.

## Initial profile

Confidential clients, bearer tokens, explicit HTTPS endpoint allowlists, and authorization-code/refresh grants only. No authorization server, implicit/device/client-credentials grants, DPoP, or automatic retry after an unknown exchange.

## Consumption and testing

The application adapter supplies an unguessable browser binding from its protected
session/cookie handling, the exact receiving redirect URI, and uniquely decoded
callback fields. Reject duplicate query parameters before invoking `accept_callback`.
Use distinct redirect URIs for different issuers when the provider does not return
an issuer parameter. Token material remains a protected value when returned to
authorized integrations; it must not be serialized into an ordinary HTTP response.

The public commands are `begin_authorization`, `accept_callback`, `refresh`,
`revoke`, and separately authorized `set_enabled`. State uses a versioned policy
Document, challenge KV with an expiry index, credential/operation Tables, and
private work Queues. Native maintenance expires challenge material in bounded
batches while retaining operation evidence. No application cleanup loop is needed.

`completions`, `status`, `credential_metadata`, and `policy_status` require current
read authority. `token_material` additionally requires explicit protected-use
invocation authority. The `token` and optional `revocation` sink references permit
explicit effect authorization; queues remain private. OIDC composes the small
atomic `issue_challenge` helper with its own nonce KV in one transaction. It uses
the same guards as `begin_authorization`, with a separate invocation capability.

Select `Http` for native begin/callback Sources or `Publication` for authorized
status reads. The core target selects neither. The optional HTTP target sets a
protected cookie, returns 303 from initiation and 202 from callback admission;
applications consume the result Stream to continue their own workflow.

Declare this repository at an exact revision with subdirectory `packages/oauth`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build oauth` and `just test oauth` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [OAuth 2.0](https://www.rfc-editor.org/rfc/rfc6749.html), [PKCE](https://www.rfc-editor.org/rfc/rfc7636.html), [security BCP](https://www.rfc-editor.org/rfc/rfc9700.html), [revocation](https://www.rfc-editor.org/rfc/rfc7009.html).
