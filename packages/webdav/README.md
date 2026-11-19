# webdav

Shared WebDAV client, XML multistatus codec, and optional collection mirror. Native command continuations issue bounded requests; sync pages commit resources and cursors together. Writes require HTTP preconditions. DAV server and locking roles are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`, `Client`, `Sync`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build webdav` and `just test webdav`. Compiler refusals remain failures.
