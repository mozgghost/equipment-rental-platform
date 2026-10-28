# Initial role and permission matrix

This matrix defines expected authorization. A model field or hidden button alone does not implement the permission. All unmarked API mutation routes must be denied until server-side checks and tests exist.

| Operation | Anonymous | Renter | Company manager | Company owner | Platform admin |
|---|---:|---:|---:|---:|---:|
| Browse published catalogue | Yes | Yes | Yes | Yes | Yes |
| Read own profile | No | Yes | Yes | Yes | Yes |
| Create booking for self | No | Yes | Yes | Yes | Policy decision / break-glass only |
| Read renter's own booking | No | Yes | Only when same company owns the equipment and permission policy allows it | Same company scope | Limited administrative access, audited |
| Cancel booking | No | Own eligible booking | Same company operational scope | Same company operational scope | Audited support override only if implemented |
| Create/edit equipment | No | No | Own company only | Own company only | Moderation/administrative action, audited |
| Change company legal details | No | No | No | Own company only | Limited support action |
| Invite/manage company staff | No | No | No | Own company only | Platform admin policy only |
| Schedule maintenance | No | No | Own company only | Own company only | Audited support only |
| View company reports | No | No | Operational subset for own company | Full permitted company reports | Aggregate platform statistics only as needed |
| Moderate reviews/complaints | No | Create complaint/review when eligible | No | No | Yes, with audit trail |
| Suspend platform account | No | No | No | No | Yes, reason required and audited |

## Implementation status

The custom user, company and membership models exist. Booking list scoping is an initial implementation; dedicated company mutation APIs and a complete permission regression suite are not finished. Until those tests exist, this matrix is a target contract, not an acceptance claim.
