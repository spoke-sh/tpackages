# SAML service provider

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `ServiceProvider(binding, config)` and `read_metadata(xml, digest, entity_id)`.
Package dependencies: None.

`begin_sso` emits a signed HTTP-Redirect AuthnRequest with a bound RelayState. `accept_assertion` verifies the exact signed assertion node and issuer/audience/request/recipient/time bindings. One atomic command consumes request KV, inserts the issuer/assertion replay claim, and appends a typed identity to `completions`. Trust keys are explicit runtime references; metadata requires an out-of-band content digest.

Approved trust uses a versioned Document. The separately authorized
`configure_trust` command updates keys/enabled state against an expected revision;
`policy_status` exposes that revision only to configuration authority. Outstanding
requests fence their accepted trust revision. Native bounded maintenance removes
expired context and replay KV only after the final allowed acceptance time,
including clock skew. Result history remains retained and requires current read
authority; it does not extend an identity's validity.

Optional `Http` binds same-origin initiation and cross-site POST assertion intake,
using protected transient form fields and a Secure/HttpOnly/SameSite=None browser
cookie. Selecting `ServiceProvider` alone installs no routes.
The binding checks its receiving URL against the core's pure `assertion_endpoint`
configuration accessor before activation.

## Initial profile

SP-initiated SSO with one unencrypted signed assertion, one bearer confirmation and AuthnStatement, RSA-SHA256, SHA-256 digest, and exclusive canonicalization. No IdP mode, unsolicited response, SLO, encrypted assertions, complex XML attributes, Address constraints, or arbitrary metadata URL fetching.

## Consumption and testing

Declare this repository at an exact revision with subdirectory `packages/saml`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build saml` and `just test saml` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [SAML profiles](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf), [SAML bindings](https://docs.oasis-open.org/security/saml/v2.0/saml-bindings-2.0-os.pdf).
