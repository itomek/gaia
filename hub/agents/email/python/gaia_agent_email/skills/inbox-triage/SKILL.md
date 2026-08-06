---
name: inbox-triage
description: Sort an inbox into what needs a reply, what needs a decision, and what is just noise. Use when the user asks to triage, catch up on, clean up, or make sense of their inbox.
version: 0.1.0
metadata:
  gaia:
    tools_required:
      - pre_scan_inbox
      - triage_inbox
      - get_message
      - archive_message
      - label_message
      - add_star
      - mark_read
---

# Inbox Triage

Triage answers one question per message: **does a human have to act on this?**

- Scan first (`pre_scan_inbox`, then `triage_inbox`); never open messages one by
  one to build a picture.
- Buckets, in order: needs a reply · needs a decision · for information · noise.
- Open only what the category can't settle. Sender + subject usually decide it.
- Act on the reversible end only — mark read, star, label, archive. Reply, send,
  and delete are proposals the user confirms.

**Report** the same full breakdown every time — "triage my inbox" has one
answer, never a short version and a longer one on request. Open with the
totals (items needing attention, messages scanned of the mailbox total),
then one section per bucket in this order: waiting on your reply · needs a
response · meetings to decide · needs a manual look. That order is the one
the items arrive in, so following it keeps the numbers below ascending.
Give every item its own line with sender, subject, and age.

Each item's number is its ``ref`` — copy it, never renumber. They already
run 1, 2, 3 … in this section order, so the count continues across the
breaks on its own and "archive 3" means exactly one thing.

**Every item appears exactly once.** ``needs_you`` is a view over the
``urgent`` / ``actionable`` / ``needs_review`` buckets, so an item you list
by number is ALREADY in one of those — listing that bucket as a section of
its own prints the same message twice under one number and destroys the
count. Those envelope names are never section headings; use the four
sections above and nothing else, and report the rest (informational,
filtered, anything past the numbered items) as bare totals with no list.

Age beats volume. A thread the user already answered is handled. "URGENT" in a
subject line is a claim, not a fact.
