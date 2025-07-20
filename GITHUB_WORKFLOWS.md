# GitHub Actions Workflows

This repository includes a GitHub Actions workflow for automated cross-platform building and testing.

## Available Workflow

### `build-simple.yml` - Cross-Platform Build
**File**: `.github/workflows/build-simple.yml`

**Features:**
- Builds for Linux, Windows, and macOS
- Single Python version (3.11)
- Separate jobs for each platform
- Automatic release package creation
- Cross-platform compatibility testing

**Triggers:**
- Push of version tags (e.g., `v0.01`, `v1.0.0`, `v2.1.3`)
- Manual workflow dispatch

**Output:**
- Individual platform builds
- Combined release package with README

## Workflow Details

| Feature | Details |
|---------|---------|
| Python Version | 3.11 only |
| Build Time | ~8-12 minutes |
| Complexity | Low |
| Artifacts | Single release package |
| Testing | Cross-platform tests |

## Usage

### Creating Releases
To trigger a build and create a release:

1. **Use the release script** (recommended):
   ```bash
   # Suggest next version
   python create_release.py --suggest
   
   # Create a specific version
   python create_release.py v0.01
   python create_release.py v1.0.0
   ```

2. **Manual git commands**:
   ```bash
   git tag v0.01
   git push origin v0.01
   ```

3. **Manual workflow trigger**:
   - Go to Actions tab in GitHub
   - Select the workflow
   - Click "Run workflow"
   - Choose branch and options

### Version Tag Format
Supported formats:
- `v0.01`, `v0.02`, `v0.10` (patch versions)
- `v1.0.0`, `v1.1.0`, `v2.0.0` (semantic versions)
- `v1.0.1`, `v1.2.3` (patch increments)

## Artifacts

### Build Artifacts
- **Linux**: `metavinci-linux` (executable)
- **Windows**: `metavinci-windows.exe` (executable)
- **macOS**: `metavinci-macos` (executable)

### Release Assets
When pushing a version tag, the workflow automatically:
1. Downloads all build artifacts
2. Creates a release package
3. Includes installation instructions
4. Uploads as release assets

**Note**: The release package is created automatically when you push a tag. You can then manually create a GitHub release and attach these assets if desired.

## Platform-Specific Notes

### Linux (Ubuntu)
- Uses `ubuntu-latest` runner
- Executable permissions automatically set
- No additional dependencies required

### Windows
- Uses `windows-latest` runner
- Requires Visual Studio Build Tools (included in runner)
- Creates `.exe` files
- May trigger antivirus warnings

### macOS
- Uses `macos-latest` runner
- May require code signing for distribution
- Gatekeeper may block unsigned executables
- Uses `.icns` icon format

## Troubleshooting

### Common Issues

1. **Build Fails on Windows**
   - Check if all dependencies are available
   - Ensure PyInstaller is compatible
   - Verify icon file format (.ico)

2. **Build Fails on macOS**
   - Check Python version compatibility
   - Verify icon file format (.icns)
   - May need code signing for distribution

3. **Artifacts Not Found**
   - Check build output paths
   - Verify file names match expected patterns
   - Ensure build completed successfully

### Debugging

1. **View Workflow Logs**
   - Go to Actions tab
   - Click on failed workflow
   - Check individual step logs

2. **Local Testing**
   - Test builds locally first
   - Use `test_cross_platform.py`
   - Verify all dependencies

3. **Workflow Validation**
   - Use GitHub's workflow validation
   - Check YAML syntax
   - Verify action versions

## Customization

### Adding New Platforms
1. Add platform to workflow jobs
2. Update build commands
3. Add platform-specific paths
4. Test locally first

### Modifying Build Process
1. Edit build script parameters
2. Update PyInstaller options
3. Add custom build steps
4. Modify artifact paths

### Environment Variables
You can add environment variables for:
- API keys
- Build configurations
- Platform-specific settings

## Best Practices

1. **Use Caching**
   - Cache pip dependencies
   - Cache build artifacts when possible
   - Use appropriate cache keys

2. **Optimize Build Time**
   - Use parallel jobs when possible
   - Minimize dependency installation
   - Keep builds focused

3. **Security**
   - Don't commit secrets to workflows
   - Use GitHub secrets for sensitive data
   - Validate all inputs

4. **Testing**
   - Include automated tests
   - Test on all target platforms
   - Validate build artifacts

## Monitoring

### Workflow Status
- Check Actions tab for build status
- Monitor build times and success rates
- Review failed builds promptly

### Performance
- Track build duration
- Monitor resource usage
- Optimize slow builds

### Quality
- Run tests before builds
- Validate build artifacts
- Check for regressions 