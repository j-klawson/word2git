# Word2Git: Multi-variant rendering module
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
Multi-variant rendering module.
Renders canonical Markdown templates with different data sets to produce multiple outputs.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import jinja2
import pypandoc
import yaml


class VariantRenderer:
    """Handles rendering of Markdown templates into multiple variants and formats."""

    def __init__(self,
                 template_dir: Union[str, Path],
                 output_dir: Union[str, Path],
                 reference_docx: Optional[Union[str, Path]] = None):
        """
        Initialize the variant renderer.

        Args:
            template_dir: Directory containing Jinja2 templates
            output_dir: Directory for rendered outputs
            reference_docx: Path to reference Word template for styling
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.reference_docx = Path(reference_docx) if reference_docx else None

        # Setup Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['slugify'] = self._slugify
        self.env.filters['markdown'] = self._markdown_filter

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = str(text).lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    def _markdown_filter(self, text: str) -> str:
        """Process markdown in template variables."""
        return text.replace('\n', '\n\n')

    def load_data(self, data_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load data from YAML file.

        Args:
            data_path: Path to YAML data file

        Returns:
            Loaded data dictionary
        """
        data_path = Path(data_path)
        with open(data_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def render_template(self,
                       template_name: str,
                       data: Dict[str, Any],
                       output_name: str) -> str:
        """
        Render a Jinja2 template with provided data.

        Args:
            template_name: Name of the template file
            data: Data dictionary for template rendering
            output_name: Name for the output file

        Returns:
            Path to the rendered Markdown file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        template = self.env.get_template(template_name)
        rendered_content = template.render(**data)

        output_path = self.output_dir / f"{output_name}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_content)

        return str(output_path)

    def render_variants(self,
                       template_name: str,
                       data_files: List[Union[str, Path]]) -> List[Dict[str, str]]:
        """
        Render multiple variants from different data files.

        Args:
            template_name: Name of the template file
            data_files: List of YAML data files

        Returns:
            List of rendering results
        """
        results = []

        for data_file in data_files:
            data_path = Path(data_file)
            variant_name = data_path.stem

            try:
                data = self.load_data(data_path)
                markdown_path = self.render_template(template_name, data, variant_name)

                results.append({
                    'variant': variant_name,
                    'data_file': str(data_path),
                    'markdown': markdown_path,
                    'success': True
                })

            except Exception as e:
                results.append({
                    'variant': variant_name,
                    'data_file': str(data_path),
                    'error': str(e),
                    'success': False
                })

        return results

    def convert_to_docx(self,
                       markdown_path: Union[str, Path],
                       output_name: Optional[str] = None) -> str:
        """
        Convert rendered Markdown to Word document.

        Args:
            markdown_path: Path to the Markdown file
            output_name: Optional output name (defaults to markdown filename)

        Returns:
            Path to the generated .docx file
        """
        markdown_path = Path(markdown_path)
        if not output_name:
            output_name = markdown_path.stem

        docx_path = self.output_dir / f"{output_name}.docx"

        # Pandoc options for Word conversion
        pandoc_options = {
            'to': 'docx',
            'standalone': True
        }

        if self.reference_docx and self.reference_docx.exists():
            pandoc_options['reference-doc'] = str(self.reference_docx)

        pypandoc.convert_file(
            str(markdown_path),
            outputfile=str(docx_path),
            **pandoc_options
        )

        return str(docx_path)

    def render_all_formats(self,
                          template_name: str,
                          data_files: List[Union[str, Path]],
                          formats: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Render variants in multiple output formats.

        Args:
            template_name: Name of the template file
            data_files: List of YAML data files
            formats: List of output formats (defaults to ['md', 'docx'])

        Returns:
            List of rendering results with all formats
        """
        if formats is None:
            formats = ['md', 'docx']

        results = []
        markdown_results = self.render_variants(template_name, data_files)

        for md_result in markdown_results:
            if not md_result['success']:
                results.append(md_result)
                continue

            variant_result = md_result.copy()
            variant_result['formats'] = {}

            # Always include Markdown
            if 'md' in formats:
                variant_result['formats']['md'] = md_result['markdown']

            # Convert to other formats
            if 'docx' in formats:
                try:
                    docx_path = self.convert_to_docx(md_result['markdown'])
                    variant_result['formats']['docx'] = docx_path
                except Exception as e:
                    variant_result['formats']['docx'] = f"Error: {str(e)}"

            if 'pdf' in formats:
                try:
                    pdf_path = self.convert_to_pdf(md_result['markdown'])
                    variant_result['formats']['pdf'] = pdf_path
                except Exception as e:
                    variant_result['formats']['pdf'] = f"Error: {str(e)}"

            results.append(variant_result)

        return results

    def convert_to_pdf(self, markdown_path: Union[str, Path]) -> str:
        """
        Convert Markdown to PDF (requires LaTeX).

        Args:
            markdown_path: Path to the Markdown file

        Returns:
            Path to the generated PDF file
        """
        markdown_path = Path(markdown_path)
        pdf_path = self.output_dir / f"{markdown_path.stem}.pdf"

        pypandoc.convert_file(
            str(markdown_path),
            to='pdf',
            outputfile=str(pdf_path),
            extra_args=['--pdf-engine=xelatex']
        )

        return str(pdf_path)

    def copy_assets(self, assets_dir: Union[str, Path]) -> None:
        """
        Copy assets to output directory.

        Args:
            assets_dir: Source assets directory
        """
        assets_dir = Path(assets_dir)
        if not assets_dir.exists():
            return

        output_assets = self.output_dir / "assets"
        if output_assets.exists():
            shutil.rmtree(output_assets)

        shutil.copytree(assets_dir, output_assets)

    def create_template_from_markdown(self,
                                    markdown_path: Union[str, Path],
                                    template_name: str,
                                    variables: List[str]) -> str:
        """
        Convert a Markdown file to a Jinja2 template by replacing specified text with variables.

        Args:
            markdown_path: Path to source Markdown file
            template_name: Name for the template file
            variables: List of text patterns to replace with Jinja2 variables

        Returns:
            Path to the created template file
        """
        markdown_path = Path(markdown_path)
        template_path = self.template_dir / template_name

        self.template_dir.mkdir(parents=True, exist_ok=True)

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace specified text with Jinja2 variables
        for var in variables:
            if isinstance(var, dict):
                for text, var_name in var.items():
                    content = content.replace(text, f"{{{{ {var_name} }}}}")
            else:
                # Simple variable replacement
                var_name = self._slugify(var).replace('-', '_')
                content = content.replace(var, f"{{{{ {var_name} }}}}")

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(template_path)