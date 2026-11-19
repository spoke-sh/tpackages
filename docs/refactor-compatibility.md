# Dataflow API and state compatibility

This refactor changes the target-language API for every authored package. None has
shipped a qualified executable release, so there is no parallel legacy engine or
compatibility poller. These mappings describe source changes, not an executed
migration. Package roots, dependency boundaries, repository pins, and the five
Just tasks remain the same.

## Public interfaces

| Before | Current composition |
| --- | --- |
| OAuth/provider `begin` and `callback` procedures | `begin_authorization` and `accept_callback` command dataflows. The latter admits work and returns an operation reference. |
| OAuth one `exchange` flow and public `jobs` handle | Private code, refresh, and revocation Queues with separate flows. Authorize/activate the core; consume `completions` or read `status`/`outcome`. |
| OAuth `refresh` / `revoke` procedures | Same names as commands, preserving generation fencing and immediate denial of local use during revocation. |
| OAuth `credential` record containing protected handles | Safe metadata from `credential` / `credential_metadata`; separately authorized `token_material` for protected use. No ordinary token-bearing event/publication. |
| OIDC `begin`, `callback`, and consumer-driven `finish` | `begin_authentication`, `accept_callback`, and an installed required consumer of OAuth results. `completions` carries Verified/Refused/Unknown; `outcome` only observes. |
| Explicit application key-refresh-and-finish loop | One missing-key refresh inside the OIDC validation flow, retained under the original effect ID and checkpoint. Other validation errors refuse. |
| SAML `begin` / `finish` | `begin_sso` / `accept_assertion`, atomic request/replay claims and identity Stream append. |
| WebAuthn finish methods | `accept_registration` / `accept_authentication`; begin commands retain their names. Credential updates, challenge consumption and result emission share one transaction. |
| Application calls to `prune` | Bounded native maintenance inputs. Logical expiry is checked during admission; physical cleanup is separate. |
| SCIM catch-all `request` procedure | Explicit discovery/list/get/create/replace/patch/delete commands; optional HTTP Sources own route decoding and SCIM error encoding. |
| SCIM Store `get` / materializing `list` | Typed `resources` query View and `changes` Stream; inline atomic `insert`, `replace`, `remove` helpers. Policy additionally supplies `can_read`. |
| WebAuthn Policy only has ceremony guards | Add `can_read_credential` for metadata disclosure. Ceremony guards continue to authorize mutations. |

`Http` is optional in all eight packages; OAuth adapters reuse the core binding.
The examples export `default` for core/result consumption and a separate `http`
target where appropriate. SCIM's main example deliberately selects its HTTP
module; the core remains independently selectable. OAuth, OIDC, and WebAuthn also
export optional authorized Publications. Pure validator targets select no state or
transport. Public imports never grant rights or activate resources.

Configuration commands (`set_enabled`, `configure_trust`, `configure_policy`)
require current native configuration rights and an expected Document revision.
Ordinary command invocation does not grant configuration or protected-use rights.
Examples name role settings; they do not define permissive production roles.
HTTP activation additionally requires the application's native identity binding,
including a stable pre-authentication owner where the application allows login.

## Canonical state and upgrade requirements

| Existing responsibility | Refactored owner | Required migration proof |
| --- | --- | --- |
| OAuth challenge Table | Challenge KV plus ID/deadline index Table | Preserve state commitment, original owner/browser commitment, protected verifier, expiry, claim status and operation correlation; bind an approved policy revision explicitly. |
| OAuth work-kind Queue | Separate code/refresh/revocation Queues | Preserve original accepted operation/effect identity and native continuation. Do not enqueue a pending or unknown operation as fresh work. |
| OAuth credential/operation records | Credential and operation Tables plus policy Document and completion Stream | Preserve IDs, generations, protected references, local disablement, terminal outcomes and unknown receipts. Historical results must not be backfilled as new authorization events. |
| OIDC discovery and nonce/result records | Versioned metadata/JWKS Document, nonce KV and result Table/Stream | Preserve issuer/endpoints, freshness, nonce, credential generation, accepted revision and original OAuth correlation. Bind a required consumer checkpoint to a proven cut. |
| SAML request/replay records | Separate request/replay KV plus expiry indexes; trust Document | Preserve browser binding, consumed claims, issuer/assertion replay commitment, accepted trust revision and final validity including skew. |
| WebAuthn challenges and credentials | Challenge KV/index; policy Document; credential Table | Preserve account/credential IDs, key, signature counter, backup state, consumed challenges and accepted policy revision. Never reset counters during conversion. |
| SCIM JSON resource Table | Identity/username/membership Tables plus attribute Documents | Split fields by owner; preserve IDs, ETags/timestamps, case-insensitive uniqueness, referential integrity and complete observable resource content. |

Document seeds use insert-if-absent semantics; re-evaluating constructor source
must not overwrite live mutable policy. Changing constructor trust/endpoints is
an installation change that needs an explicit reviewed definition basis.

Each conversion must participate in native migration/replacement against the
actual prior definition graph. Preserve instance/child bindings even if source
paths or aliases move. Either prove that pending work resumes under its original
definition and effect receipts, or refuse cutover until that work is resolved.
Unknown outcomes remain unknown; cleanup cannot turn them into redispatchable work.

There is no generated migration SQL here: neither old nor new protocol definition
can yet be compiled on the pins. Once executable, retain a real old artifact and
test upgrading seeded consumed challenges, replay claims, active credentials,
pending and unknown effects, SCIM relationships, and consumer positions. Test
rollback as well as successful cutover before qualifying an upgrade.

## Results, retention and delivery

Work/result Streams have immutable typed events, stable original event identities,
explicit partitions, and unlimited retention in this profile. Native required
consumer checkpoints commit with terminal mutations/output. Resource exhaustion
must backpressure or refuse admission atomically, never lose a queued continuation
or emit a result independently of state. No custom outbox or retry ledger exists.

The initial unlimited policy has no retention-gap path. A future bounded policy
must protect required consumers and expose gaps/resnapshot for optional observers
before it is enabled. Resnapshot reconstructs an authorized read model; it cannot
recreate an expired authentication grant or cause effects to be dispatched again.

Result history is evidence of a completed protocol decision, not perpetual
authentication authority. Current native rights and owner filters apply at every
read/consumption. Applications check identity expiry and current session/account
policy when using historical claims. Protected token retrieval additionally checks
current policy, credential status, purpose and expiry. Unknown outcomes never
authorize a credential or identity.

HTTP responses complete at command acceptance. OAuth/OIDC callback Sources return
202 with an operation reference; Stream consumers advance the application.
The native command owner retains the original-request result across response loss.
A new request presenting a consumed challenge is a distinct replay and refuses.

## Qualification

The native bootstrap and repository diagnostic checks can run now. Protocol,
binding, race/recovery, application Store, and selective consumer suites are
authored native tests but blocked before their bodies are checked. See the
[ledger](compiler-requirements.md) for exact observed refusals. Passing the gap
audit does not qualify protocol behavior, selected output, deployment, offline
rebuild, migration, or live provider compatibility.
