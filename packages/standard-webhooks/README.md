# standard-webhooks

Standard Webhooks sender/receiver with exact-byte HMAC v1 and endpoint-bound Ed25519 v2a signatures. The pinned specification is [3d65b18](https://github.com/standard-webhooks/standard-webhooks/blob/3d65b1824b6697f05a5a4584e7062bd23512fc8e/spec/standard-webhooks.md). Native attempts have distinct IDs; permitted redelivery retains the message ID. Receiver claims are retained; payload access checks current owner and endpoint policy.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Signatures`, `Receiver`, `Sender`, `Http`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build standard-webhooks` and `just test standard-webhooks`. Compiler refusals remain failures.
