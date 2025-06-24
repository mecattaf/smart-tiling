# Setup Context

First, read these files in order:
1. `/ai_docs/README.md` - Overview of AI documentation
2. `/ai_docs/business-logic.md` - Understanding the why
3. `/ai_docs/architecture.md` - System design
4. `/ai_docs/neovim-terminal-spec.md` - Primary use case

Then examine the codebase:
- Run `find smart_tiling -name "*.py" | head -20` to see structure
- Read `/smart_tiling/main.py` to understand entry point
- Check `/tests/test_neovim_terminal.py` for expected behavior

Remember: Version 0.0.1 only needs Neovim+terminal working perfectly.
