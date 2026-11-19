# Target-language contract used by these packages

This is a concrete proposal for upstream review, not the pinned compiler's
grammar. All files under `packages/` are target-language source. The runnable
bootstrap remains within the implemented source profile. The language basis is
linked from the [implementation plan](implementation-plan.md).

## Workspace and lazy exports (TP-01, TP-02)

```transit
WORKSPACE tpackages AS BEGIN
  PACKAGE oauth AT './packages/oauth';
  PACKAGE oauth_github AT './packages/oauth-github';
END;

DEPENDENCY oauth FROM WORKSPACE 'oauth';
IMPORT oauth FROM PACKAGE oauth FILE 'build.transit';

EXPORT MODULE Client FROM './src/client.transit';
EXPORT TYPE Configuration FROM './src/types.transit';
EXPORT TARGET default FROM './examples/build.transit';
EXPORT TEST TARGET tests FROM './tests/build.transit';
```

`PACKAGE` registers a package root, not an implicit import or activation. A
workspace dependency identifies the package by its directory name. Local
resolution uses the enclosing workspace; fetched resolution inherits the
repository and exact revision of the declaring package and consults that
snapshot's workspace map. The consumer lock records every selected subdirectory
and digest, including the workspace membership declaration itself as a verified
input to provenance and cache keys. Capturing only a package subdirectory is
insufficient for inherited resolution. Different revisions of this workspace in
one graph are an error.
Overrides must be explicit and appear in provenance. Resolution never fetches
during ordinary builds/tests.

Forwarding exports are lazy declarations. Importing `Client` loads its definition
and transitive imports, not the example/test targets. Selecting the example target
may import this public entry again without selecting that target recursively:
cycle detection is on selected declarations, not merely files. A cycle between
selected module definitions or targets still fails. Invalid source outside the
selected declaration/file closure does not invalidate it; syntax within selected
files must be valid. A library re-export carries the original nominal identity.

`EXPORT TARGET default AS GROUP (oauth.default, oidc.default);` selects independent
outputs, not one combined deployment. The test equivalent is
`EXPORT TEST TARGET tests AS GROUP (...)`. Each member has distinct provenance
and support status. No selected member may disappear on failure. Root aliases
are explicit imports of registered packages. Package default targets compile
examples with inert configuration; real applications instantiate public modules
with their own configuration and bindings.

## Types, modules, and execution (TP-03 through TP-06)

The sources extend the roadmap's typed SQL with named structural `TYPE ... AS
ROW(...)`, bounded `LIST<T>`, `OPTION<T>`, `SET<T>`, `MAP<K,V>`, `RESULT<T,E>`, and
tagged `VARIANT` types. `NONE`/`SOME`, `OK`/`ERR`, and exhaustive `MATCH` preserve
absence and errors. `?` propagates an error without coercing null/missing into
success. Record literals have named fields; `WITH (...)` creates an updated value.
`[]`, `SET(...)`, and `MAP(...)` are typed collections, not SQL text interpolation.
`VAR` declares mutable local state and `SET` assigns it; every path must assign a
local before use. `LET` creates an immutable lexical binding; shadowing is local
to the block and does not mutate an outer binding. `FOR ... IN ...` is bounded by
the input's declared collection limit. `WHILE ... BUDGET n` has an explicit bound
and refuses exhaustion. Recursive
pure functions have explicit depth/work budgets and reject exhaustion.

Interfaces declare typed functions/procedures and exported resources, including
their effects. A `MODULE Interface` value is an explicit dependency; `MODULE OF`
retains a concrete module's exports. Parameters use `$name` in SQL/module bodies.
`CREATE PUBLIC MODULE` can contain functions, tables, procedures, queues, and
dataflows; each instance specializes them under `BIND SCHEMA`. Exported routines
are callable through the instance. Pure helpers may not read mutable state.
`FUNCTION ... READS (...)` explicitly permits reads. `PROCEDURE ... AS BEGIN ATOMIC`
is one transaction, including nested procedure calls and native protected-store
updates. Guard failure aborts all writes and returns a typed refusal; it does not
commit half a state transition. `RETURN` exits the enclosing routine.

`SELECT ONE`, `SELECT OPTIONAL`, and `SELECT MANY` return a row, an optional row,
and a bounded list of rows respectively. Project scalar fields explicitly. A
parenthesized scalar aggregate subquery retains ordinary SQL scalar semantics.
Missing/extra rows are cardinality errors; absence requiring a protocol-specific
refusal uses `SELECT OPTIONAL` and an explicit match.

`CREATE PRIVATE TABLE` storage cannot be accessed by callers bypassing module
procedures. Imported source grants no runtime authority. Calls require native
module invocation grants; stateful operations additionally bind their caller's
opaque `OWNER` using `CURRENT_OWNER()`. Grant checks are repeated by the runtime at
transaction acceptance, dispatch, and result disclosure. Schema bindings determine
stable object identity. Source paths/aliases do not. Reusing an instance binding
with a different definition rejects and requires explicit migration handling.

Queue dataflows own their input operation and durable continuation. `EXECUTE SINK`
is legal only in dataflows; it uses an explicit original effect ID and
`ON REPLAY OBSERVE ONLY`. Outcomes distinguish `known`, `refused`, and `unknown`.
Unknown effects are retained. OAuth and other non-replayable operations must not
retry by creating a new ID. Explicit protocol redelivery may create a separate
authorized attempt while preserving the logical message and all prior evidence;
see the [application protocol contracts](application-protocol-contracts.md).
`ON FAILURE`
executes with the original input and cannot overwrite a terminal success. Queues
store protected handles rather than secret bytes. A protected handle is bound to
instance, owner, purpose, expiry, and originating operation; guessing its value
does not grant access. All invocations in a workflow retain the accepted owner.

## Native primitives required (TP-05, TP-07)

These are generic runtime capabilities, not hidden protocol implementations.
Every primitive must reject malformed/oversized input with a typed error, preserve
secret taint, and have a compiler signature. `REQUIRE` treats null, missing, type
error, and conflict as failure. `NOW`, entropy, secret access, and protected-store
operations have explicit effects; they are not compile-time evaluation.

| Family | Contract |
| --- | --- |
| Values | `LENGTH`, `CONTAINS`, `APPEND`, `UNIQUE`, `SORT`, `JOIN`, `SPLIT`, `LOWER`, `MIN`, `MAX`, `COALESCE`, `ONLY`, `OPTION`, `REQUIRE_SOME`, `IS_PRESENT`, map lookup/set/remove and bounded list selection preserve types. `ONLY` refuses cardinality other than one. |
| Encoding | Strict UTF-8, base64/base64url, URI percent encoding, query/form pairs with duplicate rejection, JSON with duplicate-key rejection, bounded CBOR, and XML with DTD/entities/XInclude/network disabled. Bounds include bytes, depth, nodes, and collection size. |
| Crypto | SHA-256, constant-time equality, random bytes/tokens, PKCE S256, JWK/COSE key decoding, public-key validation, RSA SHA-256 and P-256 SHA-256 sign/verify, and XML canonicalization/signature verification over an explicitly selected node. No protocol-level `VALIDATE_OAUTH`/`VERIFY_LOGIN` builtin. |
| Protected values | `SECRET(name)` resolves a deployment reference at runtime; `SECRET_CURRENT`, `COMMITMENT`, `DERIVE_SECRET`, and protected parsing/encoding retain labels. `PROTECT(value, purpose, expires)` atomically stores a protected value and returns a scoped handle; `UNPROTECT(handle, purpose)` enforces scope/owner/lifetime; `DESTROY_PROTECTED` is transactional. Handles may be stored, plaintext may not. |
| HTTP | Bounded no-redirect sinks, protected request/response bodies, redacted metadata, one dispatch attempt, typed status/headers/body, explicit current authority. `HTTP_QUERY_*` rejects duplicate fields. `HTTPS_URL` validates scheme, credentials, fragment, and host against an explicit allowlist; runtime egress additionally refuses private/link-local/loopback DNS targets. |
| State | Serializable transactions with predicate/read-set validation, unique keys, compare-and-set revision updates, atomic queue enqueues, immutable operation outcomes, and protected-store rollback. `NEW_ID` supplies bounded collision-resistant opaque IDs. `CHILD_BINDING` derives a stable explicit child instance. |

`CRYPTO_VERIFY` returns false for an invalid signature, including malformed
signature encodings; unsupported algorithms and invalid keys are typed errors.
HTTP `bytes`/`protected_bytes` responses preserve bounded raw bodies for explicit
package parsing. `JSON_PARSE` accepts strict UTF-8 bytes or text; its protected
counterpart retains taint. Test mock JSON bodies are encoded to those same wire
bytes before the native sink observes them.

Codec names in source describe individual operations (`JSON_PARSE`, `JSON_GET`,
`XML_PARSE`, `XML_CHILDREN`, `CBOR_DECODE`, etc.); their options specify bounds.
XML signature verification returns the exact verified node handle and rejects
external references, duplicate IDs, unsupported transforms, or ambiguous references.
JWT compact decoding exposes signing bytes and fields; policy validation is
implemented in `oidc`. WebAuthn authenticator bytes are decoded in package source.
SCIM filter parsing and PATCH application are package source, not native workflows.

Protected JSON permits nonsecret metadata extraction only through an explicit
field projection with a declared output type; token/code fields stay protected.
JWT claim projection is permitted only after signature/claim validation. Sources
use `PUBLIC_FIELD` for these audited projections. These operations require typed
information-flow checking; ordinary `CAST` or string encoding cannot declassify.

## Test-only controls (TP-08)

The target runner adds `ACTIVATE TEST MODULE`, `SET TEST CLOCK`, `ADVANCE TEST CLOCK`, deterministic
`SET TEST ENTROPY`, isolated `SET TEST OWNER`, `SET TEST SECRET`, `MOCK SINK`,
`DRAIN ...`, `CRASH BEFORE/AFTER ...`, `RESTART`, and `ASSERT ...` expressions.
Every test receives fresh state, a virtual clock initially set to
`2026-01-01T00:00:00Z`, and zero network access. `ACTIVATE TEST MODULE` explicitly
authorizes case-local calls and dataflows through native test authority and
activates their definitions; it cannot grant production rights or bypass module
guards. Unmocked external effects fail. `DRAIN` has an explicit
step budget and does not itself activate anything. Mock outputs are native effect observations; tests must assert
dispatch count as well as results. Test signing keys and protected literals are
case-local fixtures; they cannot become deployment credentials. `ASSERT CALL ...
FAILS WITH` checks a runtime refusal, not a compilation failure. Collection and
filter helpers are shared language primitives; fixture helper functions remain
visible Transit source.

Workspace-only `ASSERT DEPENDENCIES`, `ASSERT NO OUTPUT FROM`, and
`ASSERT COMPILE ... FAILS WITH` inspect real compiler results. They do not infer
behavior from text search. The Python repository checker only inventories files,
enforces obvious source boundaries, runs commands, and matches recorded failures;
it does not implement any of these language semantics.

## Commands, resource composition, and observation (refactor contract)

The authored dataflow refactor uses the following additional target contracts.
These are proposed spellings and semantics, not claims of support on the pins.
The focused probes and first refusals are in `compiler-requirements.md`.

### Execution and authority

`CREATE DATAFLOW ... FROM COMMAND (typed parameters) AS request AS BEGIN ATOMIC`
accepts one native command. Its input, owner, original request identity, guarded
read set, mutation, and returned result share the native operation contract.
`WITH (idempotency = 'original_owner_request')` retrieves the original result for
an identical retry; changed arguments conflict. A new invocation with an already
consumed protocol challenge is a new command and must refuse. Retained result
inspection rechecks invocation/disclosure authority and exposes no request secrets.
Command inputs containing secret values use protected native input retention.
Read-only commands obtain one consistent snapshot and current read authorization.

`CURRENT_OWNER()` in a Queue or Stream continuation is the accepted input owner,
not the worker role. Execution roles grant the module narrowly scoped state or
effect access while preserving that attribution. A consumer may only assume an
input owner through an authenticated native input binding, never an ordinary row
containing an owner field. Ordinary application code cannot impersonate that owner.
`NATIVE_ALLOWED(owner, 'configure', resource)` names a separate configuration right.
`policy_status` Views reveal the revision only to holders of that right. Native
module invocation grants alone cannot configure policy or retrieve protected tokens.

`AUTHORIZE MODULE instance WITH (...)` is a proposed checked expansion of explicit
role bindings over the selected instance graph: `commands`, `state`, `effects`,
`reads`, `maintenance`, or `sources`. It supplies no default role, configure right,
or protected-token-use grant. Missing required bindings refuse activation; bindings
for categories absent from a specialized graph are inert. Command/read bindings cover only root public exports; private child invocation
capabilities require explicit composition requirements. State/effect/maintenance
bindings follow the selected graph. Native roles/resources must already exist. `ACTIVATE MODULE` installs selected consumers before ingress,
and never imports unselected HTTP/publication modules. Typed exports grant no
rights. Examples name deployment settings and remain inert until installed by an
authorized application; `USE` alone neither authorizes nor activates anything.

Protected-use functions and cross-module atomic helpers require separate explicit
invocation capabilities. In particular OIDC's child composition binds
`issue_challenge`, `credential`, and `token_material` to its own flows only. Passing
a module value grants no capability to an unrelated consumer. Consumer activation
must validate those required internal capabilities; it must not grant them to all
callers of the parent module. This binding is represented explicitly in the OIDC
constructor and its emitted authorization graph.

Procedures still inline in a single native transaction. `issue_challenge` allows
OIDC to create its own nonce context in that transaction. `settle` couples a
terminal protocol state with one event. Store helpers allow SCIM to commit a
protocol write, resource versions, relationships, and events together. They cannot
dispatch effects or own a scheduler. `RETURN` in a dataflow marks its input terminal;
it does not abandon a Queue lease or leave a Stream checkpoint pending.

### Documents, KV, and relational reads

Versioned `DOCUMENT` declarations contain typed rows and bounded structured fields.
`INSERT ... ON CONFLICT DO NOTHING` in installation input seeds an absent record
once; a later install cannot reset accepted policy. `_revision`/`REVISION` identify
an exact document revision. A document read enlisted by an atomic command, guard,
or acceptance block participates in serializable validation. Security policy
updates use expected revision and refuse stale writes or unresolved conflicts;
no CRDT or automatic merge grants authority. The selected document owner must
support the complete mixed transaction, not merely standalone row operations.

For this proposal, `GET FROM kv KEY key` returns `OPTION<ROW(value T, revision
REVISION)>`. It is an explicit typed point-read form, not an assumed equivalence
to every existing SQL KV projection. `PUT ... IF ABSENT`, `PUT ... IF REVISION = r`,
and `DELETE ... KEY ... IF REVISION = r` enlist conditional mutations in the same
transaction as Table, Document, Queue and Stream work. Revision mismatch conflicts;
missing expiry indexes or resource participants cannot turn acceptance partial.
Keys are bounded text/binary. Challenge context is canonical in KV; expiry Tables
only index keys/deadlines and never decide validity. `LENGTH_PREFIXED_UTF8` is a
bounded generic encoder of length-delimited strings, used to avoid composite-key
ambiguity before hashing an issuer/assertion pair.

Relational module interfaces export a `VIEW name ROW(...)` or `STREAM name ROW(...)`
with its typed row schema, privacy and effect requirements. `MODULE OF constructor`
refers to that constructor's exported interface. A structural interface can require
only selected dataflow signatures, as the OAuth HTTP adapter does. Constructor
forwarding (`EXPORT MODULE Http = oauth.Http`) preserves the original interface
and dependency identity without constructing a second implementation.

`ARRAY(SELECT ...)`, `UNNEST`, generated columns, named UNIQUE constraints, enforced
foreign keys, JOIN, bounded ORDER BY/OFFSET/LIMIT and scalar COUNT are native typed
query operations. Pure bounded predicates such as SCIM `filter.matches` can occur
in WHERE and must lower through the same query engine; the package does not
materialize all records or build SQL strings. Page and count share a read snapshot.
`JSON_OMIT` and disjoint JSON merge are generic bounded value operations. SCIM
assigns disjoint fields to its identity/name/membership Tables and attribute
Documents; its read View reconstructs the wire document. The optional application
Store fixture intentionally uses a different Table model under the same contract.

`ON CONSTRAINT name FAIL 'code'` and `ON FOREIGN KEY FAILURE FAIL 'code'` map a named
native integrity refusal to a protocol error without committing any write. They
must not swallow unrelated conflicts, I/O failures, or unknown transaction results.
Native serializable retries retain input and operation identity. Unique races
cannot bypass the constraint through a prior stale existence check.

### Effects, Streams, and lifecycle

`HTTP_FIELDS` is a typed map whose cells retain their public/protected labels.
Encoding it for an authorized Sink preserves taint. It cannot be serialized to an
ordinary log or result. `TRY_RESULT(expression)` captures a bounded pure validator's
typed refusal into `OK(value)`/`ERR(public_code)`; it does not catch an unknown
commit, retry an effect, or declassify a payload. OIDC uses it to distinguish the
single allowed missing-key refresh from other token failures.

`FROM STREAM ... WITH (consumer = ..., required = TRUE, checkpoint =
 'terminal_atomic')` consumes a native assigned input with a retained original
identity. Its terminal state/output writes and input offset commit together. An
intermediate transaction (such as accepting refreshed OIDC keys) records durable
continuation progress but does not settle the input. Replay resumes that original
continuation with retained effect observations. Failure continuation has the same
checkpoint rule. A filtered or already-terminal input settles without another
output event. Consumer group identity is scoped to the Stream and stable instance;
source paths and import aliases do not rename it. Assignment generations fence
obsolete workers. Input disclosure, output disclosure, and every read of a protected
reference require current rights in addition to preserved owner attribution.

Streams declare partition keys and `disclosure = 'current_owner'`; ordinary reads
and finite test reads filter by the caller's owner and also require native Stream
read authority. Authorized flow consumption uses the accepted-owner binding above.
All current protocol work/result Streams retain unlimited history explicitly.
Changing retention later requires reviewed required-consumer and accepted-work
protection; it cannot silently drop an unconsumed identity result. Optional
observers must report a gap and resnapshot if a future policy permits expiry.
Resnapshotting must not reissue effects. These Streams are not another dispatch or
retry ledger: native effects retain their own authoritative receipts.

`FROM TIMER EVERY SECONDS(n)` is a native bounded maintenance input, with an
original tick identity and explicit maintenance role. No package host loop or
application call to `prune` drives it. Tests drain ticks due at the virtual clock,
not future ticks. Expiry commands select at most 64 eligible indexed records per
tick, recheck the canonical point value, then delete the value and its index in
one decision. Native protected-store expiry/destruction is idempotent, transactional,
and preserves separate operation evidence. OAuth excludes Pending operations from
challenge cleanup; terminal unknown metadata remains after protected bytes expire.
SAML replay retention uses the validator's final permitted acceptance time, already
including clock skew. Native trusted time is checked at the transaction decision.

### Optional native HTTP bindings

`SOURCE ... FROM HTTP REQUEST AS request INTO COMMAND instance.command(arguments)`
is a proposed native binding, with explicit method/path, decoding expressions,
limits, admission, authentication, response mapping and error encoding. The typed
command owns behavior. Source-local `LET` binds protected transient inputs before
admission; `RESULT` names the retained command result. Response templates consume
one native response capability after acceptance and recheck disclosure policy.
Lost delivery cannot reinvoke the command. These examples complete callbacks with
202 operation references; application result consumers own subsequent UI/session
behavior. They do not retain an HTTP response across a background exchange.

`HTTP_*_UNIQUE` rejects duplicates after decoding/normalization with the public
code `DuplicateHTTPField`; disallowed query parameters use `UnsupportedQueryParameter`.
Optional variants
return OPTION; `HTTP_SECRET_*` keeps code/cookie/assertion fields protected. JSON
helpers enforce strict UTF-8, duplicate-key refusal, depth/work budgets and base64url
byte decoding. `HTTP_PATH_WITHOUT_PREFIX` returns the bounded normalized route path.
Cookie templates require secure/HttpOnly attributes and the declared SameSite/path;
redirect templates use only the accepted command result. The SAML POST binding uses
SameSite=None with the one-use browser/request challenge, while initiation checks
same origin. WebAuthn's example binding delegates authentication to application
policy and checks same origin for all routes.

The `application` authentication profile is a required application-supplied native
identity binding, not an anonymous or trusted-by-default shortcut. A Source must
refuse activation without it. Native decoding/unknown-route/method errors also
pass through the binding's error encoder. SCIM explicitly maps command errors to
its status/media-type/error-body contract and rejects unknown query parameters;
its native Sources do not infer a generic CRUD dispatcher. Sources grant neither
state access nor permission to call other commands. A selected Publication
similarly needs explicit authorization/activation and checks current View policy
at each disclosure. No credential-bearing publication is exported.

### Additional native test controls

`INVOKE COMMAND instance.command(...) [WITH REQUEST_ID '...']` submits through the
native command boundary. Default invocations get distinct request identities;
explicit reuse tests original-result recovery. `SIMULATE HTTP module(ROW(...))`
submits through that module's installed Sources and real decoders/encoders; it is
not an in-process call to an old request procedure. `DRAIN MODULE` advances only
activated due work in the selected instance graph, under a finite step budget.

`RACE COMMANDS (...) AT FIRST WRITE` uses native transaction scheduling to align
contenders after their initial reads and reports accepted results and typed
refusals. Crash selectors can target effect dispatch/retained observation, commits
producing a public Stream, and a named consumer checkpoint. `RESTART` restores
native retained state. `TEST STREAM` exposes a finite observed cut for assertions
with current authority; reading it neither settles a consumer nor admits work.
`GRANT TEST ACTION 'configure' ON MODULE ... TO OWNER ...` supplies only case-local
native configuration authority for that instance. It does not disable its guards.
`ASSERT NO RESOURCES OF KINDS`, `NO RUNTIME SETTINGS`, and `NO AUTHORIZATIONS` inspect
actual selected compiler output and provenance. None is implemented by text search.

`PUBLIC_RECORD(value, purpose => 'verified_saml_identity')` is an audited generic
projection of the explicitly constructed typed result after all SAML signature and
binding checks. It does not verify XML or accept arbitrary response documents.
Secret input taint is preserved through parsing; only the named result fields are
projected for authorized result consumers. The compiler must track this explicit
disclosure boundary as it does `PUBLIC_FIELD` for JWT claims. Test-only
`TEST_PROTECT` adds taint to synthetic fixtures; it cannot declassify production
inputs. Public-to-protected promotion is allowed, protected-to-public coercion is
forbidden without a declared projection.

`SIMULATE HTTP SOURCE instance.source(ROW(...))` selects an installed native route
by reference, supplying its configured path while still exercising method,
authentication, admission, decoders, command invocation, and response encoding.
`raw_query`/`raw_body` retain wire duplicates; supplying decoded `query`/`body` in
other fixtures first uses the host's ordinary wire encoder. Case-local activation
supplies the native identity binding from `SET TEST OWNER`, never a production
authentication bypass. Strict decoder failures default to 400 and admission
failures to 403 unless an explicit encoder maps them. Error bodies omit protected
payloads. SCIM keeps its own encoder and media type.

`ASSERT HTTP COOKIE ... HAS ATTRIBUTES` inspects response cookie metadata in the
native test host. `TEST RESPONSE COOKIE response 'name'` returns only a protected
Cookie request header, preserving taint through the next simulated request. It
does not expose cookie values as ordinary text. These are TP-08/16 requirements,
not Python helpers or evidence that the current test host implements them.

`SET TEST RESOURCE BUDGET stream TO EVENTS(n)` changes the native test admission
budget for that resource. Appending beyond it refuses with `ResourceExhausted`
and rolls back the entire transaction, including KV/Document/protected-store
writes. It neither truncates retained history nor bypasses ordinary dataflows.
This fault-control requirement exercises mixed-resource rollback under bounded
backpressure; it is not an alternative production retention implementation.

`CRASH AFTER COMMAND COMMIT BEFORE RESPONSE` crashes the native host after durable
admission/result retention and before returning a value. The test resumes after
`RESTART` and resubmits the same request identity. It cannot assign a return value
to the interrupted call or infer that a lost response means failure.

Expiry Tables have explicit native `(expires_at, key)` indexes; OIDC indexes only
pending results. Indexes are derived access paths maintained by the same native
transaction, not independently writable state owners. A LIMIT bounds mutations;
native query/work budgets must also bound candidate scans (including OAuth's
pending-operation exclusion). Exhaustion defers a maintenance tick without partial
deletion or skipped logical expiry checks. Query/index lowering is part of TP-14/15.
