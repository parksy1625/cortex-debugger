# After M9

1. Complete: Windows PowerShell published ZIP startup + actual GPT-2 CPU;
   packaged `.exe` GUI launcher compiled and headless integrity-checked.
2. Complete: unsigned macOS Finder `.app` launcher verified on Apple Silicon
   with actual MPS activation-patching inference.
3. Add human/manual GUI click tests on both platforms; automate real Windows
   GUI workflows where CI desktop sessions are available.
4. Provide properly signed Windows installer/MSI and notarized macOS .app or
   signed .dmg, with publisher trust/rollback and user installation docs.
5. Move toward a true self-contained Python/Torch runtime or an explicit
   installer wizard with progress reporting, model download estimate and errors.
6. Implement authenticated local API or owner-bound IPC, limit model IPC bytes,
   set hard memory budgets and add opt-in retention/compaction policies.
7. Capture polished application screenshots, demo video and developer
   benchmark suite across diverse models before expanding beyond GPT-2.
