# retrocpu Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies

- (002-m65c02-port)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes

- 002-m65c02-port: Added

<!-- MANUAL ADDITIONS START -->

## Temporary Files Policy

**IMPORTANT**: All temporary files created during development, debugging, or investigation MUST be placed in the `temp/` directory:

- **Investigation notes**: `temp/UART_RX_INVESTIGATION.md`
- **Debug scripts**: `temp/test_serial_fix.py`
- **Progress tracking**: `temp/BOOT_FAILURE_NOTES.md`
- **Research documents**: `temp/ECP5_MEMORY_RESEARCH.md`
- **Status reports**: Any `.md` files documenting temporary state

**Do NOT create temporary `.md` or `.py` files in the root directory.**

The `temp/` directory is in `.gitignore` and will not pollute the codebase. Clean, permanent documentation should go in the appropriate `docs/` or `specs/` directories.

<!-- MANUAL ADDITIONS END -->
