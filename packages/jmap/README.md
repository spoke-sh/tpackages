# jmap

JMAP Core client with independently selected Mail metadata methods, synchronization mirror, native SSE Push, and blob transfers. Method errors remain distinct from HTTP success. Sync uses opaque account/type states and stable query snapshots, then reconciles changes from the pre-snapshot state. Mail submission, MIME processing, and server roles are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Core`, `Mail`, `Sync`, `Push`, `Blobs`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build jmap` and `just test jmap`. Compiler refusals remain failures.
