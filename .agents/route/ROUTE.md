# Routes

When this entrypoint is loaded, immediately read the complete linked route metadata before continuing. Do not stop at this file.

- [Skills](skills.jsonl)
- [Rules](rules.jsonl)

After loading both route files, follow each `_meta.instructions` and load every selected Skill or matching Rule source before performing the task.

This directory is compatibility routing metadata only. Canonical Skill and Rule sources remain authoritative.
