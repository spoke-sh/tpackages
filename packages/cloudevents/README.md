# cloudevents

CloudEvents 1.0 envelope, JSON format, structured/binary HTTP encoding, and an optional source-bound intake Stream. The Stream adapter retains payloads; applications must select it only for data approved for retained history. Batch and non-HTTP bindings are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`, `Http`, `Streams`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build cloudevents` and `just test cloudevents`. Compiler refusals remain failures.
