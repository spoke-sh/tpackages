# Application protocol package implementation plan

Status: **Implementation authorized; first target-language profiles authored — 2026-11-19.**

The twelve added roots now contain source, examples, and native tests. See the
[implementation contracts](application-protocol-contracts.md) for profile limits,
new native requirements, and the explicit federation peer profile. Executable
qualification remains blocked; no protocol suite has run.

Extend `tpackages` with nine application-layer protocol packages: CloudEvents,
Standard Webhooks, tus, JSON-RPC, WebSub, CalDAV, CardDAV, JMAP, and ActivityPub.
Applications must be able to select each package, and its useful public modules,
without installing the rest of the workspace.

MCP, its Apps extension, and frontend hosting are excluded. JSON-RPC remains an
independent protocol package. Service-specific APIs belong in `tintegrations`;
application interfaces and business policy belong in consuming applications.

This plan extends the [dataflow and state model plan](dataflow-refactor-plan.md)
and [package conventions](../packages/README.md). The existing eight packages
remain the baseline. Their implementations are unqualified on the current pins;
new source will likewise target the intended language even where compiler/runtime
support is incomplete. All twelve new package roots are registered with independent build/test targets.

## Proposed scope and dependency boundaries

Implement the following first profiles. A profile defines the supported role and
operations; the package name alone does not promise every protocol extension.
Public module names below are proposed API boundaries, not established syntax.

| Package | First profile and selectable modules | Required package dependencies |
| --- | --- | --- |
| `cloudevents` | Event envelope and JSON codec; HTTP binding; optional Stream adapters. | None. |
| `standard-webhooks` | Signing/verification; receiver; sender; optional HTTP ingress. | None; compose CloudEvents in the application when wanted. |
| `tus` | Resumable-upload server; core, creation, expiration, termination; HTTP binding. | None. |
| `json-rpc` | JSON-RPC 2.0 codec, client, server dispatch, optional HTTP transport. | None. |
| `websub` | Subscriber discovery, subscription lifecycle, verified content intake. | None. |
| `caldav` | Calendar client: discovery, queries, synchronization, conditional writes. | `webdav`, `icalendar`. |
| `carddav` | Address-book client: discovery, queries, synchronization, conditional writes. | `webdav`, `vcard`. |
| `jmap` | Core client and typed extension ports; optional Mail read/sync module. | None; JMAP has its own request protocol, independent of JSON-RPC. |
| `activitypub` | Bounded server-to-server federation profile; ActivityStreams codec; HTTP binding. | None. |

Propose three supporting roots alongside the nine requested roots:

- `webdav`: shared client protocol machinery used by both DAV packages.
- `icalendar`: independently selectable calendar format parsing and serialization.
- `vcard`: independently selectable contact format parsing and serialization.

This would add twelve roots, for twenty total. These supporting packages have
concrete wire contracts and consumers; there is no generic `protocol-utils`
package. Keep ActivityStreams as a selectable module inside `activitypub` initially.
CalDAV must not depend on CardDAV, or vice versa. Authentication is an explicit
application-supplied capability; these packages do not automatically import OAuth.

Use the existing `packages/<name>/{build.transit,src,tests,examples}` layout plus
each package's README. Export codec, stateful behavior, HTTP bindings, and optional
read Publications separately. Internal dependencies resolve from the consumer's
selected repository snapshot. Pure codec selection must create no state, effects,
routes, timers, or grants.

## Transit implementation model

Stateful APIs expose typed commands, named guards, declarative dataflows, committed
result Streams, and authorized Views. An accepted operation advances through
native continuations; callers do not poll and invoke a finishing procedure.
Functions handle bounded parsing and transformation. Small atomic helpers are
appropriate only when a mutation must join the caller's transaction.

The typical composition is:

```text
Command or optional HTTP Source
  -> decode and authorize
  -> atomic state admission
  -> native Queue/effect when a peer interaction is needed
  -> guarded result transition
  -> committed typed Stream
  -> application dataflow with a native checkpoint
```

A local command needs no Queue when one transaction suffices. Codec functions
need none of these stateful resources. Native HTTP response ownership determines
when a wire response can be issued; an internal admission event is not necessarily
a protocol success response.

| Construct | Ownership in this expansion |
| --- | --- |
| Versioned Document | Endpoint policy, negotiated capabilities, subscription intent, and structured calendar/contact/federated objects. Each field has one canonical owner. |
| KV | Expiring challenge context and bounded replay/deduplication claims that need point lookup and atomic insertion. |
| Table | Relational identity, unique delivery claims, indexed operation status, resource mappings, memberships, and synchronization cursors. |
| Private Queue | Native execution of accepted external work and bounded continuations. Never a package-built scheduler or outbox engine. |
| Typed Stream | Committed outcomes and changes with original owner/correlation, stable identity, and native consumer checkpoints. |
| Native blob capability | Upload bytes and large payloads; packages retain protected handles and protocol metadata rather than storing chunks in Tables or Streams. |
| View / optional Publication | Current authorized state and status, derived from canonical owners. |

Define resource ownership and transaction boundaries before source implementation.
For each instance, bind identity, policy, secrets, effect permissions, consumer
rights, and activation explicitly. Queued work retains the original caller and
accepted policy revision; current revocation and destination rules still apply
before dispatch or disclosure. Credentials and private payloads must not leak into
immutable event history; expose minimal metadata and protected references.

Separate logical message identity, protocol correlation, and native effect
attempt identity. Recover an interrupted attempt using its original native
identity. Where a protocol permits redelivery, schedule a distinct authorized
attempt while preserving the message identity and prior evidence. Never infer
remote exactly-once execution from a local transaction or correlation ID.

Specify ordering, expiry, retry budget, retention, and cleanup per profile. Dedup
claims must cover the supported delivery/replay horizon; finite retention must
state what happens after that horizon. Required Stream consumers protect progress
with native checkpoints and backpressure. Cleanup is bounded, respects references,
and preserves unresolved effects and evidence. Initial result history follows the
existing retained-history policy until native retention and gap handling qualify.

## Package implementation work

### CloudEvents

Target the [CloudEvents 1.0.2 specification](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md),
with wire `specversion` `1.0`, JSON event format, and the structured and binary
modes of its [HTTP binding](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/bindings/http-protocol-binding.md).
This is an event representation; it does not supply a delivery guarantee.

Implement selectable `Codec`, `Http`, and `Streams` modules. Decode and validate
required attributes, attribute types, extension names, content types, and the
distinction between JSON data and encoded binary data. Preserve supported unknown
extensions without letting them overwrite reserved attributes. Keep transport
metadata separate from the application event.

The codec owns no storage. The optional adapter maps committed application events
to envelopes and validated incoming envelopes to typed inputs. Applications bind
authorized event sources and decide payload schemas. If intake deduplication is
selected, atomically claim `(instance, authenticated source, event id)` with
admission; a claimed `source` URI alone conveys no authority.

Acceptance: round trips for JSON and binary data; absent versus null data;
invalid/missing attributes; header/body conflicts; unknown extensions; preserved
source/id identity; and a codec-only consumer with no state or HTTP resources.
Batch mode and non-HTTP transport bindings are deferred.

### Standard Webhooks

Target the current [Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md),
recording its exact commit during implementation because the document is mutable.
Implement its headers and signature inputs, HMAC `v1` and endpoint-bound asymmetric
`v2a`, timestamp validation, and overlapping-key rotation. Retries retain the
message ID and use a fresh attempt timestamp. Native primitives perform crypto.

Expose `Signatures`, `Receiver`, `Sender`, and `Http`. Endpoint Documents own
versioned policy and protected key references. Receiver admission verifies exact
body bytes before parsing, checks current trust, then atomically claims a scoped
message ID and emits an accepted event. Retain a payload commitment so a duplicate
ID with different content is refused. Acknowledge only durable admission.

Sender commands freeze payload identity and create a delivery record. Native
Queue dataflows sign, send, record receipts, and schedule bounded redelivery.
Preserve ambiguous attempts; permitted redelivery can still produce duplicate
remote processing. Endpoint policy determines deadlines, backoff, throttling, and
manual replay authority. An HTTP acknowledgement completes delivery, not the
consumer's business operation. Do not follow delivery redirects automatically.

Acceptance: official signature vectors; byte changes; wrong endpoint/key;
clock boundaries; concurrent duplicates; rotation; revoked endpoints; response
loss after remote acceptance; retry exhaustion; and recovery across admission,
dispatch, and receipt commits. Include independent sender/receiver examples and
an optional application composition carrying CloudEvents. Provider-specific
webhook schemes remain outside this package.

### tus

Implement a server for [tus 1.0.0](https://tus.io/protocols/resumable-upload),
including core offset handling and the creation, expiration, and termination
extensions. Advertise only implemented extensions. Authentication and upload
authorization come from the application.

Expose upload commands, authorized status Views, lifecycle Streams, and an optional
HTTP binding. A Document owns immutable upload metadata and owner policy; a Table
owns lifecycle state and the binding to native blob storage. The blob capability
owns durable bytes and their committed offset. Any indexed offset is a fenced
projection, never a second independent authority.

The PATCH flow validates ownership and expected offset, streams a bounded body to
native storage, and commits the accepted offset before responding. Require a
native contract that coordinates blob acceptance with lifecycle fencing; a
Document/Table transaction alone cannot make external blob writes atomic. Expiry,
termination, and concurrent PATCH requests must not resurrect an upload.
Completion emits once only after all declared bytes are durable. Interrupted
PATCH requests can leave a durable partial offset, which HEAD must report.

Acceptance: offset mismatch, parallel writes, disconnect after partial acceptance,
unknown write outcome, zero-length uploads, size limits, expiry, termination races,
and completion recovery. Checksum and concatenation extensions are deferred;
checksum support would require whole-chunk rollback on mismatch, beyond ordinary
partial-PATCH semantics. Storage drivers, virus scanning, and file-processing
workflows belong to the runtime or application.

### JSON-RPC

Implement [JSON-RPC 2.0](https://www.jsonrpc.org/specification): requests,
notifications, responses, standard errors, and batches. Request IDs correlate
responses; they do not confer idempotency. Missing IDs and explicit null IDs have
different meaning. Batch members are independent operations, not one transaction.

Expose `Codec`, `Client`, `Server`, and optional `Http`. Applications supply typed
method-to-command bindings with parameter/result codecs and invocation authority.
A declarative dispatch flow validates, routes, and correlates command results;
it must not become a procedural interpreter of arbitrary application functions.

Use state only for in-flight work that needs durable continuation. Tables own
correlation and deadlines; Queues own outbound calls; Streams expose local call
outcomes. Define a bounded HTTP transport profile, including response ownership,
deadlines, status codes, and notification handling. A local accepted command is
not a successful RPC result. Timeouts preserve uncertain remote outcomes, and
automatic replay requires an explicit method-level safety contract.

Acceptance: malformed requests, standard error codes, named/positional parameters,
ID type preservation, explicit null IDs, valid notifications with no response,
empty/mixed batches, out-of-order results, duplicate/unknown peer response IDs,
and restart during a call. Bound batch size and concurrency. WebSocket sessions,
progress extensions, dynamic application discovery, and MCP are excluded.

### WebSub

Implement the subscriber role in the [2026 WebSub Recommendation](https://www.w3.org/TR/2026/REC-websub-20260602/):
discovery, subscription/unsubscription, intent verification, lease renewal, and
content distribution. WebSub uses its own signature contract, independent of
Standard Webhooks.

Expose `Discovery`, `Subscriber`, and `Http`. Documents own desired subscriptions
and approved hub/topic policy; KV holds pending verification context; Tables own
active lease generations. Dataflows discover, request a subscription, verify the
callback, activate the lease, and renew through native timers. A successful POST
alone does not activate a subscription. Bind challenges to the intended operation;
renewal must not erase a still-valid subscription before replacement verification.

Use fresh capability callbacks for replacement leases and unique protected
secrets. Verify exact content bytes with an allowed signature algorithm. Serve
challenge responses as bounded safe content with `nosniff`. Emit protected content
references and lease outcomes into Streams. Notifications carry no universal
event ID: do not discard legitimate repeated publications merely because their
content hashes match.

Acceptance: HTTP/XML/HTML discovery precedence, invalid hubs/topics, unsolicited
verification, safe challenge reflection, forged or missing signatures, renewal
races, old callbacks, expiry, and restart between request and verification.
Apply native destination and redirect restrictions during discovery. Publisher
and hub roles are deferred; feed parsing and downstream content policy remain
application concerns.

### Shared DAV and format support

Build `webdav` before the two DAV clients. Its `Codec`, `Client`, and `Sync` modules
cover bounded XML, property discovery, per-resource/per-property multistatus
results, conditional resource operations, and negotiated collection synchronization.
The protocol bases are [WebDAV, RFC 4918](https://www.rfc-editor.org/rfc/rfc4918.html)
and [collection synchronization, RFC 6578](https://www.rfc-editor.org/rfc/rfc6578.html).

Documents own approved discovery/capability snapshots. Tables own resource
mappings, ETags, cursors, and staged enumeration generations. Use opaque server
tokens, scoped to account and collection. Apply each page's changes and durable
continuations atomically with cursor advancement; never skip unfetched content by
advancing only the cursor. Invalid sync tokens trigger a bounded rescan. An
incomplete listing cannot establish that unseen resources were deleted.

Native effects perform network requests. Validate returned hrefs and redirect
destinations before attaching credentials. Reject DTDs and external/custom entity
expansion; bound document depth, property counts, and response size. Surface
conditional-write conflicts and unknown write outcomes for reconciliation; do not
automatically overwrite remote changes. No DAV server or locking implementation
is included in this first profile.

Implement pure `icalendar` and `vcard` codecs with unfolding/folding, escaping,
typed values, unknown-property preservation, and bounded parsing. Keep format
versions explicit. Use [iCalendar, RFC 5545](https://www.rfc-editor.org/rfc/rfc5545.html),
[vCard 3, RFC 2426](https://www.rfc-editor.org/rfc/rfc2426.html), and
[vCard 4, RFC 6350](https://www.rfc-editor.org/rfc/rfc6350.html).
Parsing recurrence/timezone definitions does not require shipping a recurrence
expansion engine. Preserve originals and apply explicit edits without losing
unrecognized fields.

Acceptance: mixed multistatus success/failure, truncated sync pages, invalid tokens,
concurrent remote edits, failed rescans, hostile hrefs/XML, multiline and Unicode
format fixtures, extension preservation, and standalone codec selection.

### CalDAV

Implement a client profile of [CalDAV, RFC 4791](https://www.rfc-editor.org/rfc/rfc4791.html):
principal/calendar discovery, calendar queries, multiget, conditional CRUD, and
collection sync when supported. Support calendar object interchange while making
the initial typed editing API focus on VEVENT. Preserve other valid components;
do not silently rewrite components the typed editor does not understand.

Expose `Client`, optional `Mirror`, and read Views. The client composes `webdav`
and `icalendar`; the mirror stores authoritative fetched representations in
Documents, with derived indexes and remote version mappings in Tables. Commands
request remote edits; accepted local intent and confirmed remote state are
separate records. Dataflows handle discovery, query, fetch, conflict, and commit
before emitting calendar change Streams.

Delegate time-range filtering to the server in this profile. Preserve recurrence,
exceptions, timezone definitions, and all-day versus timed values. Do not claim
local occurrence expansion, scheduling/invitations, or calendar server support.

Acceptance: discovery and capability limits, all-day/timezone/recurrence round
trips, query and multiget responses, incremental sync and rescan, conditional-write
conflicts, deletion races, and unchanged fields surviving an edit. Demonstrate a
calendar-only consumer and a stateless query consumer without a mirror.

### CardDAV

Implement a client profile of [CardDAV, RFC 6352](https://www.rfc-editor.org/rfc/rfc6352.html):
address-book discovery, queries, multiget, conditional CRUD, and negotiated sync.
Support vCard 3 interchange and vCard 4 where advertised by the peer; do not assume
vCard 4 is accepted everywhere.

Expose `Client`, optional `Mirror`, and read Views, composing `webdav` and `vcard`.
Documents own fetched contact representations; Tables own collection/resource
identity, remote versions, and derived indexes. Commands admit edits and sync
requests; dataflows reconcile remote results and emit committed contact changes.
Remote href, contact UID, and application person identity remain distinct.

Acceptance: multiple address books, repeated properties and parameters, Unicode,
embedded/linked data limits, negotiated format versions, extension preservation,
partial results, sync-token invalidation, conflicting writes, and interrupted
rescans. Neither a partial page nor a transient error may delete unobserved
contacts. Avoid automatic contact merging, enrichment, or CRM field mappings.
Provide a contact-only consumer and a combined CalDAV/CardDAV consumer sharing
only the DAV protocol machinery, with independent accounts and resource owners.

### JMAP

Implement a client for [JMAP Core, RFC 8620](https://www.rfc-editor.org/rfc/rfc8620.html):
Session discovery, capabilities/accounts, method calls and responses, result
references, state tokens, and bounded blob transfer. Model extensions with typed
method ports. Add a separately selected Mail module for Mailbox/Email metadata
query, retrieval, and change synchronization from
[JMAP Mail, RFC 8621](https://www.rfc-editor.org/rfc/rfc8621.html).

Expose `Core`, `Mail`, optional `Sync`, and optional `Push`. Session Documents own
validated capabilities and endpoint policy; Tables own account/type cursors and
call status. The optional Mail mirror uses Documents for fetched records. Queued
calls produce per-method outcomes; a successful HTTP response does not make every
method successful. Commit changes and their checkpoint together. Handle
`cannotCalculateChanges` by rebuilding a bounded snapshot before retiring unseen
records. State strings are opaque and scoped, not numeric versions.

Push uses a native SSE capability to trigger reconciliation; it is not the sole
source of record truth. Core selection must not instantiate Mail state, push
connections, or domain-specific methods. Native blob handles avoid materializing
large transfers in ordinary state.

Acceptance: capability limits, account separation, result references, mixed method
errors, paginated changes, state mismatch, resnapshot recovery, push reconnect,
session endpoint changes, and Core-only selection. Mail submission, a mail server,
full MIME processing, and domain-specific UI are deferred.

### ActivityPub

Implement a documented server-to-server profile of
[ActivityPub](https://www.w3.org/TR/2018/REC-activitypub-20180123/), with selectable
[ActivityStreams 2.0](https://www.w3.org/TR/activitystreams-core/) codecs. Start with
actor/object retrieval, paginated inbox/outbox collections, delivery, and typed
Create/Update/Delete, Follow/Accept/Reject, and Undo flows. Start with Person/Service
actors and Note/Document objects. Document unsupported activity and object types
explicitly.

Before implementing federation handlers, select a concrete peer-authentication
profile and named interoperability peer; this is a qualification dependency, not
a new authentication-package proposal. ActivityPub does not mandate one universal
federation authentication mechanism. Require verified actor/key/endpoint binding
through native security capabilities. Do not claim Mastodon compatibility merely
from implementing the W3C document.

Documents own actor/object representations and tombstones; Tables own activity
identity, inbox membership, follow relationships, and delivery status. Atomic
intake verifies authority and deduplicates activity IDs before emitting accepted
activities. Application commands decide follow approval, publication, and policy.
Native Queue flows perform bounded recipient expansion and delivery, preserving
activity identity across retries. A remote acknowledgement is not proof of
display, moderation acceptance, or human readership.

Use a pinned, bounded JSON-LD context profile; arbitrary remote context fetching
is excluded. Apply destination restrictions to actor/object resolution and keep
private recipients out of public representations and result Streams.

Acceptance: authenticated ownership, forged updates/deletes, duplicate activities,
out-of-order state changes, follow/undo correlation, pagination, private recipient
handling, inaccessible objects, blocked peers, delivery recovery, and native
backpressure. Client-to-server APIs, HTML rendering, social application policy,
and broad ecosystem extensions are excluded from this first profile.

## Compiler and runtime requirements

Continue using the pinned Transit/transitc output artifacts and existing five Just
tasks. This work does not introduce Zig, another language implementation, a custom
executor, or per-protocol repository task commands.

The following are candidate requirements to investigate, not newly observed
compiler failures. Reuse existing contracts where sufficient; extend the
[language proposal](target-language.md) and [requirement ledger](compiler-requirements.md)
only with precise contracts, minimal probes, and actual diagnostic evidence.

| Capability to establish | First consumers | Existing requirement area |
| --- | --- | --- |
| Strict raw-byte HTTP input/output, headers, method dispatch, deferred response ownership, bounded streaming. | Webhooks, tus, JSON-RPC, WebSub. | TP-06, TP-16. |
| Native blob append/offset/fencing, lifecycle coordination, partial acceptance, and recovery. | tus; later JMAP transfers. | New blob contract alongside TP-06/TP-12/TP-16. |
| Protected HMAC/Ed25519 operations, exact signed-byte handling, key rotation. | Standard Webhooks, WebSub. | TP-05, TP-07. |
| Bounded XML/HTML discovery, DAV XML handling, line-based codecs, controlled JSON-LD contexts. | WebSub, DAV, ActivityPub. | TP-03, TP-07. |
| Native timers, retry scheduling, bounded fanout, policy fencing, network destination restrictions. | Webhooks, WebSub, DAV, ActivityPub. | TP-04, TP-06, TP-15. |
| SSE lifecycle, reconnect/cancellation, bounded buffering, authenticated endpoint changes. | JMAP Push. | TP-06, TP-16; separate native connection contract if needed. |
| Atomic state/claim/result/checkpoint commits and staged synchronization recovery. | Stateful modules throughout. | TP-10 through TP-14. |
| Native test peers, binary bodies, partial I/O, concurrent requests, clock and crash injection. | Protocol qualification throughout. | TP-08. |

Do not label downstream stages unsupported merely because an earlier declaration
refuses. Record “not reached” accurately. A recorded refusal is not a passing
protocol test. Keep upstream pin changes separate from behavioral changes and
re-audit existing packages if pins change.

## Delivery sequence

Each wave produces target-language source, public composition examples, native
tests, profile documentation, and evidence of reached or blocked stages. Compiler
gaps may leave executable qualification pending without preventing later source
waves. All nine requested profiles belong to this plan; deferred extensions do not.

| Wave | Deliverable | Review/acceptance checkpoint |
| --- | --- | --- |
| 0 | Freeze protocol references and profiles; document API ports, canonical state, identities, retry/expiry rules, and native capability probes. | Confirm the three supporting roots, client/server roles, and ActivityPub peer profile. No invented compiler evidence. |
| 1 | CloudEvents and Standard Webhooks, each independently consumable, plus their application composition. | Pure codec selection; exact-byte verification; committed intake; visible redelivery semantics. |
| 2 | tus server and native blob contract/probes. | Concurrent offset and lifecycle design; partial-write and completion recovery tests authored. |
| 3 | JSON-RPC client/server and WebSub subscriber. | Typed command dispatch, notification semantics, lease verification, and automatic renewal. |
| 4 | `webdav`, `icalendar`, `vcard`, followed by CalDAV and CardDAV clients/mirrors. | Shared dependency selection; conditional writes; safe incremental sync and rescan. |
| 5 | JMAP Core, optional Mail read/sync, and optional Push. | Core-only selection, per-method errors, account isolation, and checkpoint recovery. |
| 6 | ActivityStreams codec and scoped ActivityPub federation. | Explicit peer/authentication profile, authority checks, privacy, fanout, and delivery recovery. |
| 7 | Cross-package consumer fixtures, closure/provenance checks, compatibility documentation, and qualification reports. | Each package's supported, blocked, and untested surfaces are independently visible. |

For each implementation wave, register completed package roots and grouped targets
in `build.transit`, extend consumer fixtures and structural checks, and update
READMEs. Integrate native tests with `just test <package>` and examples with
`just build <package>`. Keep `just check` strict about observed compiler gaps;
never bulk-accept failures or weaken existing tests to make the expansion green.

## Consumer and qualification acceptance

Add independently rooted consumers for every package and supporting codec, plus:

- CloudEvents over Standard Webhooks, with no compulsory dependency in either core.
- tus completion consumed by an application flow, with no caller-driven finish step.
- JSON-RPC methods bound to application commands, with no MCP or frontend resources.
- WebSub content intake consumed through a native checkpoint.
- CalDAV alone, CardDAV alone, and both with independent state and shared DAV code.
- JMAP Core alone, Core plus Mail, and optional Push activation.
- ActivityPub with explicit application policy ports and a named federation peer.

Check selection at module and package level: unused state, HTTP bindings,
Publications, timers, credentials, and dependencies must be absent from emitted
artifacts. Exercise two instances and tenants; no shared claims, resource names,
queues, or authority should arise accidentally.

Reuse frozen external-consumer and provenance checks. Test same-snapshot transitive
dependencies, rejected conflicting revisions, offline rebuilds, and installation
from emitted artifacts. Keep stable resource identity across source moves. Only
test upgrades against real prior executable artifacts with an explicit migration
basis; do not invent a historical schema while compilation remains blocked.

Native protocol suites cover the package cases above plus size/concurrency bounds,
unauthorized access, revocation during queued work, cleanup races, rollback,
crash/restart, consumer lag, and uncertain external effects. Use pinned standard
vectors where available, with provenance/license notes, and authored deterministic
peer fixtures. Live interoperability checks are separate, opt-in targets within
the existing task surface; record peer versions and the exact tested profile.

Completion has two independently reported milestones:

1. **Source authored:** all nine first profiles and three support packages have
   reviewed target-language implementations, examples, tests, dependency boundaries,
   and accurate compiler/runtime requirements. Tests may remain blocked.
2. **Executable qualification:** builds, emitted SQL, native protocol/recovery
   tests, consumer selection, and relevant peer interoperability actually pass.
   Publish support claims per profile, module, and pinned toolchain only then.

The main review choices are the twelve-root layout, the proposed first roles and
extension limits, delivery order, and the concrete ActivityPub interoperability
profile to select in wave 0. The dataflow/state model and selective-consumer model
remain the established direction.
