# carddav

carddav discovery, conditional CRUD, query/multiget, and optional synchronization mirror. Composes public webdav and vcard entries from the same workspace snapshot. Account credentials and policy are supplied by the application; domain workflows and server roles are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Client`, `Mirror`. Dependencies: webdav, vcard.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build carddav` and `just test carddav`. Compiler refusals remain failures.
