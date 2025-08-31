# Loading Animation Refactoring Plan

## Overview
This document outlines the plan to enhance the `AnimatedLoadingWindow` class in `metavinci.py` by incorporating the robust features from the `LoadingSplash` class in `test_loading.py`, while maintaining the existing class structure and interface.

## Current Implementation Analysis

### `AnimatedLoadingWindow` (metavinci.py)
- Extends `QWidget`
- Current Features:
  - GIF animation support
  - Custom window sizing
  - Animation speed control
  - Text label for status messages
  - Automatic centering
  - Keep-alive timer for animation

### `LoadingSplash` (test_loading.py) - Features to Port
- Robust Features to Integrate:
  - More reliable GIF loading and error handling
  - Automatic window positioning
  - Transparent background support
  - Progress update capability
  - Better resource path resolution

## Refactoring Steps

### 1. Preparation
- [ ] Create backup of `metavinci.py`
- [ ] Document all current usages of `AnimatedLoadingWindow`
- [ ] Identify all methods and properties in `AnimatedLoadingWindow` that need to be maintained

### 2. Implementation Plan

#### 2.1. Update `AnimatedLoadingWindow` Class
- [ ] Change base class from `QWidget` to `QSplashScreen` for better animation support
- [ ] Integrate robust GIF loading from `LoadingSplash`
- [ ] Maintain existing method signatures for backward compatibility

#### 2.2. Update Internal Implementation
- [ ] Implement robust GIF loading and error handling from `LoadingSplash`
- [ ] Update window positioning and transparency handling
- [ ] Maintain existing public API methods:
  - `start_animation()` - Keep as is for compatibility
  - `stop_animation()` - Call parent's close()
  - `set_animation_speed()` - Maintain for backward compatibility

#### 2.3. Update All Usages
- [ ] Find all instances of `AnimatedLoadingWindow` in the codebase
- [ ] Replace each instance with `LoadingSplash`
- [ ] Update method calls to match new API

### 3. Testing
- [ ] Test on all supported platforms (Windows, macOS, Linux)
- [ ] Verify GIF loading from different locations
- [ ] Test error handling for missing GIF files
- [ ] Verify window behavior (positioning, focus, etc.)

## Code Changes Required

### Methods to Add/Update in `AnimatedLoadingWindow`
```python
def update_text(self, text):
    """Update the loading text (new method)."""
    self.showMessage(text, Qt.AlignBottom | Qt.AlignCenter, Qt.white)

def _find_loading_gif(self):
    """Robustly find the loading GIF file (internal method)."""
    # Implementation from test_loading.py's find_loading_gif method
    pass
```

### Usage Example
```python
# Before and After (API remains the same)
loading = AnimatedLoadingWindow(self, "Processing...", "path/to/loading.gif")
loading.start_animation()
loading.set_animation_speed(150)  # Still works
loading.update_text("Still processing...")  # New method
```

## Migration Checklist
- [ ] All existing code using `AnimatedLoadingWindow` continues to work without changes
- [ ] New features from `LoadingSplash` are properly integrated
- [ ] Code tested on all target platforms
- [ ] Documentation updated to reflect new capabilities
- [ ] Performance and memory usage verified

## Benefits
- Maintains backward compatibility with existing code
- Gains robust GIF loading and error handling
- Better cross-platform compatibility
- Improved error handling and fallback behavior
- More maintainable implementation

## Potential Risks
- Changes in window behavior due to `QSplashScreen` base class
- May need to adjust window styling to match existing UI
- Need to ensure all existing method calls continue to work as expected

## Rollback Plan
If issues are found:
1. Revert to the backup of `metavinci.py`
2. Restore any modified files from version control
3. Verify all functionality is restored
