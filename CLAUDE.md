# Claude Code Configuration

This file contains configuration and commands for working with the Word2Git project in Claude Code.

## Development Commands

### Setup and Installation
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black word2git/

# Type checking
mypy word2git/

# Linting
flake8 word2git/
```

### Testing Commands
```bash
# Run example usage
python examples/example_usage.py

# Test CLI commands
word2git --help
word2git init
word2git status

# Validate installation
python -c "from word2git import Word2GitProcessor; print('Import successful')"
```

### Build and Package
```bash
# Build package
python setup.py sdist bdist_wheel

# Install locally
pip install dist/word2git-*.whl

# Clean build artifacts
rm -rf build/ dist/ word2git.egg-info/
```

## Project Structure

```
word2git/
├── word2git/           # Main package
│   ├── __init__.py     # Package exports
│   ├── core.py         # Main processor
│   ├── ingest.py       # Word document ingestion
│   ├── extract.py      # Content Controls extraction
│   ├── render.py       # Multi-variant rendering
│   ├── validate.py     # Round-trip validation
│   └── cli.py          # Command-line interface
├── filters/            # Pandoc Lua filters
│   └── normalize.lua   # Document normalization
├── examples/           # Usage examples
│   └── example_usage.py
├── tests/              # Test suite (to be created)
├── setup.py           # Package configuration
├── requirements.txt   # Dependencies
├── README.md          # Documentation
├── CLAUDE.md          # This file
└── .gitignore         # Git ignore rules
```

## Common Development Tasks

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Add implementation in appropriate module
3. Add tests in `tests/` directory
4. Update CLI if needed in `cli.py`
5. Update documentation in README.md
6. Test with: `python examples/example_usage.py`

### Working with Pandoc
```bash
# Test pandoc conversion manually
pandoc input.docx -t markdown+pipe_tables+yaml_metadata_block --wrap=none --eol=lf -o output.md

# Test with Lua filter
pandoc input.docx -t markdown --lua-filter=filters/normalize.lua -o output.md

# Convert back to Word
pandoc output.md -t docx --reference-doc=reference.docx -o final.docx
```

### Debugging Content Controls
```bash
# Extract and examine Content Controls
word2git extract document.docx -o debug_controls.yaml
cat debug_controls.yaml

# Test template rendering
python -c "
from word2git import VariantRenderer
renderer = VariantRenderer('docs/', 'build/')
results = renderer.render_variants('template.md.j2', ['data/test.yaml'])
print(results)
"
```

### Validation and Testing
```bash
# Full validation workflow
word2git ingest test_document.docx
word2git render template.md.j2 --all-data
word2git validate --roundtrip -m docs/test_document.md
word2git validate --templates

# Check workspace status
word2git status
```

## Dependencies

### Core Dependencies
- `pypandoc>=1.11` - Pandoc Python wrapper
- `jinja2>=3.1.0` - Template engine
- `pyyaml>=6.0` - YAML processing
- `lxml>=4.9.0` - XML processing for Content Controls
- `click>=8.0.0` - CLI framework

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `black>=22.0.0` - Code formatter
- `flake8>=4.0.0` - Linter
- `mypy>=0.991` - Type checker

### External Dependencies
- Pandoc - Document conversion engine
- LaTeX (optional) - For PDF output

## Environment Setup

### macOS
```bash
# Install system dependencies
brew install pandoc
brew install --cask mactex  # For PDF support

# Install Python dependencies
pip install -e ".[dev]"
```

### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended

# Install Python dependencies
pip install -e ".[dev]"
```

## Troubleshooting

### Common Issues

1. **Pandoc not found**
   - Install Pandoc system-wide
   - Check `pandoc --version`

2. **Content Controls not extracting**
   - Ensure Word document has Structured Document Tags
   - Check Developer tab is enabled in Word
   - Verify tags have proper names

3. **Template rendering fails**
   - Check Jinja2 syntax in template
   - Validate YAML data files
   - Use `word2git validate --templates`

4. **Round-trip validation fails**
   - Check Lua filter normalization
   - Compare with `diff` command
   - Adjust pandoc options if needed

### Debug Mode
```bash
# Enable verbose output
export WORD2GIT_DEBUG=1
word2git ingest document.docx

# Check intermediate files
ls -la /tmp/word2git_*
```

## Contributing Guidelines

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write docstrings for public APIs
4. Add tests for new functionality
5. Update documentation as needed
6. Use semantic commit messages

### Code Style
```bash
# Auto-format before committing
black word2git/
flake8 word2git/
mypy word2git/
```

## Release Process

1. Update version in `__init__.py` and `setup.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag v0.x.y`
5. Build and publish: `python setup.py sdist bdist_wheel`
- This project is licensed under GPL v2
- The current year is 2025