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

**Report** every item, every time. Totals alone are NOT an answer: a reply
that says "14 items need attention" and stops has failed — "triage my inbox"
and "triage my inbox with details" get the identical full breakdown.

Open with the totals in one sentence, then a section per bucket in this
order: waiting on your reply · needs a response · meetings to decide · needs
a manual look. Then list EVERY item on its own line: its ``ref`` number, the
sender's name, the subject, the age.

List every ``needs_you`` item exactly once, and list nothing else.
``needs_you`` is a view over the ``urgent`` / ``actionable`` /
``needs_review`` buckets, so adding a section named after one of those
prints the same message twice under one number. Everything beyond the
numbered items — informational, filtered — is a bare total, never a list.

Age beats volume. A thread the user already answered is handled. "URGENT" in a
subject line is a claim, not a fact.
