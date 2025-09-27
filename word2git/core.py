# Word2Git: Core module that orchestrates the Word2Git workflow
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
Core module that orchestrates the Word2Git workflow.
Provides a high-level interface for the complete pipeline.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .ingest import WordIngester
from .extract import SDTExtractor
from .render import VariantRenderer
from .validate import RoundTripValidator


class Word2GitProcessor:
    """Main processor that orchestrates the complete Word2Git workflow."""

    def __init__(self,
                 workspace_dir: Union[str, Path],
                 lua_filter_path: Optional[str] = None):
        """
        Initialize the Word2Git processor.

        Args:
            workspace_dir: Root directory for the Word2Git workspace
            lua_filter_path: Optional path to Lua filter for normalization
        """
        self.workspace_dir = Path(workspace_dir)
        self.lua_filter_path = lua_filter_path

        # Create workspace structure
        self.docs_dir = self.workspace_dir / "docs"
        self.data_dir = self.workspace_dir / "data"
        self.templates_dir = self.workspace_dir / "templates"
        self.build_dir = self.workspace_dir / "build"
        self.assets_dir = self.workspace_dir / "assets"

        # Initialize components
        self.ingester = WordIngester(lua_filter_path=lua_filter_path)
        self.extractor = SDTExtractor()
        self.renderer = VariantRenderer(
            template_dir=self.docs_dir,
            output_dir=self.build_dir
        )
        self.validator = RoundTripValidator(lua_filter_path=lua_filter_path)

    def setup_workspace(self) -> bool:
        """
        Set up the workspace directory structure.

        Returns:
            True if workspace was created successfully
        """
        try:
            directories = [
                self.docs_dir,
                self.data_dir,
                self.templates_dir,
                self.build_dir,
                self.assets_dir
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)

            return True

        except Exception:
            return False

    def ingest_document(self,
                       docx_path: Union[str, Path],
                       extract_content_controls: bool = True) -> Dict[str, Any]:
        """
        Ingest a Word document into the workspace.

        Args:
            docx_path: Path to the Word document
            extract_content_controls: Whether to extract Content Controls

        Returns:
            Ingestion results
        """
        docx_path = Path(docx_path)
        results = {}

        # Ensure workspace exists
        self.setup_workspace()

        # Ingest to canonical Markdown
        ingest_result = self.ingester.ingest_docx(
            docx_path=docx_path,
            output_dir=self.docs_dir,
            extract_media=True
        )
        results['ingestion'] = ingest_result

        if not ingest_result['success']:
            return results

        # Create reference template
        template_path = self.ingester.create_reference_template(
            docx_path=docx_path,
            template_dir=self.templates_dir
        )
        results['reference_template'] = template_path

        # Extract Content Controls if requested
        if extract_content_controls:
            sdt_result = self.extractor.extract_from_docx(docx_path)
            results['content_controls'] = sdt_result

            if sdt_result['success'] and sdt_result['data']:
                # Save extracted data to YAML
                data_file = self.data_dir / f"{docx_path.stem}.yaml"
                self.extractor.save_to_yaml(sdt_result, data_file, values_only=True)
                results['data_file'] = str(data_file)

                # Convert Markdown to template
                markdown_file = Path(ingest_result['markdown'])
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                template_content = self.extractor.create_template_mapping(
                    sdt_result, markdown_content
                )

                template_file = self.docs_dir / f"{docx_path.stem}.md.j2"
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(template_content)

                results['template_file'] = str(template_file)

        return results

    def render_variants(self,
                       template_name: str,
                       data_files: Optional[List[Union[str, Path]]] = None,
                       formats: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Render document variants from template and data files.

        Args:
            template_name: Name of the template file
            data_files: List of data files (defaults to all in data_dir)
            formats: Output formats (defaults to ['md', 'docx'])

        Returns:
            List of rendering results
        """
        if data_files is None:
            data_files = list(self.data_dir.glob("*.yaml"))

        if formats is None:
            formats = ['md', 'docx']

        # Set reference document for Word output
        reference_docx = self.templates_dir / "reference.docx"
        if reference_docx.exists():
            self.renderer.reference_docx = reference_docx

        # Copy assets to build directory
        if self.assets_dir.exists():
            self.renderer.copy_assets(self.assets_dir)

        return self.renderer.render_all_formats(
            template_name=template_name,
            data_files=data_files,
            formats=formats
        )

    def validate_roundtrip(self,
                          markdown_file: Union[str, Path],
                          docx_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Validate round-trip conversion between formats.

        Args:
            markdown_file: Path to Markdown file
            docx_file: Optional Word file for comparison

        Returns:
            Validation results
        """
        results = {}

        # Test Markdown -> Word -> Markdown
        reference_docx = self.templates_dir / "reference.docx"
        md_validation = self.validator.validate_markdown_to_docx(
            markdown_path=markdown_file,
            reference_docx_path=reference_docx if reference_docx.exists() else None
        )
        results['markdown_roundtrip'] = md_validation

        # Test Word -> Markdown if Word file provided
        if docx_file:
            docx_validation = self.validator.validate_docx_to_markdown(
                docx_path=docx_file,
                reference_md_path=markdown_file
            )
            results['docx_conversion'] = docx_validation

        return results

    def validate_templates(self) -> List[Dict[str, Any]]:
        """
        Validate all templates in the workspace.

        Returns:
            List of validation results
        """
        results = []

        template_files = list(self.docs_dir.glob("*.j2"))
        data_files = list(self.data_dir.glob("*.yaml"))

        for template_file in template_files:
            template_results = self.validator.validate_template_rendering(
                template_path=template_file,
                data_files=data_files
            )
            results.extend(template_results)

        return results

    def get_workspace_status(self) -> Dict[str, Any]:
        """
        Get the current status of the workspace.

        Returns:
            Workspace status information
        """
        status = {
            'workspace_dir': str(self.workspace_dir),
            'directories': {},
            'files': {}
        }

        # Check directories
        directories = {
            'docs': self.docs_dir,
            'data': self.data_dir,
            'templates': self.templates_dir,
            'build': self.build_dir,
            'assets': self.assets_dir
        }

        for name, path in directories.items():
            status['directories'][name] = {
                'path': str(path),
                'exists': path.exists(),
                'file_count': len(list(path.glob("*"))) if path.exists() else 0
            }

        # Check key files
        files = {
            'canonical_md': list(self.docs_dir.glob("*.md")),
            'templates': list(self.docs_dir.glob("*.j2")),
            'data_files': list(self.data_dir.glob("*.yaml")),
            'reference_docx': list(self.templates_dir.glob("*.docx")),
            'rendered_outputs': list(self.build_dir.glob("*"))
        }

        for name, file_list in files.items():
            status['files'][name] = [str(f) for f in file_list]

        return status

    def create_makefile(self) -> bool:
        """
        Create a Makefile for common operations.

        Returns:
            True if Makefile was created successfully
        """
        makefile_content = f"""# Word2Git Makefile
# Generated by Word2Git processor

WORKSPACE_DIR = {self.workspace_dir}
DOCS_DIR = {self.docs_dir}
DATA_DIR = {self.data_dir}
BUILD_DIR = {self.build_dir}
TEMPLATES_DIR = {self.templates_dir}

.PHONY: all clean build validate help

all: build

build:
\t@echo "Building all variants..."
\t@word2git render --all

validate:
\t@echo "Validating round-trip conversion..."
\t@word2git validate --roundtrip

clean:
\t@echo "Cleaning build directory..."
\t@rm -rf $(BUILD_DIR)/*

help:
\t@echo "Available targets:"
\t@echo "  build     - Render all document variants"
\t@echo "  validate  - Validate round-trip conversion"
\t@echo "  clean     - Clean build directory"
\t@echo "  help      - Show this help message"
"""

        try:
            makefile_path = self.workspace_dir / "Makefile"
            with open(makefile_path, 'w', encoding='utf-8') as f:
                f.write(makefile_content)
            return True
        except Exception:
            return False