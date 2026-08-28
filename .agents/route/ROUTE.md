# Routes

When this entrypoint is loaded, immediately read the complete [Skill route](skills.jsonl) before continuing. Do not stop at this file.

After loading `skills.jsonl`, follow its `_meta.instructions` and load every selected Skill source before performing the task.

This directory is compatibility routing metadata only. Canonical Skill sources remain authoritative.
