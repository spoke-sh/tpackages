# Application protocol source and native contracts

The twelve roots added by the [implementation plan](application-protocol-plan.md)
contain target-language source, examples, and native tests. They are unqualified.
The pinned compiler rejects their public entries before checking implementation
bodies. The three new native probes also stop at declaration lowering; later
capabilities are **not reached**, rather than individually proven unsupported.

## Profiles and public selection

| Root | Authored surface | Deliberate limits |
| --- | --- | --- |
| `cloudevents` | `Codec`, structured/binary `Http`, source-bound `Streams`. | CloudEvents wire 1.0 / specification 1.0.2. No batch or non-HTTP binding. Stream payloads must be approved for retained history. |
| `standard-webhooks` | `Signatures`, `Receiver`, `Sender`, `Http`. | Specification [3d65b18](https://github.com/standard-webhooks/standard-webhooks/blob/3d65b1824b6697f05a5a4584e7062bd23512fc8e/spec/standard-webhooks.md); HMAC v1 and endpoint-bound Ed25519 v2a. 1 MiB bodies, 300-second timestamp window, retained receiver claims. Sender permits up to twelve attempts within three days. |
| `tus` | `Server`, optional `Http`, protected completed-blob access. | Version 1.0.0 core, creation, expiration, termination. Declared upload lengths; no checksum, concatenation, deferred length, or creation-with-upload. |
| `json-rpc` | `Codec`, `Server`, `Client`, `Http`. | Version 2.0; HTTP POST profile, 128-member inbound batch, 30-second method deadline. No retry inferred from an RPC ID. No MCP. |
| `websub` | `Discovery`, `Subscriber`, `Http`. | 2026 subscriber profile; HTTPS destinations explicitly allowed, signed content using SHA-256 or stronger HMAC. No publisher or hub. |
| `webdav` | `Codec`, `Client`, `Requests` port, optional `Sync`. | Same-origin DAV requests, conditional writes, 1 MiB responses and at most 1,000 resources per response. Incremental sync or complete bounded PROPFIND fallback. No server or locks. |
| `icalendar` | Pure `Codec`. | Bounded structural iCalendar 2.0 parsing and serialization, preserved recurrence/timezone/extension fields, explicit VEVENT summary editing. It does not expand recurrence or implement scheduling. |
| `vcard` | Pure `Codec`. | vCard 3/4 structural interchange, preserved unknown fields and parameters, formatted-name editing. It does not interpret every property extension or merge people. |
| `caldav` | `Client`, optional `Mirror`. | Discovery, VEVENT range queries, multiget, conditional CRUD, optional DAV sync. No server, invitation processing, or local occurrence expansion. |
| `carddav` | `Client`, optional `Mirror`. | Discovery, contact queries, multiget, conditional CRUD, optional DAV sync; vCard 4 writes require advertised support. No CRM mappings or contact merging. |
| `jmap` | `Core`, `Mail`, `Sync`, `Push`, `Blobs`. | Core request protocol, Mailbox/Email metadata read/sync, native SSE and bounded blob transfers. No submission, MIME engine, or mail server. |
| `activitypub` | `Codec`, `Signatures`, `Federation`, `Http`. | Configured peers and bounded ActivityStreams context; Create/Update/Delete, Follow/Accept/Reject, Undo of Follow. Note/Document object IDs live below their actor's `/objects/` namespace. No client-to-server API or general ecosystem compatibility claim. |

All modules use public package entries. CalDAV selects `webdav` and `icalendar`;
CardDAV selects `webdav` and `vcard`. JMAP does not select JSON-RPC. CloudEvents and
Standard Webhooks compose in the application without requiring each other.
Examples use explicit deployment roles; credentials and native storage are supplied
through runtime settings, with no credentials or active network access in this repo.

## State and authority

Documents own mutable endpoint policy, discovery/session state, subscription
intent, and structured mirrored objects. Tables own identity, versions, cursors,
relationships, and indexed lifecycle state. KV owns point claims and verification
context. Effects and their scheduling belong to native Queues; Streams contain
committed outcomes and use durable consumer checkpoints.

DAV and JMAP mirrors key objects by owner and remote identifier. Remote ETags,
opaque synchronization tokens, and local Document revisions have distinct roles.
Replacement snapshots use a fresh generation so records seen before a reset cannot
survive deletion merely because an earlier page touched them. Failed or incomplete
enumeration never proves absence. Snapshot deletion is limited to 1,000 candidates
per completion; larger reconciliations refuse atomically and need a wider native
maintenance profile before qualification.

Protected bodies remain private. `INFINITY` requests explicit retained protected
storage, with current owner/purpose/grant checks on every read; it does not imply
permanent authority. Required consumers cannot lose payloads through an arbitrary
seven-day timeout. Deployment quotas can refuse admission atomically. Any future
finite retention policy needs checkpoint-aware cleanup and a documented gap path.
ActivityPub's public activity Document is a derived, sanitized projection, written
only in the same publication transaction as its canonical activity. Private inbox
history and blind recipients are never exposed by that projection.

Native maintenance needs a restricted owner-continuation capability.
`PROTECT_FOR_OWNER` and `ENQUEUE ... AS OWNER` accept only an owner already recorded
by an authorized admission in the same instance. They require maintenance grants,
retain provenance, and cannot authorize arbitrary caller impersonation. WebSub
renewal uses this capability; its helper procedure only joins an existing atomic
transaction and performs no external effects.

## Effects, replies, and retries

`EXECUTE ... EFFECT id ON REPLAY OBSERVE ONLY` is one native attempt. The runtime
freezes the first dispatched request and observes its recorded result on recovery;
it must not rebuild or send a different request under the same ID after key or
clock changes. Current policy still controls new dispatch and disclosure. The
owner exposes known, refused, and unknown outcomes without discarding ambiguous
evidence. A synchronous command dataflow may await this durable continuation;
network I/O never executes inside `BEGIN ATOMIC`.

Webhook and ActivityPub redelivery is explicitly permitted by their profile and
creates a new attempt while preserving logical message/activity identity. Prior
receipts survive. RPC and DAV mutations do not receive this automatic permission.
`ENQUEUE ... AVAILABLE AT` is native scheduling with bounded policy, not a package
retry engine. Expired or revoked work refuses without silently changing identity.

HTTP bindings add strict unique-header/query access, raw/protected bytes, and
native response ownership. `application_endpoint` means an explicitly bound local
endpoint principal; it never trusts an owner header from the peer. Signature and
challenge guards still run inside that boundary. Binding refusal statuses are
protocol-specific. RPC responses await actual method results, while webhook
acknowledgement follows durable admission.

## Blob storage (TP-17)

`BLOB_STORE`, `BLOB_REF`, and `BYTE_STREAM` are native capabilities. `BLOB_CREATE`
joins admission; `BLOB_DURABLE_OFFSET` reads committed byte progress. Append accepts
an expected offset, byte limit, original effect ID, and a lifecycle-row fence.
Every durable prefix must be fenced against concurrent append, termination, and
expiry. The returned receipt distinguishes a complete request, a committed prefix,
and an unknown observation. HEAD reports durable progress even after disconnect.

`BLOB_FENCE_AND_RETIRE` commits retirement with the lifecycle transition. Late
writers cannot recreate bytes. Native reclamation can run later, without making
bytes readable again. Blob progress and completion-event publication require
recoverable receipts; an ordinary Table transaction is not a substitute for the
native blob coordinator. `EXECUTE HTTP DOWNLOAD/UPLOAD` applies equivalent bounded
streaming, authorization, redirect, ownership, and replay contracts for JMAP.

## Typed command dispatch (TP-18)

`COMMAND_BINDINGS('name' => command)` is a compile-time map of typed command ports.
The compiler supplies bounded named/positional JSON adapters from each command's
schema. `HAS_COMMAND` is a pure lookup. `DISPATCH COMMAND` enforces invocation
authority, original owner, a native child continuation, and a deadline. The
generic `COMMAND_ERRORS` result contains stable public categories; JSON-RPC maps
them to wire errors in package source. There is no native JSON-RPC interpreter.

Each batch member owns an independent transaction. A deadline is not evidence
that remote work did not happen. Valid notifications execute through the same
guarded path and suppress responses, including errors from the invoked method.

## Connections and primitives (TP-19, TP-07)

Native SSE bindings own reconnect, cancellation, bounded buffering, and endpoint
authorization. JMAP Push treats reconnect/state notifications as reconciliation
triggers; Sync remains authoritative. A reconnect during an existing sync must
leave a durable coalesced refresh request, so the notification cannot disappear
between the last page and the completion transaction.

The new source also requires bounded generic operations, with compiler signatures
and secret-taint propagation: HTTP Link and Structured Field parsing, URI-template
expansion, strict XML tree access/building, bounded HTML head-link parsing, JSON
accessors/result errors, quoted-delimiter splitting, Unicode-safe byte-counted
line folding, HMAC SHA-256/384/512, Ed25519, and digest/signature encoding. JSON
and XML duplicate/ambiguity rejection stays explicit. Date, URI, header, and key
validation must reject controls and oversized input. These primitives perform
individual operations; the protocol workflows remain Transit source.

## Federation profile and tests

The first ActivityPub peer profile signs POST with
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) Ed25519 over `@method`,
`@target-uri`, `content-digest`, and `content-type`, plus explicit creation/expiry,
key ID, and algorithm parameters. Its SHA-256 content digest follows
[RFC 9530](https://www.rfc-editor.org/rfc/rfc9530.html). Trust is configured per actor
and inbox, rather than taken from an incoming key URL. The fixed context is
`https://www.w3.org/ns/activitystreams`; remote context loading is refused.

`tpackages-federation-peer-v1` is an authored deterministic native test peer, not a
claim of interoperability with a deployed server. Broader signature formats,
discovery, delegation, vocabularies, and peer policies need separate profiles.

Tests use case-local crypto keys, partial byte streams, native effect observations,
controlled clocks, concurrent commands, crash/restart, and resource-budget
injection. `TEST_ED25519_KEYPAIR`, `TEST_BYTE_STREAM`, and `SECRET_LITERAL` are
test-only fixture operations. `TRY` returns the language's typed `RESULT` and
cannot catch a compiler failure as a protocol refusal. Stream/effect count helpers
inspect native test evidence. Concurrent command capture records independent
native results; method-filtered sink mocks provide deterministic DAV peers. Native
test activation must bind isolated test blob/auth capabilities for declared runtime
settings and refuse any unresolved external capability. No protocol behavior is
implemented in Python.

Independent consumers and cross-package compositions assert actual compiler
closures once reachable. Existing frozen external-source, offline/provenance,
and migration obligations remain. No live peer credentials, historical executable
migration basis, or executable protocol conformance has been established here.
