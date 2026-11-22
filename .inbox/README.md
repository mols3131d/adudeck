# Inbox

`.inbox/` is a temporary, non-canonical workspace. This `README.md` defines its policy.

## Organization

- Group related working material by work unit and reuse the same container across sessions.
- GitHub Issue or Pull Request: `.inbox/github-<number>/`.
- Branch without an Issue/PR: `.inbox/branch-<slug>/`.
- No stable work-unit identifier: `.inbox/YYYY-MM-DD/` (creation date).
- Existing dated directories may remain where they are; do not rename unrelated records solely for consistency.

## Rules

- Keep at most 30 date-based fallback directories. When adding one would exceed the limit, delete the oldest dated
  directories only after checking their contents and preservation requirements. Do not count work-unit directories.
- Use inbox material as working context only when it is reasonably fresh and accurate. It is never project authority;
  canonical artifacts win on conflict.
- Except for this `README.md`, do not link to or reference inbox files from outside `.inbox/`.
- Promote durable material before external reference: move it to its canonical location or absorb the relevant content
  into an existing canonical artifact, then reference that artifact.
- Repository safety and confidentiality rules still apply. Never store secrets, credentials, access tokens, or private
  account identifiers here.
