# Manual Testing Guide for Smart-Tiling

This guide provides step-by-step instructions for manually testing the smart-tiling system to ensure the complete workflow functions correctly.

## Prerequisites

1. **Scroll Window Manager**: Ensure Scroll is installed and running
2. **Terminal Emulator**: Install a supported terminal (kitty, alacritty, foot)
3. **Text Editor**: Install a text editor that can be detected (neovim, vim, emacs, etc.)
4. **Smart-Tiling**: Install and configure smart-tiling

## Test Environment Setup

### 1. Install Smart-Tiling

```bash
cd /path/to/smart-tiling
pip install -e .
```

### 2. Create Test Configuration

Create the configuration file at `~/.config/smart-tiling/rules.yaml`:

```yaml
rules:
  - name: "editor_terminal"
    parent:
      app_id: ["kitty", "alacritty", "foot"]
      title_pattern: ["*nvim*", "*vim*", "*emacs*"]
    child:
      app_id: ["kitty", "alacritty", "foot"]
    actions:
      - place: below
      - size_ratio: 0.333

  - name: "browser_devtools"
    parent:
      app_id: ["firefox", "google-chrome", "chromium"]
      title_pattern: ["*localhost*", "*127.0.0.1*"]
    child:
      app_id: ["kitty", "alacritty", "foot"]
    actions:
      - place: right
      - size_ratio: 0.5

settings:
  debug: true
  rule_timeout: 15
```

### 3. Configure Scroll

Add to your Scroll config (`~/.config/scroll/config`):

```bash
exec_always smart-tiling --config ~/.config/smart-tiling/rules.yaml --debug
```

### 4. Restart Scroll

```bash
# Reload Scroll configuration
scrollctl reload
# Or restart Scroll completely
```

## Primary Workflow Tests

### Test 1: Editor → Terminal Workflow

**Objective**: Verify that a terminal opened from within an editor is placed below with correct sizing.

**Steps**:

1. **Setup**:
   ```bash
   # Open a terminal in workspace 1
   Mod4 + Return
   ```

2. **Start Editor**:
   ```bash
   # In the terminal, start your editor
   nvim ~/test_file.py
   # or
   vim ~/test_file.py
   # or
   emacs ~/test_file.py
   ```

3. **Verify Editor Detection**:
   - Check that the window title contains your editor name
   - In debug mode, you should see log messages indicating rule matching

4. **Create Child Terminal**:
   ```bash
   # From within the editor, open a terminal
   # In nvim: :terminal
   # In vim: :terminal
   # In emacs: M-x term
   # Or use Mod4+Return to create a new terminal
   Mod4 + Return
   ```

5. **Expected Behavior**:
   - New terminal should appear below the editor
   - Terminal should occupy approximately 1/3 of the vertical space
   - Editor should remain in focus initially
   - Layout should be in vertical split mode

6. **Verify Success**:
   - [ ] Terminal is positioned below editor
   - [ ] Size ratio is approximately 33%
   - [ ] Both windows are visible
   - [ ] No geometry-based tiling conflicts

### Test 2: Browser → Terminal Workflow

**Objective**: Test alternative rule with different placement direction.

**Steps**:

1. **Start Browser**:
   ```bash
   # Open browser and navigate to localhost
   firefox
   # Navigate to http://localhost:3000 or http://127.0.0.1:8080
   ```

2. **Create Terminal**:
   ```bash
   Mod4 + Return
   ```

3. **Expected Behavior**:
   - Terminal should appear to the right of browser
   - Terminal should occupy approximately 50% of horizontal space

4. **Verify Success**:
   - [ ] Terminal is positioned to the right of browser
   - [ ] Size ratio is approximately 50%
   - [ ] Horizontal split layout

## Edge Case Testing

### Test 3: Multiple Editor Windows

**Objective**: Verify behavior with multiple editor instances.

**Steps**:

1. **Create Multiple Editors**:
   ```bash
   # Terminal 1
   nvim file1.py
   ```
   ```bash
   # Terminal 2 (new terminal)
   nvim file2.py
   ```

2. **Focus Different Editors**:
   - Click on first editor window
   - Create terminal (Mod4+Return)
   - Verify placement relative to focused editor

3. **Expected Behavior**:
   - Terminal should be placed relative to the most recently focused editor
   - Previous editor-terminal relationships should be preserved

### Test 4: Rule Timeout Testing

**Objective**: Verify rule timeout expiration.

**Steps**:

1. **Focus Editor**:
   ```bash
   nvim test.py
   ```

2. **Wait for Timeout**:
   - Wait 20 seconds (longer than rule_timeout of 15 seconds)

3. **Create Terminal**:
   ```bash
   Mod4 + Return
   ```

4. **Expected Behavior**:
   - Terminal should use geometry-based tiling (not rule-based placement)
   - Should follow standard autotiling behavior

### Test 5: Workspace Switch Testing

**Objective**: Verify workspace isolation of rules.

**Steps**:

1. **Setup Rule in Workspace 1**:
   ```bash
   # In workspace 1
   nvim test.py
   ```

2. **Switch Workspace**:
   ```bash
   # Switch to workspace 2
   Mod4 + 2
   ```

3. **Create Terminal in Workspace 2**:
   ```bash
   Mod4 + Return
   ```

4. **Expected Behavior**:
   - Terminal in workspace 2 should use geometry-based tiling
   - No cross-workspace rule application

### Test 6: Invalid Configuration Handling

**Objective**: Test graceful handling of configuration errors.

**Steps**:

1. **Create Invalid Config**:
   ```yaml
   # Temporarily modify ~/.config/smart-tiling/rules.yaml
   rules:
     - name: "invalid_rule"
       # Missing required fields
   ```

2. **Restart Smart-Tiling**:
   ```bash
   scrollctl reload
   ```

3. **Check Logs**:
   ```bash
   journalctl -u scroll -f
   ```

4. **Expected Behavior**:
   - Smart-tiling should start despite invalid config
   - Error messages should be logged
   - System should fall back to geometry-based tiling

## Performance Testing

### Test 7: Response Time Verification

**Objective**: Ensure rule processing is fast (< 10ms overhead).

**Steps**:

1. **Enable Debug Logging**:
   - Ensure `debug: true` in configuration

2. **Rapid Window Creation**:
   ```bash
   # Quickly create multiple windows
   for i in {1..10}; do
     Mod4 + Return &
     sleep 0.1
   done
   ```

3. **Monitor Performance**:
   ```bash
   # Check system resource usage
   htop
   # Check smart-tiling logs for timing
   journalctl -u scroll -f | grep smart-tiling
   ```

4. **Expected Behavior**:
   - No noticeable lag in window creation
   - CPU usage should remain low
   - Memory usage should be stable

## Debugging and Verification

### Log Analysis

**Check Smart-Tiling Logs**:
```bash
# View live logs
journalctl -u scroll -f | grep smart-tiling

# View recent logs
journalctl -u scroll --since="5 minutes ago" | grep smart-tiling
```

**Common Log Messages**:
- `Smart rule matched: editor_terminal` - Rule successfully matched
- `Starting child window placement flow` - Placement initiated
- `Applied child window size ratio` - Sizing completed
- `Failed to set placement mode` - Error in mode setting

### Manual State Inspection

**Check Active Rules**:
```bash
# If debugging hooks are available
smart-tiling --status
```

**Verify Window Properties**:
```bash
# Use i3-msg or scroll-msg to inspect windows
i3-msg -t get_tree | jq '.nodes[].nodes[].nodes[]' | grep -A5 -B5 '"app_id"'
```

### Troubleshooting Common Issues

1. **Rule Not Matching**:
   - Verify window title patterns with `grep -E` 
   - Check app_id vs window_class requirements
   - Enable debug mode for detailed matching logs

2. **Placement Not Working**:
   - Verify Scroll mode commands are supported
   - Check that parent container exists
   - Ensure workspace detection is working

3. **Size Ratio Not Applied**:
   - Verify ratio is between 0.1 and 0.9
   - Check that set_size commands are executed
   - Ensure original mode restoration

## Success Criteria Checklist

### Core Functionality
- [ ] Configuration loads without errors
- [ ] Rules are parsed correctly
- [ ] Context detection identifies applications
- [ ] State manager tracks relationships
- [ ] IPC commands execute properly

### Primary Workflow
- [ ] Editor window focus event detected
- [ ] Rule is matched and stored as pending
- [ ] Terminal creation triggers rule application
- [ ] Terminal is placed in correct position (below editor)
- [ ] Size ratio is applied (33% height)
- [ ] Working directory inheritance works (if implemented)

### Edge Cases
- [ ] Multiple editor windows handled correctly
- [ ] Rule timeout expiration works
- [ ] Workspace switching isolates rules
- [ ] Invalid configuration handled gracefully
- [ ] Performance remains under 10ms overhead

### Integration
- [ ] No conflicts with geometry-based tiling
- [ ] Fallback to geometry tiling when rules don't match
- [ ] State cleanup prevents memory leaks
- [ ] System stability maintained

## Test Environment Variations

### Different Terminal Emulators
Test with each supported terminal:
- [ ] kitty
- [ ] alacritty  
- [ ] foot

### Different Editors
Test with each supported editor:
- [ ] neovim
- [ ] vim
- [ ] emacs
- [ ] other text editors

### Different Display Configurations
- [ ] Single monitor
- [ ] Multiple monitors
- [ ] Different resolutions
- [ ] Different scaling factors

## Reporting Results

When reporting test results, include:

1. **Environment Details**:
   - OS version
   - Scroll version
   - Terminal emulator and version
   - Editor and version

2. **Configuration Used**:
   - Full rules.yaml content
   - Any custom Scroll configuration

3. **Test Results**:
   - Which tests passed/failed
   - Screenshots or videos of behavior
   - Relevant log excerpts

4. **Performance Metrics**:
   - Window creation response times
   - Memory usage observations
   - CPU usage during testing

5. **Issues Found**:
   - Detailed steps to reproduce
   - Expected vs actual behavior
   - Workarounds discovered

This comprehensive testing ensures that smart-tiling works correctly across different configurations and use cases, validating the system for the 0.0.1 release.