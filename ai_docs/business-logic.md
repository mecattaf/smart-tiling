# Business Logic and Context

## The Problem
User opens Neovim, presses Mod4+Return expecting a terminal below (like VSCode).
Instead, Scroll opens it to the right. This breaks the workflow.
Scroll opens new windows following a set direction in the .config file, we want to make this contextual based on the currently focused window.

## The Solution
Detect when the focused window is Neovim, intercept terminal creation,
place it below with proper sizing and working directory.

## Why This Matters
- Developers expect IDE-like behavior
- Scroll's unique features make this possible
- No other tiling WM does context-aware placement

## Success Metrics
1. 100% reliable Neovim+terminal placement
2. Zero regressions in normal autotiling
3. <10ms performance overhead
4. Intuitive configuration

## Non-Goals for v0.0.1
- Other applications (Browser, IDEs)
- Multi-monitor support
- Dynamic learning
- GUI configuration
