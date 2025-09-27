# Word2Git: Word document ingestion module
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
Word document ingestion module.
Converts .docx files to canonical Markdown using Pandoc with normalization.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import pypandoc
import yaml


class WordIngester:
    """Handles ingestion of Word documents into canonical Markdown format."""

    def __init__(self,
                 pandoc_options: Optional[Dict[str, Union[str, List[str]]]] = None,
                 lua_filter_path: Optional[str] = None):
        """
        Initialize the Word ingester.

        Args:
            pandoc_options: Custom pandoc conversion options
            lua_filter_path: Path to Lua filter for normalization
        """
        self.pandoc_options = pandoc_options or self._default_pandoc_options()
        self.lua_filter_path = lua_filter_path

    def _default_pandoc_options(self) -> Dict[str, Union[str, List[str]]]:
        """Default pandoc options for deterministic conversion."""
        return {
            'to': 'markdown+pipe_tables+table_captions+yaml_metadata_block',
            'wrap': 'none',
            'eol': 'lf',
            'columns': '999',
            'standalone': True,
        }

    def ingest_docx(self,
                   docx_path: Union[str, Path],
                   output_dir: Union[str, Path],
                   extract_media: bool = True) -> Dict[str, str]:
        """
        Ingest a Word document and convert to canonical Markdown.

        Args:
            docx_path: Path to the input .docx file
            output_dir: Directory to store outputs
            extract_media: Whether to extract embedded media

        Returns:
            Dictionary with paths to generated files
        """
        docx_path = Path(docx_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare output paths
        markdown_path = output_dir / f"{docx_path.stem}.md"
        assets_dir = output_dir / "assets"

        # Build pandoc options
        options = self.pandoc_options.copy()

        if extract_media:
            options['extract-media'] = str(assets_dir)

        if self.lua_filter_path and Path(self.lua_filter_path).exists():
            options['lua-filter'] = self.lua_filter_path

        # Convert using pypandoc
        try:
            output = pypandoc.convert_file(
                str(docx_path),
                outputfile=str(markdown_path),
                **options
            )

            result = {
                'markdown': str(markdown_path),
                'assets': str(assets_dir) if assets_dir.exists() else None,
                'success': True
            }

            return result

        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def extract_metadata(self, docx_path: Union[str, Path]) -> Dict:
        """
        Extract document metadata from Word file.

        Args:
            docx_path: Path to the .docx file

        Returns:
            Dictionary containing document metadata
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
                temp_path = temp_file.name

            # Extract just metadata using pandoc
            pypandoc.convert_file(
                str(docx_path),
                to='markdown',
                outputfile=temp_path,
                template=None,
                standalone=True
            )

            # Read and parse YAML front matter
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            os.unlink(temp_path)

            # Extract YAML front matter if present
            if content.startswith('---\n'):
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    yaml_content = content[4:end_marker]
                    return yaml.safe_load(yaml_content) or {}

            return {}

        except Exception:
            return {}

    def normalize_markdown(self, markdown_path: Union[str, Path]) -> bool:
        """
        Apply post-processing normalization to Markdown.

        Args:
            markdown_path: Path to the Markdown file to normalize

        Returns:
            True if normalization succeeded
        """
        try:
            markdown_path = Path(markdown_path)

            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic normalization
            normalized = self._normalize_content(content)

            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(normalized)

            return True

        except Exception:
            return False

    def _normalize_content(self, content: str) -> str:
        """Apply content normalization rules."""
        lines = content.split('\n')
        normalized_lines = []

        for line in lines:
            # Normalize heading spacing
            if line.startswith('#'):
                # Ensure single space after hash marks
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break

                rest = line[level:].lstrip()
                if rest:
                    line = '#' * level + ' ' + rest

            # Normalize table formatting
            elif '|' in line and line.strip().startswith('|'):
                # Clean up table cell spacing
                cells = line.split('|')
                cleaned_cells = [cell.strip() for cell in cells]
                line = '| ' + ' | '.join(cleaned_cells[1:-1]) + ' |'

            normalized_lines.append(line)

        return '\n'.join(normalized_lines)

    def create_reference_template(self,
                                 docx_path: Union[str, Path],
                                 template_dir: Union[str, Path]) -> str:
        """
        Create a reference template from the source Word document.

        Args:
            docx_path: Path to source .docx file
            template_dir: Directory to store the template

        Returns:
            Path to the created template file
        """
        import shutil

        docx_path = Path(docx_path)
        template_dir = Path(template_dir)
        template_dir.mkdir(parents=True, exist_ok=True)

        template_path = template_dir / "reference.docx"
        shutil.copy2(docx_path, template_path)

        return str(template_path)