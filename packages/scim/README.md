# SCIM service provider

Status: **Target-language implementation; unqualified.** The pinned tools reject
the package entry before typechecking or running its tests. See the
[compiler ledger](../../docs/compiler-requirements.md) and
[language proposal](../../docs/target-language.md). No production compatibility or
protocol conformance is claimed from source review alone.

Public entry: [build.transit](build.transit). API: `ServiceProvider(binding, store, policy, base_url)` and optional `DocumentStore(binding)`.
Package dependencies: None.

Explicit command dataflows implement `discover`, `list_resources`, `get_resource`,
`create_resource`, `replace_resource`, `patch_resource`, and `delete_resource`.
The optional `Http` module binds Users/Groups and discovery routes to those commands
with SCIM status, headers, media type, and structured error encoding. `resources`
is an authorized query View; `changes` is an immutable resource-change Stream.
Applications provide provisioning authority and may supply their own Store.

## Initial profile

A bounded subset of SCIM 2.0: core Users (userName, displayName, active, externalId, name.givenName/familyName, emails) and Groups (displayName, externalId, direct User members). Filters support comparisons, pr, not/and/or and parentheses; general valuePath and schema-qualified extension attributes are refused. PATCH supports whole supported attributes, name subattributes, and members[value eq "id"]. No bulk, sorting, projection, /.search, passwords, enterprise extensions, nested groups, or outbound client. The optional store allows at most 1,000 resources of each kind; exhaustion refuses rather than truncating. These exclusions mean this is not a claim of full SCIM conformance.

## Consumption and testing

The `Store` contract requires one isolated provisioning scope, stable IDs,
case-insensitive unique usernames, compare-and-set versions, and serializable
read/write sets across the caller's transaction. Its typed `resources` View supports
filtering, counting, ordering, and pagination inside the query; there is no
collection-materializing `list()` method. Member references must resolve to
Users in that scope, and removing a User removes its group memberships in the same
transaction. `Policy.allow` checks current authority and refuses with `forbidden`.
`Policy.can_read` restricts each resource disclosed by the query View. Custom
stores must preserve these behavioral obligations, not merely the signatures.
The optional `DocumentStore` uses Tables for IDs/ETags, usernames with a native
case-folded uniqueness constraint, and foreign-key memberships. A versioned
Document owns the remaining attributes. Writes and change events share the
caller's transaction, including every affected Group version when a User changes.
The same provisioning suite runs against this store and an independently authored
[application store](tests/application-store.transit).

The optional HTTP Sources bound and decode JSON with duplicate-key rejection
before command admission, and preserve unique query/header fields. The package constructs
member display/type/reference fields from authoritative Users and its configured
base URL; caller-supplied read-only member fields are not trusted.

Declare this repository at an exact revision with subdirectory `packages/scim`
and import its public entry. Workspace dependencies inherit that revision. No
private sibling import or application-wide umbrella package is needed.

[Example composition](examples/build.transit) supplies explicit instance bindings,
command/effect/read/maintenance roles, activation, and a durable result consumer.
Real consumers replace the example policy/settings and supply current authority,
secrets, and a migration basis. Optional HTTP targets additionally need the
application's native authentication binding. Importing a module alone grants no
rights and activates no work.

`just build scim` and `just test scim` attempt the real compiler commands
and currently fail at the recorded gap. The [Transit tests](tests/build.transit)
are executable specifications for the target language, not tests that have passed.
`just check` audits the gap separately from the runnable bootstrap.

State belongs to explicit instance bindings. Keep accepted operations and unknown
effect outcomes when upgrading. Use an explicit prior definition graph and a
reviewed migration; changing source or configuration is not permission to replace
live state. No generated migration is published before native support is verified.

Protocol sources: [SCIM schema](https://www.rfc-editor.org/rfc/rfc7643.html), [SCIM protocol](https://www.rfc-editor.org/rfc/rfc7644.html).
