# Package conventions

This directory contains reusable application-layer (L7) protocol implementations
and provider adapters. All eight package roots contain target-language source,
examples, and tests; none is qualified for production or executable on the current
pins. The [compiler ledger](../docs/compiler-requirements.md) records the blockers.
The [dataflow implementation plan](../docs/dataflow-refactor-plan.md) records the
authored composition, consumer acceptance tests, and compiler/runtime gates.

## Naming and structure

Use a flat `packages/<name>/` layout with lowercase kebab-case names:

- Protocol core: `oauth`, `oidc`, `saml`, `scim`, `webauthn`.
- Provider adapter: `oauth-facebook`, `oauth-google`, `oauth-github`.
- Add another protocol/provider combination only when it needs a maintained
  adapter; ordinary issuer or endpoint configuration does not require a package.

Each implemented package follows this layout:

```text
packages/<name>/
  README.md          purpose, supported protocol profile, public API, usage
  build.transit      public entry point and build/test targets
  src/               implementation modules
  tests/             protocol cases, fixtures, and refusal cases
  examples/          minimal consumer compositions
```

Consumers import the public entry point. It exposes the supported modules and
delegates to implementation files; `src/` paths are private implementation details.
Keep examples and tests executable through targets rooted at the package's
`build.transit`, so their imports remain inside the package root.

Repository-level `tests/` holds isolated bootstrap tests, minimal compiler probes,
and independently rooted consumer compositions. The root `build.transit` declares
workspace membership and groups the package targets; it is not an application
dependency. Keep the existing five Just tasks as the repository command surface.

Each package must document
its client/server role, supported flows and extensions, upstream Transit/transitc
compatibility, and protocol/provider references. Include a complete target-language
example and tests for its public contract. Source can precede compiler/runtime
support; record whether builds and tests pass, fail, or are blocked. A directory
name or a complete source implementation alone makes no compatibility promise.

## Shared cores and provider adapters

`oauth` owns the common OAuth client machinery. Provider packages depend on it and
provide endpoint configuration, supported capabilities, provider parameters,
response handling, and documented deviations. They do not duplicate grant flows
or weaken the core's validation rules. The core never imports a provider adapter.
Use [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) as the security baseline.

Commands/dataflows are the primary stateful API. Small atomic procedures are
reserved for shared transactions (OIDC challenge admission and SCIM store writes),
and bounded codecs/validators remain pure functions. Core construction, authority,
and activation are separate. Public examples wire a native result consumer and
declare their required roles; those role settings have no permissive defaults.

Versioned Documents own mutable policy, discovery/trust snapshots, and structured
SCIM attributes. KV owns point-addressed challenges/replay claims. Tables own
relational integrity and indexed status; private Queues carry external work.
Typed Streams append committed results with original owner/correlation and native
checkpoints. They explicitly retain history indefinitely in this initial profile;
changing that policy requires required-consumer protection and gap handling.
Native timers clean expired context in bounded batches. Operation evidence and
unknown effects survive challenge cleanup. Read Views enforce current authority;
historical results never extend identity or credential validity.

Select optional `Http` modules and Publications explicitly. The core target must
not instantiate routes/publications merely because a package exports them.
Pure validators similarly select no storage or activation. The
[compatibility map](../docs/refactor-compatibility.md) describes renamed APIs and
the required state-migration basis.

`oidc` composes with `oauth` and adds discovery, ID-token validation, and identity
claims. OAuth authorization and OIDC authentication remain explicit APIs; an
OAuth access token alone is not an identity assertion. The
[OIDC core specification](https://openid.net/specs/openid-connect-core-1_0.html)
defines that identity layer.

Google supports [OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).
Use generic `oidc` configuration for standards-compliant Google sign-in, and
`oauth-google` for Google's OAuth authorization profile. Add an `oidc-google`
adapter only if behavior beyond generic configuration warrants one. Apply the
same rule to other providers. Provider package names do not imply that every
provider supports the same flows or token behavior.

An adapter's boundary ends at its protocol contract. GitHub repository APIs,
Google Drive operations, Facebook product APIs, and other business resources
belong in `tintegrations`. If a login adapter needs a provider-specific identity
lookup, document that narrow operation as part of its identity contract; it must
not grow into a general provider API client.

Package dependencies must work outside this monorepo. External consumers select
a pinned repository revision and package subdirectory, importing the public entry
point. The target workspace model resolves internal package dependencies from the
same selected repository revision, or from the workspace during local development.
This requires an explicit resolver contract; see the implementation plan. Do not
embed a package's own future release revision or depend on `../oauth/src/...` and
other private sibling paths. Local overrides must remain visible in provenance;
published consumers use frozen sources. The declaration syntax and actual refusal
evidence are linked from the [language proposal](../docs/target-language.md).

## Protocol roadmap

The planned protocol packages are `oauth`, `oidc`, `saml`, `scim`, and `webauthn`,
alongside `oauth-facebook`, `oauth-google`, and `oauth-github`. Implementation
starts with OAuth and OIDC. SAML, SCIM, and WebAuthn are included in the roadmap
with these scopes:

| Planned package | Protocol responsibility | Reference |
| --- | --- | --- |
| `saml` | SAML 2.0 federation, initially a defined service-provider SSO profile. | [OASIS SAML profiles](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf) |
| `scim` | Standard user/group provisioning and synchronization; specify the supported client or service-provider role. | [SCIM protocol](https://www.rfc-editor.org/rfc/rfc7644.html) |
| `webauthn` | Relying-party registration and authentication ceremonies for public-key credentials. | [W3C WebAuthn](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/) |

The repository is not limited to identity protocols. A new package should name a
concrete protocol or interoperability profile, define the peer and supported
operations, and demonstrate reuse across applications. A generic feature name
such as `sessions`, `audit`, or `webhooks` is insufficient on its own. A webhook
package would need a defined wire contract, such as
[Standard Webhooks](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md).

Write against Transit's target transport, effect, secret, and durable-state
capabilities, documenting unsupported constructs as compiler/runtime requirements.
Use established cryptographic implementations through native primitives for
protocol validation. Qualify executable support separately from source authoring.
Application policy and provider product workflows stay with their respective
consumers.
