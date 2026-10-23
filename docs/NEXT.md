# M7 follow-up roadmap

1. Verify private-data redaction, record deletion and browser E2E checks.
2. Read measured 3-run CPU benchmark artifact, record timings and sampled
   RSS with explicit hardware/environment caveats.
3. Commit an npm package-lock and a vetted Python 3.11 Linux resolution,
   enforce npm ci / locked Python installs in GitHub Actions.
4. Add redacted shareable reports to exact end-to-end real-model Chromium flow.
5. Add automatic retention policies with opt-in controls, SQLite VACUUM
   and backup guidance (do not promise secure erase).
6. Add true OS memory hard limits and IPC response byte ceilings;
   benchmark Apple MPS cold/warm latencies.
7. Package a standalone local installer and signed releases.
