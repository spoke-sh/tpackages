# json-rpc

JSON-RPC 2.0 client, command-bound server, and optional HTTP POST transport. Batch members have separate native transactions. Notifications produce no response; explicit null IDs remain requests. Correlation IDs never authorize remote replay. MCP, discovery extensions, and frontend hosting are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`, `Server`, `Client`, `Http`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build json-rpc` and `just test json-rpc`. Compiler refusals remain failures.
