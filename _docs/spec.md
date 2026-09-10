# CloseTab MVP Scope

## Product Vision

A collaborative family/group expense splitting tool focused on fair settlements, auditability, controlled closure, and optimized settlement flows.

---

## Target Audience

- Group-focused usage
Group can be family household, friend group, trip or dinning etc...

## Primary Goal

- Split expenses fairly
- Determine who owes whom
- Settlement management

---

## Identity Model

### Device-Based Identity

- Device gets a local identity
- User provides a display name
- No mandatory login for MVP
- Account linking can be considered later

### Lightweight Identity

- Minimal onboarding
- No complex profile management

---

## Member Model

### Equal Members

- All members are treated equally for expense sharing
- No weights or adult/dependent hierarchy in MVP

### Retroactive Member Inclusion

New members can be added at any time.

Effective date options:

- From today onwards
- From a chosen historical date

Recalculation options:

1. Recompute History
   - Historical balances are recalculated.
2. Adjustment Entries
   - Historical records remain unchanged.
   - System creates adjustment transactions.
3. User chooses either mode during member addition.

---

## Expense Entry

### Expense Date

- Default = Today
- User can select any past date
- Future dates are not allowed

### Split Modes

When creating an expense, user chooses:

#### Mode A: Everyone

- Include all members
- Allow exclusions

#### Mode B: Selected Members

- Start with no one selected
- User explicitly selects participants

Rationale:

- Avoid large-group uncheck operations
- Works well for both small and large groups

### Split Calculation

- Equal split among participating members

---

## Balances

- Maintain running balances
- Show who owes whom
- Automatically recalculate when valid changes occur

---

## Settlements

### Settlement Recording

- Record settlement transactions
- Update balances automatically

### Settlement Audit Trail

Store:

- Payer
- Receiver
- Amount
- Date
- Optional notes

### Settlement Optimization

Support optimized settlement suggestions that reduce the total number of transfers required across the group.

---

## Expense Locking Rules

### Settlement Protection

Once an expense participates in settled balances:

- Expense becomes locked
- Editing is not allowed
- Deletion is not allowed

Corrections should be handled using:

- Reversal entries
- Adjustment entries

---

## Group Lifecycle

### Open State

Allowed:

- Add expenses
- Edit expenses
- Delete expenses (subject to locking rules)

### Close Group / Trip

Group creator closes the group.

After closure:

- No expense editing
- No expense creation
- Review balances only
- Settlement phase becomes available

### Reopen Process

- Group members decide externally (outside application scope)
- Group can be reopened
- Changes can be made
- Group can be closed again
- Settlements proceed afterwards

Principle:

- Close first
- Settle afterwards

---

## Collaboration

### Concurrent Editing Protection

Only one user may edit a record at a time.

While a record is being edited:

- Others can view it
- Others cannot modify it

Lock is released when:

- Save succeeds
- Edit is cancelled
- Timeout occurs

---

## Explicitly Deferred From MVP

- Weighted member sharing
- Adult/dependent hierarchy
- Budgeting features
- Spending analytics
- External messaging/approval workflows
- Complex authentication systems

---

## MVP Summary

1. Group-focused expense splitting
2. Device-based lightweight identity
3. Equal member model
4. Past-date expense entry
5. Everyone / Selected Members split modes
6. Equal split calculation
7. Balance tracking
8. Settlement recording
9. Settlement history and audit trail
10. Retroactive member inclusion
11. Recompute-history or adjustment-entry recalculation
12. Settlement optimization
13. Expense locking after settlement impact
14. Trip/group closure workflow
15. Single-editor concurrency lock
