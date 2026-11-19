# websub

WebSub subscriber with HTTP/XML/HTML discovery, signed content intake, verification, and native lease renewal. Hubs must support SHA-256 or stronger HMAC. Callback identities belong to the bound application endpoint owner. Publisher and hub roles are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Discovery`, `Subscriber`, `Http`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build websub` and `just test websub`. Compiler refusals remain failures.
