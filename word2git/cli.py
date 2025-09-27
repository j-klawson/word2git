# Word2Git: Command-line interface for Word2Git
# Copyright (C) 2025 Keith Lawson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Command-line interface for Word2Git.
Provides easy access to all Word2Git functionality.
"""

import sys
from pathlib import Path
from typing import List, Optional

import click
import yaml

from .core import Word2GitProcessor
from .ingest import WordIngester
from .extract import SDTExtractor
from .render import VariantRenderer
from .validate import RoundTripValidator


@click.group()
@click.version_option()
@click.option('--workspace', '-w', type=click.Path(), default='.',
              help='Workspace directory (default: current directory)')
@click.option('--filter', '-f', type=click.Path(exists=True),
              help='Path to Lua filter for normalization')
@click.pass_context
def cli(ctx, workspace, filter):
    """Word2Git: Word-first document workflows with Git integration."""
    ctx.ensure_object(dict)
    ctx.obj['workspace'] = Path(workspace)
    ctx.obj['filter'] = filter


@cli.command()
@click.argument('docx_file', type=click.Path(exists=True))
@click.option('--extract-controls', '-c', is_flag=True, default=True,
              help='Extract Content Controls (default: True)')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory (default: docs/)')
@click.pass_context
def ingest(ctx, docx_file, extract_controls, output_dir):
    """Ingest a Word document into the workspace."""
    workspace = ctx.obj['workspace']
    filter_path = ctx.obj.get('filter')

    processor = Word2GitProcessor(workspace, lua_filter_path=filter_path)

    click.echo(f"Ingesting {docx_file}...")
    results = processor.ingest_document(
        docx_path=docx_file,
        extract_content_controls=extract_controls
    )

    if results['ingestion']['success']:
        click.echo("✓ Document ingested successfully")
        click.echo(f"  Markdown: {results['ingestion']['markdown']}")

        if 'content_controls' in results and results['content_controls']['success']:
            click.echo(f"  Content Controls: {results['content_controls']['count']} found")
            if 'data_file' in results:
                click.echo(f"  Data file: {results['data_file']}")
            if 'template_file' in results:
                click.echo(f"  Template: {results['template_file']}")
    else:
        click.echo(f"✗ Ingestion failed: {results['ingestion']['error']}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('template_name')
@click.option('--data', '-d', type=click.Path(exists=True), multiple=True,
              help='Data files to render (can specify multiple)')
@click.option('--format', '-f', multiple=True, default=['md', 'docx'],
              help='Output formats (default: md, docx)')
@click.option('--all-data', '-a', is_flag=True,
              help='Render all data files in data/')
@click.pass_context
def render(ctx, template_name, data, format, all_data):
    """Render document variants from template."""
    workspace = ctx.obj['workspace']
    filter_path = ctx.obj.get('filter')

    processor = Word2GitProcessor(workspace, lua_filter_path=filter_path)

    if all_data:
        data_files = None
    elif data:
        data_files = list(data)
    else:
        click.echo("Error: Specify --data files or use --all-data", err=True)
        sys.exit(1)

    click.echo(f"Rendering variants of {template_name}...")
    results = processor.render_variants(
        template_name=template_name,
        data_files=data_files,
        formats=list(format)
    )

    for result in results:
        if result['success']:
            click.echo(f"✓ {result['variant']}")
            for fmt, path in result.get('formats', {}).items():
                if not path.startswith('Error:'):
                    click.echo(f"  {fmt}: {path}")
                else:
                    click.echo(f"  {fmt}: {path}", err=True)
        else:
            click.echo(f"✗ {result['variant']}: {result['error']}", err=True)


@cli.command()
@click.argument('docx_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(),
              help='Output YAML file (default: data/{filename}.yaml)')
@click.option('--values-only', is_flag=True, default=True,
              help='Extract only values (default: True)')
@click.pass_context
def extract(ctx, docx_file, output, values_only):
    """Extract Content Controls from Word document."""
    docx_path = Path(docx_file)

    if not output:
        workspace = ctx.obj['workspace']
        data_dir = workspace / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        output = data_dir / f"{docx_path.stem}.yaml"

    extractor = SDTExtractor()

    click.echo(f"Extracting Content Controls from {docx_file}...")
    results = extractor.extract_from_docx(docx_file)

    if results['success']:
        click.echo(f"✓ Found {results['count']} Content Controls")

        if extractor.save_to_yaml(results, output, values_only=values_only):
            click.echo(f"✓ Saved to {output}")
        else:
            click.echo("✗ Failed to save YAML file", err=True)
            sys.exit(1)
    else:
        click.echo(f"✗ Extraction failed: {results['error']}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--markdown', '-m', type=click.Path(exists=True),
              help='Markdown file to validate')
@click.option('--docx', '-d', type=click.Path(exists=True),
              help='Word document to validate against')
@click.option('--templates', '-t', is_flag=True,
              help='Validate all templates in workspace')
@click.option('--roundtrip', '-r', is_flag=True,
              help='Test round-trip conversion')
@click.pass_context
def validate(ctx, markdown, docx, templates, roundtrip):
    """Validate document conversions and templates."""
    workspace = ctx.obj['workspace']
    filter_path = ctx.obj.get('filter')

    processor = Word2GitProcessor(workspace, lua_filter_path=filter_path)

    if templates:
        click.echo("Validating templates...")
        results = processor.validate_templates()

        for result in results:
            if result['success']:
                data_file = Path(result['data_file']).name
                click.echo(f"✓ {data_file}: rendered {result['rendered_length']} chars")
                if not result['syntax_valid']:
                    for issue in result['syntax_issues']:
                        click.echo(f"  ⚠ {issue}", err=True)
            else:
                click.echo(f"✗ {result['data_file']}: {result['error']}", err=True)

    if roundtrip and markdown:
        click.echo(f"Testing round-trip conversion for {markdown}...")
        results = processor.validate_roundtrip(markdown, docx)

        if 'markdown_roundtrip' in results:
            rt_result = results['markdown_roundtrip']
            if rt_result['success']:
                if rt_result['identical']:
                    click.echo("✓ Round-trip conversion preserves content")
                else:
                    click.echo("⚠ Round-trip conversion has differences")
                    if rt_result['diff']:
                        click.echo("Differences found:")
                        for line in rt_result['diff'][:10]:  # Show first 10 lines
                            click.echo(f"  {line.rstrip()}")
            else:
                click.echo(f"✗ Round-trip failed: {rt_result['error']}", err=True)


@cli.command()
@click.pass_context
def status(ctx):
    """Show workspace status."""
    workspace = ctx.obj['workspace']
    filter_path = ctx.obj.get('filter')

    processor = Word2GitProcessor(workspace, lua_filter_path=filter_path)
    status_info = processor.get_workspace_status()

    click.echo(f"Workspace: {status_info['workspace_dir']}")
    click.echo()

    click.echo("Directories:")
    for name, info in status_info['directories'].items():
        status_icon = "✓" if info['exists'] else "✗"
        click.echo(f"  {status_icon} {name}: {info['file_count']} files")

    click.echo()
    click.echo("Files:")
    for name, files in status_info['files'].items():
        if files:
            click.echo(f"  {name}: {len(files)}")
            for file in files[:3]:  # Show first 3 files
                click.echo(f"    {Path(file).name}")
            if len(files) > 3:
                click.echo(f"    ... and {len(files) - 3} more")
        else:
            click.echo(f"  {name}: none")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize a new Word2Git workspace."""
    workspace = ctx.obj['workspace']

    processor = Word2GitProcessor(workspace)

    if processor.setup_workspace():
        click.echo(f"✓ Initialized Word2Git workspace in {workspace}")

        # Create example files
        readme_content = """# Word2Git Workspace

This workspace contains:

- `docs/` - Canonical Markdown files and templates
- `data/` - YAML data files for variants
- `templates/` - Reference Word documents
- `build/` - Generated outputs
- `assets/` - Images and other media

## Usage

1. Ingest a Word document:
   ```
   word2git ingest document.docx
   ```

2. Render variants:
   ```
   word2git render canonical.md.j2 --all-data
   ```

3. Validate round-trip conversion:
   ```
   word2git validate --roundtrip -m docs/canonical.md
   ```
"""

        readme_path = workspace / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # Create Makefile
        if processor.create_makefile():
            click.echo("✓ Created Makefile")

        click.echo("✓ Created README.md")
    else:
        click.echo("✗ Failed to initialize workspace", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()