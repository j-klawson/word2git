#!/usr/bin/env python3
# Word2Git: Example usage of the Word2Git Python module
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
Example usage of the Word2Git Python module.
Demonstrates the complete workflow from Word document to Git-managed variants.
"""

from pathlib import Path
from word2git import Word2GitProcessor, WordIngester, SDTExtractor, VariantRenderer


def basic_workflow_example():
    """Demonstrate basic Word2Git workflow."""
    print("=== Basic Word2Git Workflow ===")

    # Initialize processor
    workspace = Path("./example_workspace")
    processor = Word2GitProcessor(workspace)

    # Setup workspace
    print("Setting up workspace...")
    processor.setup_workspace()

    # For this example, we'll create a mock workflow since we don't have a real .docx
    print("Workspace created at:", workspace)
    print("Directories:")
    status = processor.get_workspace_status()
    for name, info in status['directories'].items():
        print(f"  {name}: {info['path']}")


def content_controls_example():
    """Demonstrate Content Controls extraction."""
    print("\n=== Content Controls Example ===")

    # This would work with a real .docx file containing Content Controls
    extractor = SDTExtractor()

    # Example of what extracted data looks like
    mock_extracted_data = {
        'data': {
            'project.name': {
                'tag': 'project.name',
                'alias': 'Project Name',
                'value': 'My Awesome Project',
                'type': 'text'
            },
            'client.contact': {
                'tag': 'client.contact',
                'alias': 'Client Contact',
                'value': 'john.doe@client.com',
                'type': 'text'
            },
            'report.date': {
                'tag': 'report.date',
                'alias': 'Report Date',
                'value': '2024-01-15',
                'type': 'date'
            }
        },
        'success': True,
        'count': 3
    }

    print("Mock extracted Content Controls:")
    for tag, data in mock_extracted_data['data'].items():
        print(f"  {tag}: {data['value']} ({data['type']})")

    # Generate schema
    schema = extractor.generate_schema(mock_extracted_data)
    print(f"\nGenerated schema has {len(schema.get('properties', {}))} properties")


def template_rendering_example():
    """Demonstrate template rendering with variants."""
    print("\n=== Template Rendering Example ===")

    workspace = Path("./example_workspace")
    docs_dir = workspace / "docs"
    data_dir = workspace / "data"
    build_dir = workspace / "build"

    # Create directories
    docs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Create example template
    template_content = """# Project Report: {{ project_name }}

## Overview
This report covers the {{ project_type }} project for {{ client_name }}.

**Report Date:** {{ report_date }}
**Contact:** {{ contact_email }}

## Summary
{{ project_summary }}

## Budget
Total Budget: ${{ budget | default("TBD") }}
"""

    template_path = docs_dir / "report_template.md.j2"
    with open(template_path, 'w') as f:
        f.write(template_content)

    # Create example data files
    client_a_data = {
        'project_name': 'Website Redesign',
        'project_type': 'web development',
        'client_name': 'Acme Corp',
        'report_date': '2024-01-15',
        'contact_email': 'sarah@acme.com',
        'project_summary': 'Complete redesign of corporate website with modern UI/UX.',
        'budget': '50000'
    }

    client_b_data = {
        'project_name': 'Mobile App Development',
        'project_type': 'mobile development',
        'client_name': 'Beta Industries',
        'report_date': '2024-01-20',
        'contact_email': 'mike@beta.com',
        'project_summary': 'Native iOS and Android app for customer engagement.'
    }

    import yaml

    with open(data_dir / "client_a.yaml", 'w') as f:
        yaml.safe_dump(client_a_data, f)

    with open(data_dir / "client_b.yaml", 'w') as f:
        yaml.safe_dump(client_b_data, f)

    # Render variants
    renderer = VariantRenderer(
        template_dir=docs_dir,
        output_dir=build_dir
    )

    data_files = [data_dir / "client_a.yaml", data_dir / "client_b.yaml"]
    results = renderer.render_variants("report_template.md.j2", data_files)

    print("Rendered variants:")
    for result in results:
        if result['success']:
            print(f"  ✓ {result['variant']}: {result['markdown']}")
        else:
            print(f"  ✗ {result['variant']}: {result['error']}")


def validation_example():
    """Demonstrate validation capabilities."""
    print("\n=== Validation Example ===")

    workspace = Path("./example_workspace")
    validator = RoundTripValidator()

    # Create a test markdown file
    docs_dir = workspace / "docs"
    test_md = docs_dir / "test.md"

    markdown_content = """# Test Document

This is a test document for validation.

## Features

- Lists work correctly
- **Bold text** is preserved
- `Code snippets` are maintained

| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |
"""

    with open(test_md, 'w') as f:
        f.write(markdown_content)

    # Validate markdown syntax
    validation_result = validator._validate_markdown_syntax(markdown_content)
    print(f"Markdown syntax validation:")
    print(f"  Valid: {validation_result['valid']}")
    if validation_result['issues']:
        for issue in validation_result['issues']:
            print(f"  Issue: {issue}")
    else:
        print("  No issues found")


def full_pipeline_example():
    """Demonstrate the complete pipeline."""
    print("\n=== Full Pipeline Example ===")

    workspace = Path("./example_workspace")
    processor = Word2GitProcessor(workspace)

    # Get status
    status = processor.get_workspace_status()
    print(f"Workspace status:")
    print(f"  Templates: {len(status['files']['templates'])}")
    print(f"  Data files: {len(status['files']['data_files'])}")
    print(f"  Canonical MD: {len(status['files']['canonical_md'])}")

    # Create Makefile
    if processor.create_makefile():
        print("✓ Created Makefile for automation")

    print("\nNext steps:")
    print("1. Place your .docx file in the workspace")
    print("2. Run: word2git ingest your_document.docx")
    print("3. Edit data files in data/ directory")
    print("4. Run: word2git render template.md.j2 --all-data")
    print("5. Run: word2git validate --templates")


if __name__ == "__main__":
    """Run all examples."""
    try:
        basic_workflow_example()
        content_controls_example()
        template_rendering_example()
        validation_example()
        full_pipeline_example()

        print("\n" + "="*50)
        print("✓ All examples completed successfully!")
        print("Check the ./example_workspace directory for generated files.")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()