# tus

tus 1.0.0 server with creation, expiration, and termination. Offsets belong to native blob storage; lifecycle Tables fence byte acceptance. Metadata Documents never contain upload bytes. Checksum, deferred lengths, concatenation, and creation-with-upload are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Server`, `Http`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build tus` and `just test tus`. Compiler refusals remain failures.
