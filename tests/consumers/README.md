# Consumer contracts

Every directory is an independently rooted application composition importing only
public package entries. `github`, `google`, `facebook`, `oidc`, `saml`, `scim`,
`webauthn`, `saml-scim`, and `oidc-github` assert the selected dependency/output
closure. Standalone applications wire result consumers with explicit authority
and activation; `github`, `oidc`, and `webauthn` additionally assert core selection
has no HTTP Source or Publication. `surfaces` selects pure validators and asserts
that they require no resources, runtime settings, or grants. `two-instances` adds a
challenge-isolation suite; `conflicting-bindings` specifies the refusal for two
different definitions mapped to one durable identity.

`selection` is an independent workspace. Its unrelated package and unselected
test target deliberately contain constructs unsupported by the pinned parser.
Building its production target must not load either source. These fixtures remain
blocked at workspace syntax today, so none of these assertions has passed.

`external/build.transit.in` uses the implemented repository/revision/subdirectory
syntax. The checker creates an isolated temporary Git snapshot of the workspace,
substitutes its exact revision, and invokes an explicit local `--fetch` without
overrides. This does not commit or change the working repository. The current
compiler reaches the fetched GitHub package and rejects its workspace dependency.
That is evidence of fetching and crossing the package boundary, not successful
transitive resolution or an offline rebuild. The snapshot and its cache are
discarded after the check; there is no network access or provider contact.

Package examples separately export optional HTTP targets. Their test targets run
core and HTTP suites independently; the three adapters share OAuth's native HTTP
contract suite. SCIM's provisioning suite also runs against an application-owned
Store implementation with a typed query View and inline atomic writes.

Frozen external rebuilds, mixed-revision rejection, rename preservation, and
state migrations remain qualification gates in the implementation plan. They need
a successfully resolved/compiled package first; no synthetic passing evidence or
invented prior migration basis is checked in.
