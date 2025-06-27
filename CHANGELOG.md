# Smart-Tiling Changelog

## v0.0.1 (2025-06-25) - Initial Release

### Major Features
- **Context-Aware Window Placement**: Intelligent placement based on parent-child window relationships
- **Generic Rule Engine**: Configurable YAML-based rules for any application combination
- **Scroll Window Manager Integration**: Enhanced IPC support for Scroll-specific features
- **Backward Compatibility**: Preserves original autotiling behavior as fallback

### Core Components
- **Rule-Based Configuration**: Flexible YAML rules with parent/child matching criteria
- **State Management**: Thread-safe tracking of window relationships and pending rules
- **Context Detection**: Application identification via app_id, window_class, and title patterns
- **Layout Management**: Direction-based placement (below, above, left, right) with configurable sizing

### Implementation Highlights
- Removed hardcoded application-specific logic for generic rule-driven system
- Complete integration testing framework with mock infrastructure
- Performance optimized (< 10ms rule processing overhead)
- Comprehensive edge case handling (timeouts, workspace isolation, invalid configs)

### Testing & Documentation
- Integration test suite with end-to-end workflow validation
- Manual testing guide with step-by-step procedures
- Mock i3ipc infrastructure for reliable testing
- Performance benchmarks and success criteria

### Configuration Example
```yaml
rules:
  - name: "editor_terminal"
    parent:
      app_id: ["kitty", "alacritty"]
      title_pattern: ["*nvim*", "*vim*"]
    child:
      app_id: ["kitty", "alacritty"] 
    actions:
      - place: below
      - size_ratio: 0.333

settings:
  debug: false
  rule_timeout: 15
```

### Breaking Changes
- Renamed from autotiling to smart-tiling
- New configuration format (YAML-based rules)
- Application-specific logic moved to configuration

### Dependencies
- i3ipc >= 2.0.1
- PyYAML
- Python >= 3.6

---

## Original Autotiling History

Based on [autotiling](https://github.com/nwg-piotr/autotiling) by Piotr Miller.

### v1.5 (autotiling master)
- added `Event.BINDING` subscription [#26](https://github.com/nwg-piotr/autotiling/issues/26) @mtshrmn

### v1.4 (autotiling 2021-02-24)
- nwg-panel integration: args.workspaces saved to /tmp/autotiling on start

### v1.3 (autotiling 2021-01-08)
- added `--workspaces` argument to restrict autotiling to certain workspaces @riscie
- code formatting and arguments cleanup

### v1.2 (autotiling 2021-01-04)
- added --version argument @nschloe
- allowed autotiling to be run as a script directly @Lqp1

### v1.1 (autotiling 2020-07-21)
- added proper Python package structure so that could be published on PyPi 
[#14](https://github.com/nwg-piotr/autotiling/pull/14) @nschloe

### v1.0 (autotiling 2020-07-19)
- changed fullscreen mode detection to reflect changes in sway 1.5 
[#11](https://github.com/nwg-piotr/autotiling/pull/11) @ammgws

### v0.9 (autotiling 2020-04-08)
- bug in debugging fixed [#6](https://github.com/nwg-piotr/autotiling/pull/6)

### v0.8 (autotiling 2020-03-21)
- `--debug` option added [#5](https://github.com/nwg-piotr/autotiling/pull/5) @ammgws

### v0.7 (autotiling 2020-02-20)
- Only run command if absolutely necessary [#3](https://github.com/nwg-piotr/autotiling/pull/3) @ammgws

### v0.5 (autotiling 2020-02-19)
- Check if con exists before querying submembers [#2](https://github.com/nwg-piotr/autotiling/pull/2) @ammgws

### v0.4 (autotiling 2019-12-11)
- ignoring stacked layouts added [#1](https://github.com/nwg-piotr/autotiling/pull/1) @travankor

### v0.3 (autotiling 2019-09-26)
- unnecessary Event.WINDOW_NEW subscription removed

### v0.2 (autotiling 2019-09-25)
- tabbed layouts and full screen mode excluded
- fullscreen_mode detection diversified for i3 and sway
