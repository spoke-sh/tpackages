# Protocol packages implementation plan

Status: **Implementation authorized; target-language source authored.** The eight
package roots, examples, protocol tests, consumer fixtures, and compiler gap
reporting now exist. Qualification remains blocked by the pinned compiler. See
[compiler-requirements.md](compiler-requirements.md) for actual evidence and
[target-language.md](target-language.md) for the proposed syntax in use.

The [dataflow and state model refactor](dataflow-refactor-plan.md) is now authored
across all eight packages, with qualification still blocked. It replaces the behavior/API
approach and delivery sequence below while preserving the workspace, package
selection, protocol profiles, and qualification obligations recorded here.

## Objective and proposed decisions

Write reusable protocol implementations in the target Transit language, maintained
in one workspace and consumed as individual packages by Transit applications.
The source, tests, and examples should express the language we intend to support,
even when the pinned compiler or runtime cannot execute them yet. Those failures
are concrete upstream requirements, not a reason to move protocol logic into
another language or omit the intended behavior.

The implementation decisions are:

1. Keep eight independent package roots under `packages/`: `oauth`,
   `oauth-facebook`, `oauth-google`, `oauth-github`, `oidc`, `saml`, `scim`, and
   `webauthn`. Applications select packages and their transitive dependencies.
2. Initially version the collection by one exact Git revision per consuming
   application. Packages remain independently selectable without introducing
   independent release trains or a registry yet.
3. Implement OAuth clients and OIDC relying parties, SAML service-provider SSO,
   SCIM service-provider provisioning, and WebAuthn relying-party ceremonies.
   Broader roles and extensions are separate scope decisions.
4. Start with `oauth` plus `oauth-github` as a complete vertical slice, then add
   Google, Facebook, and OIDC. Author SAML, SCIM, and WebAuthn against the same
   composition conventions without waiting for every compiler gap to close.
5. Track source completeness separately from executable support. A package can
   be complete for design review while still awaiting compiler/runtime support;
   a usable release requires passing its actual build and protocol tests.

## Language basis and current baseline

Follow Transit's target model for
[modules, workspaces, packages, targets, and executable SQL](https://github.com/spoke-sh/transit/blob/c1f2680d9353175e58ad503e750e7b4da76a84c5/docs/roadmap/12-application-modules-compilation-and-testing.md#d2--recursive-typed-modules-repository-dependencies-and-explicit-stateful-instances)
and its
[downstream application language direction](https://github.com/spoke-sh/transit/blob/c1f2680d9353175e58ad503e750e7b4da76a84c5/docs/roadmap/downstream-application-language.md).
Use the
[implemented source contract](https://github.com/spoke-sh/transit/blob/c1f2680d9353175e58ad503e750e7b4da76a84c5/contracts/APPLICATION_SOURCE_V1.md)
to establish support, rather than treating roadmap examples as implemented syntax.

The starting pins in [flake.nix](../flake.nix) are Transit
`c1f2680d9353175e58ad503e750e7b4da76a84c5` and transitc
`61536eaa510e2ba8826c08b4f41072ed66f41ed5`. The standalone transitc artifact is
currently a CLI scaffold; existing builds and tests use Transit's embedded
compiler. The bootstrap fixture is the currently executable subset.

Keep consuming the upstream executable artifacts through Nix. Compiler and runtime
implementation belongs upstream; this repository needs no Zig toolchain. When the
target design leaves syntax unspecified, document a small proposed language
extension with its `.transit` use case and expected semantics. Label it proposed;
do not present an invented construct as an existing language feature.

## Repository and package boundaries

```text
build.transit                       workspace composition and selected targets
packages/
  README.md                         shared package conventions
  <name>/
    README.md                       role, profile, public API, support status
    build.transit                   public modules and build/test/example targets
    src/                            private Transit implementation
    tests/                          Transit tests and bounded protocol fixtures
    examples/                       small Transit consumer compositions
tests/
  bootstrap/                        runnable tooling baseline
  consumers/<case>/build.transit     independently rooted consumer applications
docs/
  implementation-plan.md            this plan
  compiler-requirements.md           requirement and support ledger, added in phase 1
```

A workspace coordinates packages and targets. A package is a distributable source
boundary; modules provide typed interfaces; targets select compositions. A SQL
schema is a runtime namespace, not a package identity. The root build aggregates
development targets without becoming an umbrella dependency for applications.

Each package exports its public modules through `build.transit`. Tests and examples
have explicit targets and are excluded from production compositions. Other
packages and consumers import those exports, never `src/` internals. Shared code
belongs to a declared package dependency; do not create a hidden root `lib/` that
only works in a checkout of this repository.

The initial dependency graph is:

| Package | Direct package dependencies |
| --- | --- |
| `oauth` | None |
| `oauth-facebook`, `oauth-google`, `oauth-github` | `oauth` |
| `oidc` | `oauth` |
| `saml`, `scim`, `webauthn` | None initially |

Runtime capabilities such as HTTP, cryptography, secrets, and durable storage are
explicit inputs or native primitives, not reasons to depend on an unrelated
protocol package. In particular, SCIM's application-supplied authorization does
not impose an OAuth implementation. Add shared protocol dependencies later only
when their public contracts justify them.

### Selective consumption and reproducibility

An external application declares the repository URL, exact revision, and selected
package subdirectory, then imports that package's public entry point. Use Transit's
repository dependency and lock model, including content verification and explicit
fetch/update operations. A frozen build must work offline after fetching.

Internal dependencies need a native **same-workspace dependency** contract:

- In this checkout, `oauth-github` resolves its declared `oauth` dependency to the
  workspace package through the public interface.
- When fetched from revision R, it resolves `oauth` from this repository at R.
  The consumer lock records both package subdirectories and their shared revision.
- The package must not embed its own future release commit hash or import private
  sibling files. A local override is explicit and appears in provenance.
- Selecting `oidc` and `oauth-github` at R shares one source dependency on `oauth`.
  Source deduplication does not silently merge their stateful instances. Initially,
  conflicting tpackages revisions in one application are rejected with a useful
  diagnostic; supporting mixed revisions is a later resolver decision.

The precise declaration syntax and resolver support must be specified with
transitc. This is a target-language requirement, not a claim that the current
dependency syntax already supports inherited workspace revisions. Do not build a
second package resolver in shell, Python, or JavaScript to conceal the gap.

Only the selected package/target dependency closure may be resolved, typechecked,
and emitted. Unselected packages and test/example targets must not introduce
dependencies, require runtime settings or secrets, create state, or break the
selected build because their source uses unsupported features. Source capture and
cache invalidation should preserve this boundary too. Fetching a Git repository
may still transfer its entire tree; selective compilation does not promise
per-package network downloads.

Outputs are executable SQL plus source maps and provenance identifying package
revisions, compiler/contract versions, targets, bindings, and dependency closure.
Compilation must not contact providers, resolve live secrets, apply migrations,
or activate services. A source upgrade is not a state migration: stateful packages
need stable instance bindings and explicit migration targets with a prior basis.

## Implementation contracts

Protocol logic, message validation, state transitions, and tests live in `.transit`.
Use typed module parameters and exports for configuration, application policy,
and runtime capabilities. Keep deterministic transformations, atomic state changes,
and external effects distinct in their interfaces. Do not return an undifferentiated
JSON value where a typed success, refusal, pending, or unknown outcome is needed.

Each stateful constructor accepts an explicit instance binding. Applications can
instantiate the same package for separate tenants or providers without sharing
challenges, credentials, or replay state accidentally. Instance identity survives
import renames and source moves. Package imports themselves confer no authority;
runtime access enforcement must survive lowering to SQL.

Secrets and bearer credentials use protected values or handles. Application-facing
results expose only the necessary claims, references, and permitted token access.
Do not serialize credentials into ordinary tables, logs, errors, or build outputs.
Use runtime cryptographic and codec primitives backed by established implementations;
the package owns protocol policy and validation, not handwritten cryptography.

External requests use explicit durable effects with bounded deadlines, response
sizes, and parsing work. Retries must respect the original operation and the
protocol's replay rules. A lost token-exchange response can leave an unknown
outcome; recovery must not blindly repeat the exchange. Atomic challenge claim,
effect scheduling, result acceptance, and response ownership must have explicit
contracts and tests. The package does not promise remote rollback.

Applications retain account linking, sessions, roles, and business policy.
`tintegrations` retains product resource APIs. Browser code can invoke WebAuthn's
browser API, but protocol verification and state transitions remain in Transit.

## Initial protocol profiles

These are proposed first implementation boundaries, not claims of full standard
coverage. Every package README will name its role, supported operations, excluded
extensions, configuration, dependencies, and compiler/runtime support.

| Package | First profile and public behavior | Required tests |
| --- | --- | --- |
| `oauth` | OAuth client authorization-code flow with PKCE, one-use state, redirect binding, protected token results, and explicit refresh/revocation capabilities where supported. No authorization-server implementation or additional grants initially. | State mismatch/expiry/replay, redirect and provider mix-up, malformed responses, unsupported capability refusal, refresh races, and lost exchange outcomes. |
| `oauth-github` | Thin GitHub endpoint, parameter, response, and capability profile over `oauth`; no repository or issue APIs. | Core contract suite plus provider-specific parameters, errors, token modes, and capability refusals. |
| `oauth-google` | Google's OAuth authorization profile over `oauth`; generic OIDC configuration handles standards-based Google sign-in. | Core contract suite plus scopes, consent/offline-access behavior, and token-response variations. |
| `oauth-facebook` | Facebook Login authorization profile over `oauth`, with explicit supported capabilities and documented deviations. | Core contract suite plus provider errors, token lifecycle, and unsupported-feature behavior. |
| `oidc` | Relying-party authorization-code flow composed with OAuth; discovery, JWKS, ID-token validation, and typed verified claims. | Issuer/audience/nonce/time checks, algorithm/key restrictions, key rotation, invalid signatures, discovery bounds, and replay. |
| `saml` | SAML 2.0 SP-initiated Web Browser SSO: Redirect requests, POST responses, explicit metadata/trust configuration, and verified assertion results. Defer IdP mode, unsolicited responses, and single logout. | Signed-node binding and wrapping attacks, destination/audience/InResponseTo checks, time/replay rules, trust rotation, and bounded XML parsing. |
| `scim` | SCIM 2.0 service provider for Users and Groups, backed by application-supplied identity storage and authorization modules. Define schemas/discovery, filtering, pagination, PATCH, errors, and conditional version behavior. Defer bulk and outbound client role. | Schema validation, filter limits, PATCH atomicity, pagination, uniqueness, authorization, stale versions, and group membership consistency. |
| `webauthn` | Relying-party registration and authentication: begin/finish ceremonies, challenge binding, credential verification, and typed results. Start with an explicit attestation policy accepting `none`; defer broader attestation trust management. | Challenge expiry/replay, origin/RP ID binding, user-presence/verification policy, malformed CBOR/COSE, bad signatures, duplicate credentials, and policy-aware counter/backup handling. |

Use [OAuth security BCP](https://www.rfc-editor.org/rfc/rfc9700.html),
[OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html),
[SAML profiles](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf),
[SCIM protocol](https://www.rfc-editor.org/rfc/rfc7644.html), and
[WebAuthn](https://www.w3.org/TR/2026/REC-webauthn-3-20260825/) as the protocol
references. Record the precise normative sections and any profile exclusions with
the tests implementing them.

Maintain a provider capability matrix sourced from the current official
[GitHub](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps),
[Google](https://developers.google.com/identity/protocols/oauth2/web-server), and
[Facebook](https://developers.facebook.com/documentation/facebook-login/guides/advanced/manual-flow)
documentation. Do not assume identical PKCE, refresh, revocation, or identity
behavior across providers. Unsupported capabilities must refuse explicitly; an
adapter must not silently downgrade the core's guarantees. Resolve any required
profile exception explicitly before describing that provider flow as supported.

## Driving compiler and runtime development

Add `docs/compiler-requirements.md` during the first implementation phase. It will
record exact source/test locations, intended semantics, upstream ownership,
support evidence, and linked upstream work. The following are requirements to
audit, not a declaration that all are missing today:

| ID | Required capability | Primary owner | Demonstrating consumer |
| --- | --- | --- | --- |
| TP-01 | Workspace package identity, inherited revision dependencies, public entry points, frozen transitive resolution. | transitc workspace/resolver | External application importing only `oauth-github`. |
| TP-02 | Selected target/source closure; unused future syntax and test dependencies cannot invalidate production builds. | transitc workspace/build | `oauth-github` builds while an unrelated package remains unsupported. |
| TP-03 | Typed higher-order modules, nominal values, result variants, behavioral/effect interfaces, hygienic specialization. | transitc typechecking/lowering | Core OAuth composed with a provider and application policy. |
| TP-04 | Stable stateful instances, enforceable private storage, explicit migration bases. | transitc and Transit catalog/authorization | Two OAuth instances, source rename, and a reviewed state upgrade. |
| TP-05 | Protected secret/token values, controlled disclosure, runtime settings, and redacted diagnostics. | transitc and Transit secret/effect owners | Token exchange and credential rotation without plaintext leakage. |
| TP-06 | Typed HTTP ingress/egress, atomic claim and scheduling, durable effect outcomes, deadlines, response ownership. | Transit effects/serving and transitc lowering | OAuth callback with a crash or lost provider reply. |
| TP-07 | Bounded URI/form/JSON/JWT/JWK/XML/CBOR/COSE handling and suitable native cryptographic operations. | Transit native primitives and transitc bindings | OIDC validation, SAML signatures, WebAuthn verification. Split into precise primitive contracts as needed. |
| TP-08 | Deterministic clock/entropy controls, mocked transports, effect assertions, failure injection, and replay tests. | Transit test execution and transitc test targets | Expiry, duplicate callbacks, and recovery tests. |
| TP-09 | Canonical executable SQL with provenance and package-attributed diagnostics; compiler CLI parity. | transitc and Transit SQL execution | Standalone compiler output installed without a source checkout. |

For every blocked case, record the selected target and command, exact upstream
pins, first failing stage and diagnostic, minimal reproducer, intended result, and
the requirement that would unblock it. Distinguish `not attempted`, `blocked`,
`failed`, and `passed` for resolution, parsing/typechecking, SQL emission, SQL
installation, and test execution. A parser failure in a negative protocol test
does not count as the protocol correctly rejecting an invalid message.

Author full target-language implementations and expected test outcomes despite
known gaps. Empty exports, TODO bodies, and skipped assertions do not complete an
authoring milestone. Minimal reproducers accompany the real implementation; they
do not replace its tests. Track changes to proposed syntax against the upstream
language decision so several packages do not invent incompatible versions.

### Commands and CI during the transition

Keep exactly five Just recipes: `default`, `build`, `test`, `check`, and `fmt`.
The intended command contract is below; optional selection arguments and their
underlying CLI mapping are implementation work, not commands available today.

| Recipe | Intended behavior |
| --- | --- |
| `just` | List tasks and explain package selection. |
| `just build [package\|all]` | Build the selected package composition and dependency closure; default to all maintained packages. Return failure when compilation is unsupported. |
| `just test [package\|all]` | Run selected protocol and relevant consumer tests; default to all. Report blocked execution distinctly and return failure when tests cannot run. |
| `just check` | Check tooling, package boundaries, requirement records, the isolated bootstrap, and executable-package regressions. Report separately whether target-language builds/tests are qualified. |
| `just fmt` | Format supported files; add Transit formatting when an upstream artifact provides it. |

Before adding unsupported source, isolate the bootstrap's source root and Nix
check so unrelated source capture cannot break the runnable tooling baseline.
Use explicit compiler targets, not a recursive shell build per package. Ordinary
build/test commands must not fetch dependencies implicitly or convert a failure
into success with `|| true`.

CI should distinguish blocking tooling/boundary checks and regressions from
reported known compiler gaps. Run the attempted target-language builds/tests and
retain their diagnostics even while those cases are blocked. A narrowly matched,
reviewed gap record can explain a non-blocking case; blanket allowed-failure jobs
cannot qualify a package. New failures, changed failure stages, and unexpected
passes require triage and ledger updates. Passing bootstrap checks must never be
presented as passing the protocol suite. Once a case executes successfully, make
it a required regression check.

## Delivery sequence and review gates

Each phase produces a reviewable change. Compiler fixes and pin upgrades can
proceed alongside package authoring; unsupported compilation does not prevent a
source-design review from completing.

### Phase 1 — Workspace contract and consumer fixtures

Specify public entry points, native sibling dependency semantics, instance
bindings, and target selection. Add the requirement ledger and independently
rooted consumer fixtures. Adjust task/CI wiring to separate the bootstrap from
future package sources without expanding the five-recipe interface.

Acceptance: each consumer fixture declares its own imports and expected package
closure. At least one exercises a pinned repository/subdirectory dependency from
a clean fetched snapshot with no sibling checkout or implicit override. Record
unsupported resolver behavior rather than substituting filesystem shortcuts.

### Phase 2 — OAuth core and GitHub vertical slice

Implement the public OAuth types, configuration interfaces, authorization request,
challenge lifecycle, callback claim, protected exchange, and outcomes. Add the
GitHub adapter, provider capability declarations, protocol tests, and a minimal
consumer example whose application owns the resulting account/session policy.

Acceptance: the complete intended flow and refusal/recovery cases exist in Transit;
the adapter contains no duplicated grant engine or product API client. Every
blocked build/test maps to a reproducible requirement. Review the resulting API
before multiplying it across other packages.

### Phase 3 — Google, Facebook, and OIDC

Add the remaining OAuth adapters, then compose OIDC discovery and verified
identity claims over the common client. Reuse the core contract suite through
typed provider modules, supplemented by provider-specific fixtures. Include both
an OAuth authorization example and generic Google OIDC sign-in configuration.

Acceptance: provider differences are explicit, invalid capability combinations
refuse, and identity assertions are distinct from access tokens. An OIDC consumer
requires `oauth` but no provider adapter. Mixed OIDC/GitHub composition shares
source while retaining explicit stateful instance boundaries.

### Phase 4 — SAML, SCIM, and WebAuthn

Implement each initial profile as its own package and reviewable change. These
packages can progress independently after the workspace conventions are settled.
For SAML, define the XML/signature boundary before completing the SSO flow. For
SCIM, begin with the application identity-store interface and transactional PATCH
semantics. For WebAuthn, define credential/ceremony types and the codec/crypto
boundary before completing registration and authentication.

Acceptance per package: public API, full profile implementation, minimal consumer,
success/refusal/replay tests, and specific native/compiler requirements. No OAuth
dependency is introduced solely to share generic runtime capabilities. Record
profile exclusions explicitly rather than claiming complete standard coverage.

### Phase 5 — Qualification and first usable snapshots

As upstream capabilities land, update exact pins in separate changes, replace gap
records with execution evidence, and promote tests to required checks. Compile
consumer applications offline, install emitted SQL, and run the native tests.
Test state upgrades against explicit prior definitions and immutable migration
history. Confirm SQL can run without the package source tree or compiler.

Acceptance: each qualified package has a documented protocol profile and passing
package/consumer tests on named compiler/runtime revisions and platforms. Publish
support per package and profile: one executable package must not imply all eight
are ready. Early development snapshots remain clearly marked unqualified where
builds or tests are blocked.

## Consumer acceptance matrix

These tests define success for selective distribution and must live outside the
selected packages' own source roots.

| Consumer case | Required outcome |
| --- | --- |
| GitHub authorization only | Closure is `oauth-github` plus `oauth`; no Google, Facebook, OIDC, SAML, SCIM, or WebAuthn output or configuration. |
| Generic OIDC only | Closure is `oidc` plus `oauth`; no provider adapter required. |
| WebAuthn only | No OAuth code, state, secrets, or provider dependencies. |
| SAML plus SCIM | Only their explicit dependencies; application policy connects federation and provisioning. |
| OIDC plus GitHub | One pinned `oauth` source dependency, explicitly isolated instances where requested. |
| Two instances of one package | No accidental shared state; conflicting bindings fail with a diagnostic. |
| External application at revision R | Public imports resolve from the lock without a local tpackages checkout; frozen rebuild works offline. |
| Unrelated package uses unsupported syntax | Selected consumer builds without resolving or parsing the unrelated target. |
| Production target with unsupported test/example target | Production dependency closure and emitted SQL remain unchanged. |
| Two conflicting tpackages revisions | Resolver explains the conflict instead of silently selecting or mixing implementations. |
| Package/source rename or upgrade | Stable bindings preserve identity; required migration changes are explicit and reviewed. |

The implemented first profiles and exclusions are documented in each package's
README. Remaining qualification work includes frozen external rebuilds,
mixed-revision rejection, rename/migration evidence, and actual protocol execution.
None is marked complete merely because target-language source exists.
