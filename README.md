# Smart-Tiling

Context-aware window tiling for Scroll window manager. Smart-tiling extends the original [autotiling](https://github.com/nwg-piotr/autotiling) with intelligent window placement based on application context and user behavior patterns.

## Features

- **Context-Aware Placement**: Automatically detects applications and places new windows intelligently
- **Neovim Terminal Integration**: Specially optimized for Neovim workflows with terminal integration
- **Scroll Window Manager Support**: Extended IPC support for Scroll-specific features
- **Rule-Based Configuration**: Flexible YAML configuration for custom placement rules
- **Backward Compatibility**: Preserves original autotiling behavior as fallback

## Quick Start

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Add to your Scroll config:
   ```bash
   exec_always smart-tiling --config ~/.config/smart-tiling/rules.yaml
   ```

3. Test the installation:
   ```bash
   smart-tiling --help
   ```

## Configuration

Create `~/.config/smart-tiling/rules.yaml`:

```yaml
rules:
  - name: "neovim_terminal"
    parent:
      app_id: ["kitty"]
      title_pattern: ["*nvim*"]
    child:
      app_id: ["kitty"]
    actions:
      - set_mode: v after
      - size_ratio: 0.333
      - inherit_cwd: true

settings:
  debug: false
  rule_timeout: 10
```

## Architecture

Smart-tiling is built with a modular architecture:

- **Core Modules**: Geometry, context detection, process analysis, state management, rule engine
- **Scroll Integration**: IPC extensions, layout manipulation, command building
- **Configuration**: YAML parsing, schema validation, hot-reload support

See [`ai_docs/architecture.md`](ai_docs/architecture.md) for detailed architectural documentation.

## Usage

```bash
smart-tiling [-h] [-d] [-v] [-o [OUTPUTS ...]] [-w [WORKSPACES ...]]
            [-l LIMIT] [-sw SPLITWIDTH] [-sh SPLITHEIGHT] [-sr SPLITRATIO]
            [-e [EVENTS ...]] [--config CONFIG]

Context-aware window tiling for Scroll window manager

options:
  -h, --help            show this help message and exit
  -d, --debug           print debug messages to stderr
  -v, --version         display version information
  -o [OUTPUTS ...], --outputs [OUTPUTS ...]
                        restricts smart-tiling to certain outputs
  -w [WORKSPACES ...], --workspaces [WORKSPACES ...]
                        restricts smart-tiling to certain workspaces
  -l LIMIT, --limit LIMIT
                        limit how often autotiling will split a container
  --config CONFIG       path to configuration file
```

## Smart Features

### Neovim Terminal Integration

When you open a terminal from within Neovim, smart-tiling:
1. Detects the Neovim context
2. Places the terminal in vertical split mode
3. Sizes it to 33% width by default
4. Inherits the working directory from Neovim

### Rule-Based Placement

Define custom rules for different application combinations:
- Parent-child window relationships
- Pattern matching on titles and app IDs
- Configurable actions (mode, size, focus)
- Priority and conflict resolution

## Development

This project maintains the original autotiling functionality while adding smart features. The codebase is structured for easy extension and testing.

### Project Structure

```
smart_tiling/
├── core/           # Core functionality
├── scroll/         # Scroll integration
├── config/         # Configuration handling
└── main.py         # Entry point
```

## Attribution

Smart-tiling is built upon the excellent [autotiling](https://github.com/nwg-piotr/autotiling) project by Piotr Miller. The original geometry-based tiling logic is preserved and enhanced with context-aware features.

Original autotiling:
- Copyright: 2019-2021 Piotr Miller & Contributors
- License: GPL-3.0-or-later
- Project: https://github.com/nwg-piotr/autotiling

## License

GPL-3.0-or-later (same as original autotiling)