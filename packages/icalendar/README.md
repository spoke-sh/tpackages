# icalendar

Bounded iCalendar 2.0 component codec with lossless unknown properties, Unicode folding, and VEVENT summary editing. Recurrence and timezone definitions are preserved; local expansion and scheduling are excluded.

Status: target-language source; **unqualified**. The pinned compiler refuses the
public entry before checking protocol bodies. Native test cases are authored, not
reported as passing. See the [protocol plan](../../docs/application-protocol-plan.md)
and [compiler ledger](../../docs/compiler-requirements.md).

Import `build.transit` and select only the modules needed. Public modules:
`Codec`. Dependencies: none.
The [example](examples/build.transit) binds a stable instance and explicit roles;
the [native suite](tests/protocol.test.transit) specifies supported behavior.
Run `just build icalendar` and `just test icalendar`. Compiler refusals remain failures.
