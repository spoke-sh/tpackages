# tpackages

Officially maintained application-layer protocol packages for Transit applications.
`tpackages` owns reusable protocol implementations and their provider adapters.
[`tintegrations`](https://github.com/spoke-sh/tintegrations) owns service-specific
clients, resource mappings, and workflows for Stripe, Salesforce, HubSpot, and
similar services. Integrations should compose these packages.

Eight packages now contain target-language source, examples, and tests. They are
**unqualified**: the pinned compiler rejects workspace/lazy-export syntax before
checking their implementations. No production packages have shipped yet.

## Scope and layout

All maintained packages live directly under `packages/<name>/`. Protocol cores
use the protocol name; provider adapters use `<protocol>-<provider>`. The planned
package set is:

```text
packages/
  oauth/           shared OAuth client implementation
  oauth-facebook/  Facebook OAuth adapter
  oauth-google/    Google OAuth adapter
  oauth-github/    GitHub OAuth adapter
  oidc/            OpenID Connect client implementation, composed with oauth
  saml/            SAML 2.0 federation and SSO
  scim/            user and group provisioning
  webauthn/        public-key credential registration and authentication
```

These are independent package roots. [Package conventions](packages/README.md) define the internal directory
structure, dependency boundaries, and planned protocols.

The [initial implementation plan](docs/implementation-plan.md) records the workspace
and consumer model. The [dataflow and state model plan](docs/dataflow-refactor-plan.md)
records the implemented source design across all eight packages. Commands admit
work, native dataflows advance effects and consume results, versioned Documents
hold mutable policy/attributes, and KV holds one-use challenge context. Tables
enforce relational integrity; Streams carry committed results. OIDC verification
continues automatically from OAuth completion. HTTP bindings and read Publications
are optional selected modules. The [API and state migration map](docs/refactor-compatibility.md),
[language proposal](docs/target-language.md), and
[compiler requirement ledger](docs/compiler-requirements.md) make the upstream
work needed to execute these packages explicit.

| Owner | Responsibility |
| --- | --- |
| Transit runtime | Execution, durable state, secrets, transport capabilities, and authorized effects. |
| `tpackages` | Protocol flows, message formats, validation, and provider-specific protocol behavior. |
| `tintegrations` | Product APIs and domain workflows, such as GitHub issues, Google Drive files, or Salesforce records. |
| Applications | Session policy, tenant roles, business quotas, and audit policy. |

For example, `oauth-github` obtains GitHub authorization through the shared OAuth
implementation; a GitHub integration uses that authorization to work with issues
and repositories. Provider-specific protocol behavior belongs with the adapter.

The initial implementations cover OAuth, its provider adapters, OIDC, SAML, SCIM,
and WebAuthn. Each package README defines its supported target profile and exclusions.
General sessions, authorization policy,
pagination, idempotency, rate limiting, and audit utilities are outside the initial
package roadmap. A protocol can still require internal state or helpers for those
concerns.

## Development

Install Nix with flakes enabled, then enter the shell:

```sh
nix develop
just
just check
just test bootstrap
just build bootstrap
just fmt
```

The shell consumes the upstream `transit` and `transitc` package artifacts and
provides Git, Just, nixfmt, and Python for repository checks. It contains no Zig or
C compiler toolchain. Protocol logic and tests are Transit source; Python only
checks repository structure and records compiler diagnostics.
Optional direnv support is provided by `.envrc`.

| Task | Behavior |
| --- | --- |
| `just` | List the five tasks. |
| `just check` | Check formatting, public import boundaries, checker negative controls, the native bootstrap, and exact recorded compiler gaps; evaluate the flake without changing its lock. |
| `just test [package]` | Run a package's Transit tests. Defaults to `all`; use `bootstrap` for the currently executable Table suite. |
| `just build [package]` | Emit a package's example SQL and provenance. Defaults to `all`; use `bootstrap` for the currently executable fixture. |
| `just fmt` | Format the Nix and Just files. Neither pinned CLI exposes a Transit source formatter yet. |

`build.transit` declares the target workspace and grouped package targets. It
does not make every package a dependency of every application. Consumers select
public entries and their transitive dependencies at a single pinned repository
revision; see the [consumer fixtures](tests/consumers/README.md).

`just build oauth-github` and `just test oauth-github`, like the default `all`
targets, currently return a compiler failure. `just check` reports these as
**blocked**, with downstream stages **not run**. Matching a known diagnostic is
not a successful package build or protocol test. Unexpected failures or passes
fail the check and require review. Detailed reports are in `.transit/reports/`.

The separate bootstrap checks module reuse, independent instances, isolated test
state, and duplicate-key refusal. It is not a protocol package. The tests need no
server, containers, credentials, or provider network access. The external consumer
check creates and discards a temporary local Git snapshot; it never changes this
repository's history. `nix flake check --print-build-logs` runs formatting and the
isolated bootstrap build/tests in a Nix sandbox. Nix may fetch or build upstream
artifacts on first use.

The pinned standalone `transitc` currently implements only `--help` and `--version`.
Compilation and tests use `transit build` and `transit test` until the compiler
extraction supplies those capabilities. Target-language implementation deliberately
precedes compiler/runtime support; blocked stages remain visible in the ledger.

## Upstream pins

`flake.nix` selects exact Git revisions of both upstreams; `flake.lock` records
their content hashes and transitive dependencies. nixpkgs follows Transit's
locked input. No sibling checkout or moving branch is required.

The initial `transitc` pin includes the package output introduced in
[`transitc` PR #1](https://github.com/spoke-sh/transitc/pull/1) and points to its
merge commit on `main`.

To upgrade, change the relevant full commit hash in `flake.nix`, run
`nix flake lock`, and review both files. Re-enter `nix develop`, run all four
operational tasks, and re-audit the recorded gaps; the checker intentionally
refuses stale pin/diagnostic records. Then run
`nix flake check --print-build-logs`. Keep pin changes
separate from package behavior changes so compatibility failures are attributable.

The flake declares x86_64/aarch64 Linux and Darwin, matching the upstream flakes.
Local validation establishes only the host platform's result.
