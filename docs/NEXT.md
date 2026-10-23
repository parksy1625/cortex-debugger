# Follow-up after M6

1. Verify M6 isolated subprocess live-model HTTP/Chromium integration and
   timeout/cancellation recovery in GitHub Actions.
2. Add fixed maximum IPC response size; consider enforcing memory with Linux
   cgroups v2 / systemd slices and Windows job objects.
3. Add real-model cancellation and timeout integration scenarios; measure
   time to terminate, restart and recover model memory.
4. Capture CPU/MPS cold and warm model load + activation passes and peak
   process RSS with repeatable hardware and dependency metadata.
5. Create vetted Python lockfiles and package-lock.json, switch CI to
   reproducible installation.
6. Release local installation packages, a privacy-safe report redaction
   flow, and optional branch protection checks.
