# CLAUDE.md

This file provides guidance to programming agents, like Claude Code (claude.ai/code), when working with code in this repository.

## Repository Purpose

This repository packages the Swift Concurrency Migration Guide from Apple into a Claude Skill format. The skill is automatically generated from the official Swift migration guide repository. This repository is exposed as a Claude plugin marketplace which vends a plugin which contains the skill.

## Build Commands

### Generate the Skill Package
```bash
python3 package.py
```

This command:
- Clones the official Swift migration guide repository (https://github.com/swiftlang/swift-migration-guide.git)
- Extracts and organizes the documentation content
- Copies Swift example files from Sources/Examples
- Generates the `migrating-to-swift-concurrency` directory with the skill content
- Creates `migrating-to-swift-concurrency.zip` archive for distribution

### Build Options
- `--output DIR` or `-o DIR`: Specify custom output directory (default: `./migrating-to-swift-concurrency`)
- `--keep-temp`: Keep the temporary git clone after packaging
- `--dry-run`: Simulate operations without writing files

## Code Architecture

### Design Philosophy: Separation of Concerns

The repository manages two distinct responsibilities which are intentionally decoupled:

1.  **Skill Generation (`package.py`)**:
    *   **Goal**: To be a standalone, portable tool that transforms the Swift migration guide into a canonical Claude Skill format.
    *   **Constraint**: It must have **zero dependencies** and be runnable by anyone, anywhere, to generate the skill.
    *   **Scope**: It strictly handles content extraction and generation. It generally *does not* know about the release process, versioning schemes, or marketplace metadata.

2.  **Distribution & Lifecycle (Repository & Workflow)**:
    *   **Goal**: To vend the generated skill via releases and the Claude Marketplace.
    *   **Scope**: This layer (handled by `.github/workflows/release.yml`) manages the "outer loop": running the generator, detecting changes, managing `marketplace.json`, and creating Git tags/releases.

**Implication**: Changes to `marketplace.json` or release logic should **never** be leaked into `package.py`.

### Main Components

1. **package.py**: The single-file packaging script with zero external dependencies
   - Manages temporary cloning of the Swift migration guide repository
   - Extracts metadata and parses table of contents from Guide.docc
   - Copies Swift example files from Sources/Examples
   - Orchestrates skill directory creation and artifact generation

2. **GitHub Actions Workflow** (`.github/workflows/release.yml`):
   - Orchestrates the nightly release process
   - Handles content verification, committing, and releasing

3. **Claude Plugin Marketplace Integration** (`.claude-plugin/marketplace.json`):
   - Contains metadata for the Claude plugin marketplace
   - Automatically updated by the release workflow with current date

### Key Implementation Details

- The script parses `Guide.docc/MigrationGuide.md` to determine the correct document order
- Metadata is extracted from each markdown file (title from first `#` heading, description from first paragraph)
- Swift example files are copied from `Sources/Examples/` with descriptions extracted from comments
- The skill is organized into two sections: Guide (documentation) and Examples (Swift code)
- Apache 2.0 license from the Swift repository is included for compliance

## Release Process

The repository uses a "release-on-change" strategy to minimize noise and version inflation:

1. **Nightly Trigger**: The GitHub Actions workflow runs every night.
2. **Generation**: It executes `package.py` to pull the latest documentation and generate the skill.
3. **Change Detection**: It compares the generated `migrating-to-swift-concurrency/` directory with the currently committed version.
4. **Conditional Release**:
   - **No Changes**: The workflow exits silently.
   - **Changes Detected**:
     - Updates `marketplace.json` with the new version (`YYYYMMDD`).
     - Commits the new content and metadata to the repository.
     - Creates a GitHub Release with the new artifacts.

### Configuration

- **`RELEASE_TOKEN` Secret**: The release workflow on GitHub requires a repository secret named `RELEASE_TOKEN` (Personal Access Token with `repo` or `public_repo` scope) to create releases and tags attributed to the maintainer. If missing, it falls back to the default `github.token` (bot attribution).

## Skill Content Structure

The generated `migrating-to-swift-concurrency` directory contains:
- `SKILL.md`: The main index file with frontmatter metadata
- `Guide/`: Migration documentation articles
- `Examples/`: Swift example code files
- `LICENSE.txt`: Apache 2.0 license from the Swift repository
