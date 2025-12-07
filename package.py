#!/usr/bin/env python3
"""
Package the Swift Concurrency Migration Guide into a Claude Skill.

This tool automates the creation of a structured Claude Skill directory
containing the official Swift concurrency migration documentation and code
examples. It handles repository cloning, content organization, metadata
extraction, and index generation.

Design Philosophy:
This script is designed to be a standalone, portable generator. It strictly
handles content processing and skill generation. It does NOT manage release
lifecycles, versioning schemes, or marketplace metadata. Those concerns are
handled by the repository's release workflow.

Features:
- One file
- Zero external dependencies
- Robust error handling and cleanup
- Markdown metadata extraction
- Swift example code inclusion

Usage:
    python3 package.py [--output DIR] [--keep-temp]

Copyright (c) 2025 Kyle Hughes. All rights reserved.
"""

import argparse
import dataclasses
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any


# --- Logging Configuration ---

class TerseFormatter(logging.Formatter):
    def format(self, record):
        return f"[{record.levelname}] {record.msg}"

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(TerseFormatter())

logger = logging.getLogger("migration-packager")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False


# --- Configuration ---

@dataclasses.dataclass
class Configuration:
    """Runtime configuration and constants."""

    # Runtime settings
    output_path: Path
    keep_temp: bool = False
    dry_run: bool = False

    # Constants
    REPO_URL: str = "https://github.com/swiftlang/swift-migration-guide.git"
    SKILL_NAME: str = "migrating-to-swift-concurrency"
    TOC_REL_PATH: str = "Guide.docc/MigrationGuide.md"
    GUIDE_REL_PATH: str = "Guide.docc"
    EXAMPLES_REL_PATH: str = "Sources/Examples"

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'Configuration':
        """Create configuration from parsed arguments."""
        output = Path(args.output) if args.output else Path.cwd() / cls.SKILL_NAME
        return cls(
            output_path=output,
            keep_temp=args.keep_temp,
            dry_run=args.dry_run
        )


# --- Git Operations ---

class GitRepository:
    """
    Manages a temporary git repository clone.

    Implements the Context Manager protocol for automatic cleanup.
    """

    def __init__(self, url: str, keep_temp: bool = False):
        self.url = url
        self.keep_temp = keep_temp
        self._temp_dir: Optional[str] = None
        self.path: Optional[Path] = None

    def __enter__(self) -> 'GitRepository':
        self._clone()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._cleanup()

    def _clone(self) -> None:
        """Clone the repository to a temporary directory."""
        self._temp_dir = tempfile.mkdtemp(prefix="migration-skill-")
        self.path = Path(self._temp_dir) / "repo"

        logger.info(f"Cloning repository from {self.url}...")

        cmd = ["git", "clone", "--depth", "1", self.url, str(self.path)]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr.strip()}")
            self._cleanup()
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e
        except FileNotFoundError:
            self._cleanup()
            raise RuntimeError("Git command not found. Please ensure git is installed.")

        logger.info("Repository cloned successfully")

    def _cleanup(self) -> None:
        """Remove the temporary directory unless keep_temp is True."""
        if self.keep_temp:
            logger.info(f"Temp directory retained: {self._temp_dir}")
            return

        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir: {e}")


# --- Content Processing ---

@dataclasses.dataclass
class DocumentMetadata:
    """Metadata extracted from a markdown file."""
    filename: str
    title: str
    description: str
    path: Path


@dataclasses.dataclass
class ExampleMetadata:
    """Metadata extracted from a Swift example file."""
    filename: str
    description: str
    path: Path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for use in Claude Skills. These characters are known to be incompatible."""
    return filename.replace('+', '_')


class ContentParser:
    """Parses markdown content, extracts metadata, and handles TOC parsing."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.guide_root = root_path / "Guide.docc"
        self.examples_root = root_path / "Sources" / "Examples"

    def parse_toc_order(self, toc_rel_path: str) -> List[str]:
        """Parse the TOC file to determine the correct document order."""
        toc_path = self.root_path / toc_rel_path
        if not toc_path.exists():
            raise FileNotFoundError(f"TOC file not found: {toc_path}")

        content = toc_path.read_text(encoding='utf-8')
        # Extract all document references to build the ordered list
        return re.findall(r'<doc:([^>]+)>', content)

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract title and description from a markdown file.

        Strategy:
        1. Title: First level-1 header (# Title)
        2. Description: First paragraph of text that isn't metadata or empty.
        """
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        title = file_path.stem
        description = ""

        # State machine flags
        in_metadata_block = False
        found_title = False

        for line in lines:
            stripped = line.strip()

            # Handle Metadata Blocks
            if stripped.startswith('@'):
                in_metadata_block = True
                continue

            if in_metadata_block:
                if stripped == '}' or stripped == '':
                    if stripped == '}':
                        in_metadata_block = False
                    continue
                continue

            # Skip empty lines
            if not stripped:
                continue

            # Extract Title
            if not found_title:
                if stripped.startswith('# '):
                    title = stripped[2:].strip()
                    found_title = True
                continue

            # Extract Description
            if stripped.startswith('#') or stripped.startswith('<') or stripped.startswith('>'):
                continue

            description = stripped
            break

        if not description:
            description = "No description available."

        return DocumentMetadata(
            filename=file_path.name,
            title=title,
            description=description,
            path=file_path
        )

    def extract_example_metadata(self, file_path: Path) -> ExampleMetadata:
        """
        Extract description from a Swift example file.

        Strategy: Use the first line comment or the filename.
        """
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()

        description = ""

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Check for single-line comment
            if stripped.startswith('//'):
                comment = stripped[2:].strip()
                # Skip MARK comments and file headers
                if comment and not comment.startswith('MARK:') and not comment.startswith('==='):
                    description = comment
                    break

            # Check for doc comment
            if stripped.startswith('///'):
                description = stripped[3:].strip()
                break

            # If we hit actual code, stop looking
            if not stripped.startswith('/*') and not stripped.startswith('*'):
                break

        if not description:
            # Generate description from filename
            name = file_path.stem
            # Convert CamelCase/snake_case to readable
            description = f"Example code demonstrating {name.replace('_', ' ').replace('+', ' ')}."

        # Sanitize the filename for Claude Skills compatibility
        safe_filename = sanitize_filename(file_path.name)

        return ExampleMetadata(
            filename=safe_filename,
            description=description,
            path=file_path
        )

    def get_example_files(self) -> List[Path]:
        """Get all Swift example files."""
        if not self.examples_root.exists():
            return []
        return sorted(self.examples_root.glob("*.swift"))


# --- Skill Generation ---

class SkillGenerator:
    """Orchestrates the creation of the skill directory and artifacts."""

    def __init__(self, config: Configuration, repo: GitRepository):
        self.config = config
        self.repo = repo
        self.parser = ContentParser(repo.path)
        self.doc_registry: List[DocumentMetadata] = []
        self.example_registry: List[ExampleMetadata] = []

    def build(self):
        """Main build execution flow."""
        # 1. Analyze Repository
        doc_order = self.parser.parse_toc_order(self.config.TOC_REL_PATH)

        # 2. Prepare Output Directory
        if not self.config.dry_run:
            self._prepare_directory()

        # 3. Process Content
        self._process_docs(doc_order)
        self._process_examples()

        # Copy License
        if not self.config.dry_run:
            self._copy_license()

        # 4. Generate Index
        if not self.config.dry_run:
            self._generate_skill_md()

        # 5. Create Zip Archive
        if not self.config.dry_run:
            self._create_zip_archive()

        logger.info("Packaging complete")

    def _prepare_directory(self):
        """Create clean output directory."""
        if self.config.output_path.exists():
            shutil.rmtree(self.config.output_path)

        self.config.output_path.mkdir(parents=True)

    def _create_zip_archive(self):
        """Create a zip archive of the skill directory."""
        zip_path = self.config.output_path.with_suffix('.zip')

        shutil.make_archive(
            str(self.config.output_path),
            'zip',
            root_dir=self.config.output_path.parent,
            base_dir=self.config.output_path.name
        )
        logger.info(f"Archive created: {zip_path}")

    def _process_docs(self, doc_order: List[str]):
        """Copy documentation files and extract metadata in TOC order."""

        # Pre-index all available files
        file_map: Dict[str, Path] = {}

        for md_file in self.parser.guide_root.glob("*.md"):
            # Skip the main TOC file
            if md_file.name == "MigrationGuide.md":
                continue
            file_map[md_file.stem] = md_file

        # Process in TOC order
        for doc_name in doc_order:
            if doc_name not in file_map:
                continue

            source_path = file_map[doc_name]

            # Extract Metadata
            metadata = self.parser.extract_metadata(source_path)
            self.doc_registry.append(metadata)

            # Copy File
            if not self.config.dry_run:
                dest_dir = self.config.output_path / "Guide"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_dir / source_path.name)

        if not self.doc_registry:
            raise RuntimeError("No documentation files found. Expected structure may have changed.")

        logger.info(f"Processed {len(self.doc_registry)} documentation files")

    def _process_examples(self):
        """Copy Swift example files and extract metadata."""
        example_files = self.parser.get_example_files()

        if not example_files:
            logger.warning("No example files found in Sources/Examples")
            return

        for source_path in example_files:
            # Extract Metadata
            metadata = self.parser.extract_example_metadata(source_path)
            self.example_registry.append(metadata)

            # Copy File with sanitized filename
            if not self.config.dry_run:
                dest_dir = self.config.output_path / "Examples"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_dir / metadata.filename)

        logger.info(f"Processed {len(self.example_registry)} example files")

    def _copy_license(self):
        """
        Copy the license file from the repository.

        Required to comply with the Apache 2.0 license, which mandates
        including a copy of the license with any redistribution.
        """
        for name in ["LICENSE.txt", "LICENSE.md", "LICENSE"]:
            lic_path = self.repo.path / name
            if lic_path.exists():
                shutil.copy2(lic_path, self.config.output_path / name)
                logger.info(f"Included license: {name}")
                return

        raise FileNotFoundError("No license file found in repository root. Required for packaging.")

    def _generate_skill_md(self):
        """Generate the SKILL.md index file."""

        # Frontmatter
        desc = (
            "Provides the complete Swift Concurrency Migration Guide. "
            "Use when migrating to Swift 6, resolving data-race safety errors, "
            "understanding Sendable and actor isolation, or incrementally adopting async/await."
        )

        content = [
            "---",
            f"name: {self.config.SKILL_NAME}",
            f"description: {desc}",
            "---",
            "",
            "# Swift Concurrency Migration Guide",
            "",
            "The complete content of the Swift Concurrency Migration Guide by Apple. "
            "This guide helps you migrate your code to take advantage of Swift's data-race "
            "safety guarantees and the Swift 6 language mode.",
            "",
            "## Documentation",
            ""
        ]

        # Documentation entries
        for doc in self.doc_registry:
            rel_path = f"Guide/{doc.filename}"
            safe_desc = doc.description.replace('[', '(').replace(']', ')')
            entry = f"- **{doc.title}** ([{rel_path}]({rel_path})): {safe_desc}"
            content.append(entry)

        content.append("")

        # Examples section
        if self.example_registry:
            content.append("## Code Examples")
            content.append("")
            content.append("Swift source files demonstrating migration patterns and concurrency concepts:")
            content.append("")

            for example in self.example_registry:
                rel_path = f"Examples/{example.filename}"
                safe_desc = example.description.replace('[', '(').replace(']', ')')
                entry = f"- **{example.filename}** ([{rel_path}]({rel_path})): {safe_desc}"
                content.append(entry)

            content.append("")

        # Usage Notes & License
        content.extend([
            "## Usage Notes",
            "",
            "- Start with Data Race Safety to understand the core concepts",
            "- Follow the Migration Strategy for a recommended approach",
            "- Refer to Common Problems for solutions to typical issues",
            "- Use the Code Examples as reference implementations",
            "",
            "## License & Attribution",
            "",
            "### Content License",
            "",
            "The documentation and example code in this skill are from the "
            f"[Swift Concurrency Migration Guide]({self.config.REPO_URL}), "
            "copyright Apple Inc. and the Swift project authors, "
            "distributed under the [Apache 2.0 License](LICENSE.txt).",
            "",
            "### Skill Structure License",
            "",
            "The structure and organization of this skill (this index file) is "
            "copyright Kyle Hughes, distributed under the MIT License.",
            ""
        ])

        # Write file
        out_file = self.config.output_path / "SKILL.md"
        out_file.write_text('\n'.join(content), encoding='utf-8')


# --- Entry Point ---

def signal_handler(sig, frame):
    """Handle interrupt signals gracefully."""
    print("\nOperation cancelled by user.", file=sys.stderr)
    sys.exit(0)

def main():
    """Main entry point."""
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Package the Swift Concurrency Migration Guide into a Skill."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output directory (default: ./migrating-to-swift-concurrency)"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Do not delete temporary repository clone"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate operations without writing files"
    )

    args = parser.parse_args()
    config = Configuration.from_args(args)

    try:
        with GitRepository(config.REPO_URL, config.keep_temp) as repo:
            generator = SkillGenerator(config, repo)
            generator.build()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
