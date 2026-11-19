# vcard

Bounded vCard 3/4 interchange codec with preserved property groups, parameters, repeats, and extensions. Explicit formatted-name edits escape text and prevent line injection; contact merging and enrichment are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build vcard` and `just test vcard`. Compiler refusals remain failures.
