# Claude Code Guidelines

Read and follow `genOS-main/AGENTS.md`. It defines the genOS operating system, universal commands (`kickoff`, `shutdown`, `doctor`, `status`, `batch`, `update`), single source of truth rules, and zero-history recovery protocols.

genOS is installed in the `genOS-main/` subdirectory: every brain path in the kernel (e.g. `brain/20_PROGRESS.yaml`) is relative to `genOS-main/`.
