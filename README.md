# Word2Git

A Python module for Word-first document workflows with Git integration. Enables a two-track pipeline for maintaining Word documents as Git source of truth while supporting round-trip editing and multi-variant rendering.

## Features

- **Word-first ingestion**: Convert .docx files to canonical Markdown with deterministic conversion
- **Content Controls extraction**: Extract Structured Document Tags (SDTs) for data-driven templates
- **Multi-variant rendering**: Generate multiple document versions from templates and data files
- **Round-trip validation**: Ensure document fidelity through conversion cycles
- **Git-friendly**: Markdown source with proper normalization for version control
- **Lua filtering**: Extensible normalization through Pandoc Lua filters

## Installation

```bash
pip install -e .
```

### Requirements

- Python 3.8+
- Pandoc (for document conversion)
- LaTeX (optional, for PDF output)

Install Pandoc:
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc

# Windows
# Download from https://pandoc.org/installing.html
```

## Quick Start

### 1. Initialize a workspace

```bash
word2git init
```

This creates the following structure:
```
.
├── docs/           # Canonical Markdown and templates
├── data/           # YAML data files for variants
├── templates/      # Reference Word documents
├── build/          # Generated outputs
├── assets/         # Images and media
├── Makefile        # Automation commands
└── README.md       # Documentation
```

### 2. Ingest a Word document

```bash
word2git ingest document.docx
```

This will:
- Convert the .docx to canonical Markdown
- Extract any Content Controls as YAML data
- Create a reference template for styling
- Generate a Jinja2 template if Content Controls are found

### 3. Create data variants

Edit the generated YAML files in `data/` or create new ones:

```yaml
# data/client_a.yaml
project_name: "Website Redesign"
client_name: "Acme Corp"
contact_email: "jack_white@example.com"
budget: "$50,000"
```

### 4. Render variants

```bash
word2git render template.md.j2 --all-data --format md docx pdf
```

This generates multiple output formats for each data file.

### 5. Validate conversions

```bash
word2git validate --roundtrip -m docs/canonical.md
word2git validate --templates
```

## Python API

### Basic Usage

```python
from word2git import Word2GitProcessor

# Initialize processor
processor = Word2GitProcessor("./my_workspace")

# Ingest Word document
results = processor.ingest_document("document.docx")

# Render variants
variants = processor.render_variants(
    template_name="template.md.j2",
    data_files=["data/client_a.yaml", "data/client_b.yaml"],
    formats=["md", "docx", "pdf"]
)

# Validate round-trip conversion
validation = processor.validate_roundtrip("docs/canonical.md")
```

### Advanced Usage

```python
from word2git import WordIngester, SDTExtractor, VariantRenderer

# Custom ingestion with Lua filter
ingester = WordIngester(lua_filter_path="filters/custom.lua")
result = ingester.ingest_docx("document.docx", "output/")

# Extract Content Controls
extractor = SDTExtractor()
controls = extractor.extract_from_docx("document.docx")
extractor.save_to_yaml(controls, "data/extracted.yaml")

# Render with custom templates
renderer = VariantRenderer("templates/", "output/")
rendered = renderer.render_all_formats("custom.md.j2", ["data/vars.yaml"])
```

## Content Controls

Word2Git can extract Structured Document Tags (Content Controls) from Word documents:

1. **Insert Content Controls** in Word via Developer tab → Controls
2. **Set Tag names** like `project.name`, `client.contact`
3. **Add display text** that will be extracted as template variables

Example Word Content Control:
- Tag: `project.name`
- Display text: `My Project Name`

Becomes Jinja2 template variable:
```markdown
# Project: {{ project_name }}
```

With corresponding YAML data:
```yaml
project_name: "My Project Name"
```

## Lua Filters

Customize document normalization with Pandoc Lua filters:

```lua
-- filters/custom.lua
function Header(elem)
    -- Ensure headers have stable IDs
    if not elem.identifier or elem.identifier == "" then
        elem.identifier = "section-" .. pandoc.utils.stringify(elem.content):lower():gsub("%s+", "-")
    end
    return elem
end
```

Use with:
```bash
word2git ingest document.docx --filter filters/custom.lua
```

## Workflow Examples

### Single Document Workflow

```bash
# 1. Ingest Word document
word2git ingest report.docx

# 2. Edit the canonical Markdown
vim docs/report.md

# 3. Regenerate Word document
word2git render report.md.j2 --data data/report.yaml --format docx
```

### Multi-Variant Workflow

```bash
# 1. Ingest template document with Content Controls
word2git ingest template.docx

# 2. Create multiple data files
cp data/template.yaml data/client_a.yaml
cp data/template.yaml data/client_b.yaml
# Edit each data file...

# 3. Render all variants
word2git render template.md.j2 --all-data

# 4. Results in build/
ls build/
# client_a.md  client_a.docx  client_a.pdf
# client_b.md  client_b.docx  client_b.pdf
```

### CI/CD Integration

```bash
# Validate in CI pipeline
word2git validate --templates
word2git validate --roundtrip -m docs/canonical.md

# Build all outputs
make build

# Check for changes
git diff --exit-code build/
```

## File Structure

```
workspace/
├── docs/
│   ├── canonical.md      # Main Markdown source
│   └── template.md.j2    # Jinja2 template
├── data/
│   ├── client_a.yaml     # Data for variant A
│   └── client_b.yaml     # Data for variant B
├── templates/
│   └── reference.docx    # Word styling template
├── build/
│   ├── client_a.md       # Rendered Markdown
│   ├── client_a.docx     # Rendered Word doc
│   └── client_a.pdf      # Rendered PDF
├── assets/
│   └── images/           # Extracted media
└── filters/
    └── normalize.lua     # Custom Lua filter
```

## CLI Reference

### Commands

- `word2git init` - Initialize workspace
- `word2git ingest <file.docx>` - Ingest Word document
- `word2git extract <file.docx>` - Extract Content Controls only
- `word2git render <template>` - Render document variants
- `word2git validate` - Validate conversions and templates
- `word2git status` - Show workspace status

### Global Options

- `--workspace, -w` - Workspace directory (default: current)
- `--filter, -f` - Path to Lua filter for normalization

## Integration with Git

### .gitignore

```gitignore
# Build outputs (optional - you may want to track these)
build/

# Temporary files
*.tmp
.DS_Store
```

### Git Hooks

Pre-commit hook to validate conversions:

```bash
#!/bin/sh
# .git/hooks/pre-commit
word2git validate --templates
if [ $? -ne 0 ]; then
    echo "Template validation failed"
    exit 1
fi
```

## Examples

See the `examples/` directory for complete working examples:

- `example_usage.py` - Python API examples
- `sample_workflow.sh` - Command-line workflow
- `ci_pipeline.yml` - GitHub Actions integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `pytest`
5. Submit a pull request

## License

GPL v2 License - see [LICENSE](LICENSE) file for details.

## Copyright

Copyright (c) 2024 Keith Lawson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

## Author

Keith Lawson - [Website](https://keithlawson.me) | [LinkedIn](https://www.linkedin.com/in/j-keith-lawson/)