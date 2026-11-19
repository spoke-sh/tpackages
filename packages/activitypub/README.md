# activitypub

ActivityPub server-to-server source for configured peers, with ActivityStreams JSON and an explicit RFC 9421 Ed25519/RFC 9530 digest profile. The deterministic peer fixture is tpackages-federation-peer-v1; live interoperability is untested. Local application commands approve follows and publication. Client-to-server APIs, frontend serving, legacy signature schemes, and general Mastodon compatibility are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`, `Signatures`, `Federation`, `Http`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build activitypub` and `just test activitypub`. Compiler refusals remain failures.
