# The Unofficial Swift Concurrency Migration Skill

[![Agent Skill](https://img.shields.io/badge/Agent_Skill-555?logo=claude)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
[![Latest Release](https://img.shields.io/github/v/release/kylehughes/the-unofficial-swift-concurrency-migration-skill)](https://github.com/kylehughes/the-unofficial-swift-concurrency-migration-skill/releases)

*[Swift Concurrency Migration Guide](https://www.swift.org/migration/documentation/migrationguide/), packaged as a Skill for LLMs.*

## About

The Unofficial Swift Concurrency Migration Skill provides the complete content of the [Swift Concurrency Migration Guide](https://www.swift.org/migration/documentation/migrationguide/) in the structured Skill format used by Claude. This includes all documentation articles and Swift code examples.

## Installation

### Claude Code

#### Personal Usage

To install this Skill for your personal use in Claude Code:

1. Add the marketplace:
   ```bash
   /plugin marketplace add kylehughes/the-unofficial-swift-concurrency-migration-skill
   ```

2. Install the Skill:
   ```bash
   /plugin install migrating-to-swift-concurrency-skill@the-unofficial-swift-concurrency-migration-skill
   ```

#### Project Configuration

To automatically provide this Skill to everyone working in a repository, configure the repository's `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "migrating-to-swift-concurrency-skill@the-unofficial-swift-concurrency-migration-skill": true
  },
  "extraKnownMarketplaces": {
    "the-unofficial-swift-concurrency-migration-skill": {
      "source": {
        "source": "github",
        "repo": "kylehughes/the-unofficial-swift-concurrency-migration-skill"
      }
    }
  }
}
```

When team members open the project, Claude Code will prompt them to install the Skill.

### Manual Installation

You can download the pre-packaged release for use in other environments (e.g. Claude Desktop).

1. Go to the [Releases](https://github.com/kylehughes/the-unofficial-swift-concurrency-migration-skill/releases) page.
2. Download the `migrating-to-swift-concurrency.zip` file from the latest release.
3. Import the Skill into your environment (e.g. ask Claude how).

The raw Skill content is also available in this repository's `migrating-to-swift-concurrency` directory.

## Releases

This Skill is automatically updated nightly to match the official documentation. A new version is released only when the upstream content changes.

Version numbers follow the format `YYYYMMDD` (e.g., `20251206`).

## Development

### Build from Source

You can generate the Skill package locally using the provided Python script. The script has no external dependencies and is what is used to generate the pre-packaged releases.

```bash
python3 package.py
```

This will clone the official repository and generate a `migrating-to-swift-concurrency` directory and `migrating-to-swift-concurrency.zip` archive in your current working directory.

### Options

| Option | Description |
| :--- | :--- |
| `--output DIR`, `-o DIR` | Specify output directory (default: `./migrating-to-swift-concurrency`) |
| `--keep-temp` | Do not delete the temporary git clone after packaging |
| `--dry-run` | Simulate operations without writing files |

## Contributions

The Unofficial Swift Concurrency Migration Skill is not accepting source contributions at this time. Bug reports will be considered.

## Author

[Kyle Hughes](https://kylehugh.es)

[![Bluesky][bluesky_image]][bluesky_url]  
[![LinkedIn][linkedin_image]][linkedin_url]  
[![Mastodon][mastodon_image]][mastodon_url]

[bluesky_image]: https://img.shields.io/badge/Bluesky-0285FF?logo=bluesky&logoColor=fff
[bluesky_url]: https://bsky.app/profile/kylehugh.es
[linkedin_image]: https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=fff
[linkedin_url]: https://www.linkedin.com/in/kyle-hughes
[mastodon_image]: https://img.shields.io/mastodon/follow/109356914477272810?domain=https%3A%2F%2Fmister.computer&style=social
[mastodon_url]: https://mister.computer/@kyle

## License & Attribution

The Unofficial Swift Concurrency Migration Skill is available under the **MIT License**. See `LICENSE` for details.

The content contained within the generated Skill is sourced from the [Swift Concurrency Migration Guide](https://github.com/swiftlang/swift-migration-guide) by Apple Inc. and the Swift project authors, and is distributed under the **Apache 2.0 License**.
