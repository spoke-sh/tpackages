# Compiler and runtime requirements

All twenty protocol and support packages contain target-language implementations, examples,
and Transit tests. **None is executable or qualified on the current pins.**
The compiler rejects their entries before checking implementation bodies. Source
review and the checks below do not establish protocol correctness or conformance.

Baseline:

- Transit: `f31673bbd0fa599c9d2bd98c2ceb47d328c19ae6`.
- transitc: `0dd62605005bec8c0fbb4c1b691bc635c3512244`.
- Compiler diagnostic definition: `f311e893f8d2f4c21f426790172fadfebe7eb2364615eb1566c09f11d39bb0bb`.
- Attempts below use `transitc build/test`; isolated tests use the compatible
  Transit runtime supplied by the compiler package.

Re-audited on 2026-11-20: all 114 recorded attempts retain the same diagnostic
codes, stages, native causes, and source locations. Only the diagnostic definition
changed. The bootstrap build and its two native tests pass through `transitc`.

The exact checked commands and first-diagnostic fingerprints are in
[support.json](../tooling/support.json). `just check` compares the definition, code,
stage, native cause, source, line, and column, and refuses unexpected success,
another failure, changed pins, malformed output, or a process crash. It saves raw
diagnostics under `.transit/reports/`. Build/test commands return the native
failure code; matching a gap never turns a protocol test into a passing test.

## Requirements and evidence

| ID | Owner and target contract | Source or minimal reproducer | Current evidence |
| --- | --- | --- | --- |
| TP-01 | transitc workspace: native package membership and same-snapshot dependency inheritance; conflicts between workspace revisions reject. | [Workspace probe](../tests/compiler/workspace/build.transit), [GitHub entry](../packages/oauth-github/build.transit), [external consumer](../tests/consumers/external/build.transit.in). | `FROM WORKSPACE` is a parse refusal. External local fetch reaches the same refusal in `github/build.transit`. Transitive locking/offline rebuild and version-conflict behavior are not reached. |
| TP-02 | transitc source selection: lazy module/type/target re-exports and grouped targets; selected files/targets determine the build graph. | [OAuth entry](../packages/oauth/build.transit), [selection consumer](../tests/consumers/selection/build.transit). | Lazy re-export `FROM` refuses at parse; root `WORKSPACE` is UnsupportedBuildStatement. Selection assertions do not execute. |
| TP-03 | transitc types/lowering: structural and recursive types, collections, higher-order behavioral interfaces, nested routines, bounded loops and local mutation. | [Type probe](../tests/compiler/types/build.transit), [SCIM filter](../packages/scim/src/filter.transit). | `CREATE PUBLIC TYPE ... AS ROW` is UnsupportedSourceDeclaration. Existing nominal domains/interfaces are not claimed absent; this richer composition is unverified. |
| TP-04 | transitc + Transit catalog/authorization: private storage, stable schema/child bindings, reference exports, module invocation authority, serializable procedure composition. | [Private storage probe](../tests/compiler/protected/build.transit), [isolation suite](../tests/consumers/two-instances/isolation.test.transit). | Private declaration is RuntimePrivateOrUnsupportedDeclaration. Instance isolation, enforced encapsulation and migrations are not run. |
| TP-05 | transitc + Transit secrets: typed protected values, transactional protected handles, owner/purpose/expiry checks, revocation/current-secret guards, audited claim projection. | [OAuth client](../packages/oauth/src/client.transit), [exchange](../packages/oauth/src/exchange.transit). | Not reached. Requirements include handle storage and cross-module protected return types, not plaintext secret persistence. |
| TP-06 | transitc + Transit effects: finite Queue workflows, typed bounded HTTP sinks, original effect IDs, unknown outcomes, transactional acceptance and recovery. | [Effect probe](../tests/compiler/effects/build.transit), [exchange](../packages/oauth/src/exchange.transit). | SINK declaration is RuntimePrivateOrUnsupportedDeclaration. No dispatch/replay assertion has executed. |
| TP-07a | Transit primitives + compiler bindings: strict URI/form/JSON and JWS/JWK parsing, RSA-SHA256 verification, entropy/hash operations. | [OIDC validation](../packages/oidc/src/validation.transit). | Not reached. Native primitive signatures/taint contracts are proposed in target-language.md. |
| TP-07b | Transit primitives: bounded entity-free XML, safe node construction, raw DEFLATE, canonicalization/signature checking returning the exact signed node. | [SAML validation](../packages/saml/src/validation.transit). | Not reached; no generic full-SAML verifier is substituted for these operations. |
| TP-07c | Transit primitives: strict CBOR, P-256 point validation, ES256 DER verification, byte slices/endianness, public-suffix/origin validation. | [WebAuthn verification](../packages/webauthn/src/verification.transit). | Not reached. Authenticator format and protocol checks are Transit source. |
| TP-08 | transitc + Transit test host: clocks/entropy/owners/secrets, native crypto fixtures, sink mocks, bounded draining, crash/restart, compiler/closure assertions. | [Clock probe](../tests/compiler/testing/build.transit), package test suites. | SET TEST CLOCK produces UnsupportedBuildStatement. Successful bootstrap Table tests do not qualify these facilities. |
| TP-09 | transitc CLI + Transit SQL: canonical executable SQL, provenance, current authorization, offline install and explicit-basis upgrades. | Package default targets and consumer compositions. | SQL emission, installation, migrations, and protocol execution are not reached. |
| TP-10 | transitc + Document owner: typed versioned rows, revision reads, guarded updates, and revision-fenced policy acceptance. | [Document probe](../tests/compiler/documents/build.transit), [OAuth guards](../packages/oauth/src/guards.transit). | PUBLIC DOCUMENT refuses with RuntimePrivateOrUnsupportedDeclaration at 2:17. Revision operations are not reached. Direct SQL support is a separate surface. |
| TP-11 | transitc + KV owner: typed point values, absent insertion, revision-conditional claims, and authoritative expiry. | [KV probe](../tests/compiler/kv/build.transit), [SAML SSO](../packages/saml/src/sso.transit). | PUBLIC KV refuses with RuntimePrivateOrUnsupportedDeclaration at 2:17. Claim races and expiry are not reached. |
| TP-12 | transitc + native transaction coordinator: one decision across Table/Document/KV and Queue/Stream output/checkpoint, including protected handles and rollback. | [Mixed-state probe](../tests/compiler/mixed-state/build.transit), [SCIM store](../packages/scim/src/store.transit). | Document declaration refuses at 3:17 after a Table declaration. No cross-resource transaction has run. |
| TP-13 | transitc + Stream owner: typed ports, owner attribution, required consumers, fenced checkpoints, retained continuation, and protected progress under backpressure. | [Stream probe](../tests/compiler/stream-composition/build.transit), [OIDC validation flow](../packages/oidc/src/authentication.transit). | FROM STREAM refuses with InvalidSourceTemplate at 4:39 after Table/Stream declarations. Consumption, checkpoint atomicity and retention are not reached. |
| TP-14 | transitc query lowering + storage: authorized typed Views, relational module ports, constraints, consistent count/page reads, and Publications. | [Query probe](../tests/compiler/queries/build.transit), [SCIM reads](../packages/scim/src/reads.transit), [surface selection](../tests/consumers/surfaces/build.transit). | PUBLIC VIEW refuses with RuntimePrivateOrUnsupportedDeclaration at 3:17. Query/constraint/Publication behavior is not reached. |
| TP-15 | transitc + lifecycle: bounded native timers, explicit grants/activation, retained unresolved work, and protected-value destruction. | [Maintenance probe](../tests/compiler/maintenance/build.transit), [OAuth cleanup](../packages/oauth/src/maintenance.transit). | FROM TIMER refuses with InvalidSourceTemplate at 3:39. Cleanup and replacement behavior is not reached. |
| TP-16 | transitc + command/HTTP owners: typed command admission, original-request results, strict decoding, native response ownership, and current disclosure authority. | [Command/HTTP probe](../tests/compiler/command-http/build.transit), [OAuth binding tests](../packages/oauth/tests/http.test.transit). | FROM COMMAND refuses with InvalidSourceTemplate at 2:38. The later HTTP Source, response and decoder operations are not reached. |

The application-protocol expansion adds three focused requirements. Each probe
currently refuses the declaration at `root/build.transit:2:17` with
`RuntimePrivateOrUnsupportedDeclaration`; none reaches the later operations.

| ID | Target contract | Probe and authored consumer | Evidence |
| --- | --- | --- | --- |
| TP-17 | Native blob capabilities: durable offsets, bounded streaming append, lifecycle fencing, partial-write receipts, atomic retirement, and bounded HTTP/blob transfer. | [Blob probe](../tests/compiler/blob-streaming/build.transit), [tus server](../packages/tus/src/server.transit), [JMAP blobs](../packages/jmap/src/blobs.transit). | Declaration lowering refuses; offset, concurrency, and recovery tests not run. |
| TP-18 | Typed command-port maps, JSON argument/result adapters, independent child transactions, deadlines, and generic public error categories. | [Dispatch probe](../tests/compiler/command-dispatch/build.transit), [JSON-RPC dispatch](../packages/json-rpc/src/server.transit). | Declaration lowering refuses; dispatch and batching not reached. |
| TP-19 | Native SSE connection lifecycle, bounded buffering, reconnect/cancellation, and durable coalesced reconciliation. | [SSE probe](../tests/compiler/sse/build.transit), [JMAP Push](../packages/jmap/src/push.transit). | Declaration lowering refuses; connection behavior not reached. |

The [application protocol contracts](application-protocol-contracts.md) also
extend TP-05/06/07/08/12/15/16 with precise protected-value, retry, codec, HTTP,
maintenance, and test-host requirements. Their bodies remain behind the existing
entry refusals; no additional diagnostic is inferred from source design alone.

Detailed syntax and primitive contracts are in
[target-language.md](target-language.md). These are local upstream requirements;
no upstream issue or implementation is implied. Each compiler change should use
the linked source as a reproducer and update the requirement with actual evidence.
The new probes deliberately use public resources to distinguish their first
refusals from TP-04's private-storage blocker. Exact locations above refer to the
probe's `root/build.transit`. None of these first refusals proves that every later
construct is unsupported or that any protocol body has been checked.

## Support states and progression

| Surface | Resolution / parsing | SQL emission / installation | Tests |
| --- | --- | --- | --- |
| Bootstrap Table composition | Passed on the host when `just check` succeeds | Check-mode native preparation; separate `just build bootstrap` emits SQL | Two native tests pass when the check succeeds |
| Workspace and twenty package roots | Blocked at recorded first diagnostic | Not run | Not run |
| Independently rooted consumers | Blocked before closure assertions | Not run | Not run |
| External snapshot | Git source fetched; package parse blocked | Not run | Not run |

After an upstream pin update, re-run the exact recorded attempts. An unexpected
pass is a prompt to verify the next stage and replace the gap with a required
regression test. A later-stage failure needs a new reviewed record; it cannot
inherit a parser exception. Never auto-refresh fingerprints in CI. The checker
intentionally has no command to accept new failures.

Qualification still requires actual protocol tests, consumer closure/provenance
checks, installable SQL without source/compiler, frozen offline builds, stable
bindings across moves, and explicit state upgrades. Provider-specific live
qualification is separate from mocked tests; no live credentials or external
requests are used by this repository's checks.
