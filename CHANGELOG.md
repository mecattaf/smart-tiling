# Smart-Tiling Changelog

## 0.0.1 (2025-06-27)


### ⚠ BREAKING CHANGES

* Renamed from autotiling to smart-tiling

### Features

* add manifest for release-please ([b73cae6](https://github.com/mecattaf/smart-tiling/commit/b73cae61dd0e739dbefb9b5744ed0ba0aee95b26))
* add state management and command building modules ([bf3987a](https://github.com/mecattaf/smart-tiling/commit/bf3987a45f008408b57ac3b9f390de6c7801d788))
* complete smart-tiling generic rule engine for v0.0.1 ([6bc2089](https://github.com/mecattaf/smart-tiling/commit/6bc2089548de3093d54ea63e28083b4e245bf1da))
* complete smart-tiling v0.0.1 implementation ([40c5693](https://github.com/mecattaf/smart-tiling/commit/40c56930cb68f319d8a3c273e289f945011ba4bd))
* implement complete generic app detection system ([6a76963](https://github.com/mecattaf/smart-tiling/commit/6a76963e6f5c1fde3ab0112ab986e58f6312eba8)), closes [#5](https://github.com/mecattaf/smart-tiling/issues/5)
* implement config schema validation system ([861d9f6](https://github.com/mecattaf/smart-tiling/commit/861d9f64fab086f170d5a9b700919f7e073312e8))
* implement config schema validation system ([2f30e79](https://github.com/mecattaf/smart-tiling/commit/2f30e79ba60d9e5a8be25f8cac1c503e969d4e04))
* implement integration testing and prepare 0.0.1 release ([073f728](https://github.com/mecattaf/smart-tiling/commit/073f728c4697516e88cbdb87b0aa224374010d04))
* implement integration testing and prepare 0.0.1 release ([d1b28fe](https://github.com/mecattaf/smart-tiling/commit/d1b28fe2942ddb0e9daa3470dd81dd970302c5ea))
* implement rule engine for window matching ([ff7fd4f](https://github.com/mecattaf/smart-tiling/commit/ff7fd4ff8c2ea61a22e4f519163c7c34f453ae3a))
* implement rule engine for window matching ([9d9dd58](https://github.com/mecattaf/smart-tiling/commit/9d9dd587e0fa8735610e89c78c632e929d3763e9))
* implement Scroll layout manipulation ([83f30c4](https://github.com/mecattaf/smart-tiling/commit/83f30c42f188902d2efe7ca7b453b2bfc752641e))
* implement Scroll layout manipulation with comprehensive tests ([54f029d](https://github.com/mecattaf/smart-tiling/commit/54f029d40f546c606c5600d9de4d3e3c714f25b2)), closes [#9](https://github.com/mecattaf/smart-tiling/issues/9)
* implement YAML config parser for smart-tiling rules ([30b8d9c](https://github.com/mecattaf/smart-tiling/commit/30b8d9c912c6d24f44ba6363a8ed007ba120abf5))
* implement YAML config parser for smart-tiling rules ([b1c08d4](https://github.com/mecattaf/smart-tiling/commit/b1c08d4b9fa79d3239bb06aae72997b0c3842541)), closes [#6](https://github.com/mecattaf/smart-tiling/issues/6)
* initial release ([05c0248](https://github.com/mecattaf/smart-tiling/commit/05c024898d1eba41fd9e8881e7dea0e140743c2b))
* initial smart-tiling structure with core functionality ([7d1a696](https://github.com/mecattaf/smart-tiling/commit/7d1a69672bbfb0eb7240714c78b1f8abf0627d78))
* no label for release-please ([2e9504e](https://github.com/mecattaf/smart-tiling/commit/2e9504eb046ba7f23a9aa3594064484286d00b71))
* no label for release-please 3 ([ac832ef](https://github.com/mecattaf/smart-tiling/commit/ac832ef35641232084af1f3b423686981f152ded))
* no label for release-please 4 ([dc77cdb](https://github.com/mecattaf/smart-tiling/commit/dc77cdb01dd1eef35fec64043b85aeb6aa27eb9d))
* trigger first release ([0958fc1](https://github.com/mecattaf/smart-tiling/commit/0958fc1aa339d0041fcaf7db936625e2ef8bc574))


### Bug Fixes

* cleanup readme ([2ee07eb](https://github.com/mecattaf/smart-tiling/commit/2ee07eb0f63496ec9d4b5e4209fec81605f6a42f))
* correct author mentioned in setup.cfg ([6f0d1dc](https://github.com/mecattaf/smart-tiling/commit/6f0d1dc234786e910c458e5a9e27715515ed088c))
* correct release-please config path ([3b7f3ad](https://github.com/mecattaf/smart-tiling/commit/3b7f3ad63af5d95c47687cf896565a487df73d9d))
* fixes bug introduced in PR where autotiling would not be active if no workspaces were passed ([707e9a5](https://github.com/mecattaf/smart-tiling/commit/707e9a5104f1e3771f8c52ad746cc0975aeafa8c))


### Miscellaneous Chores

* bootstrap releases for path . ([b685b52](https://github.com/mecattaf/smart-tiling/commit/b685b52eb68e20ffa718c3bc349de6259f8fa53f))

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
