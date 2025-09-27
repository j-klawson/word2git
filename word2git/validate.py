# Word2Git: Round-trip validation module
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
Round-trip validation module.
Validates that Word documents can be converted to Markdown and back without losing fidelity.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

import pypandoc
import yaml
from difflib import unified_diff


class RoundTripValidator:
    """Validates round-trip conversion between Word and Markdown formats."""

    def __init__(self,
                 pandoc_options: Optional[Dict] = None,
                 lua_filter_path: Optional[str] = None):
        """
        Initialize the round-trip validator.

        Args:
            pandoc_options: Custom pandoc options for validation
            lua_filter_path: Path to Lua filter for normalization
        """
        self.pandoc_options = pandoc_options or self._default_pandoc_options()
        self.lua_filter_path = lua_filter_path

    def _default_pandoc_options(self) -> Dict:
        """Default pandoc options for validation."""
        return {
            'to': 'markdown+pipe_tables+table_captions+yaml_metadata_block',
            'wrap': 'none',
            'eol': 'lf',
            'columns': '999',
            'standalone': True
        }

    def validate_docx_to_markdown(self,
                                 docx_path: Union[str, Path],
                                 reference_md_path: Union[str, Path]) -> Dict[str, any]:
        """
        Validate that a Word document converts to the expected Markdown.

        Args:
            docx_path: Path to the Word document
            reference_md_path: Path to the reference Markdown file

        Returns:
            Validation results dictionary
        """
        docx_path = Path(docx_path)
        reference_md_path = Path(reference_md_path)

        try:
            # Convert docx to markdown
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_file:
                temp_md_path = temp_file.name

            options = self.pandoc_options.copy()
            if self.lua_filter_path and Path(self.lua_filter_path).exists():
                options['lua-filter'] = self.lua_filter_path

            pypandoc.convert_file(
                str(docx_path),
                outputfile=temp_md_path,
                **options
            )

            # Compare with reference
            with open(reference_md_path, 'r', encoding='utf-8') as f:
                reference_content = f.read()

            with open(temp_md_path, 'r', encoding='utf-8') as f:
                converted_content = f.read()

            # Clean up temporary file
            os.unlink(temp_md_path)

            # Normalize for comparison
            reference_normalized = self._normalize_markdown(reference_content)
            converted_normalized = self._normalize_markdown(converted_content)

            is_identical = reference_normalized == converted_normalized

            result = {
                'success': True,
                'identical': is_identical,
                'reference_length': len(reference_content),
                'converted_length': len(converted_content),
                'diff': None
            }

            if not is_identical:
                result['diff'] = self._generate_diff(
                    reference_normalized,
                    converted_normalized,
                    str(reference_md_path),
                    f"{docx_path.stem}_converted.md"
                )

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def validate_markdown_to_docx(self,
                                 markdown_path: Union[str, Path],
                                 reference_docx_path: Optional[Union[str, Path]] = None) -> Dict[str, any]:
        """
        Validate that Markdown converts to Word and back without loss.

        Args:
            markdown_path: Path to the Markdown file
            reference_docx_path: Optional reference Word template

        Returns:
            Validation results dictionary
        """
        markdown_path = Path(markdown_path)

        try:
            # Convert markdown to docx
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                temp_docx_path = temp_docx.name

            docx_options = {'to': 'docx', 'standalone': True}
            if reference_docx_path and Path(reference_docx_path).exists():
                docx_options['reference-doc'] = str(reference_docx_path)

            pypandoc.convert_file(
                str(markdown_path),
                outputfile=temp_docx_path,
                **docx_options
            )

            # Convert back to markdown
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_md:
                temp_md_path = temp_md.name

            options = self.pandoc_options.copy()
            if self.lua_filter_path and Path(self.lua_filter_path).exists():
                options['lua-filter'] = self.lua_filter_path

            pypandoc.convert_file(
                temp_docx_path,
                outputfile=temp_md_path,
                **options
            )

            # Compare original and round-trip markdown
            with open(markdown_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            with open(temp_md_path, 'r', encoding='utf-8') as f:
                roundtrip_content = f.read()

            # Clean up temporary files
            os.unlink(temp_docx_path)
            os.unlink(temp_md_path)

            # Normalize for comparison
            original_normalized = self._normalize_markdown(original_content)
            roundtrip_normalized = self._normalize_markdown(roundtrip_content)

            is_identical = original_normalized == roundtrip_normalized

            result = {
                'success': True,
                'identical': is_identical,
                'original_length': len(original_content),
                'roundtrip_length': len(roundtrip_content),
                'diff': None
            }

            if not is_identical:
                result['diff'] = self._generate_diff(
                    original_normalized,
                    roundtrip_normalized,
                    str(markdown_path),
                    f"{markdown_path.stem}_roundtrip.md"
                )

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def validate_template_rendering(self,
                                  template_path: Union[str, Path],
                                  data_files: List[Union[str, Path]]) -> List[Dict[str, any]]:
        """
        Validate that template rendering works correctly with provided data files.

        Args:
            template_path: Path to the Jinja2 template
            data_files: List of YAML data files to test

        Returns:
            List of validation results for each data file
        """
        import jinja2

        template_path = Path(template_path)
        results = []

        try:
            # Load template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            template = jinja2.Template(template_content)

            for data_file in data_files:
                data_path = Path(data_file)

                try:
                    # Load data
                    with open(data_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f) or {}

                    # Render template
                    rendered = template.render(**data)

                    # Validate the rendered markdown
                    validation_result = self._validate_markdown_syntax(rendered)

                    results.append({
                        'data_file': str(data_path),
                        'success': True,
                        'rendered_length': len(rendered),
                        'syntax_valid': validation_result['valid'],
                        'syntax_issues': validation_result.get('issues', [])
                    })

                except Exception as e:
                    results.append({
                        'data_file': str(data_path),
                        'success': False,
                        'error': str(e)
                    })

        except Exception as e:
            return [{
                'template_file': str(template_path),
                'success': False,
                'error': str(e)
            }]

        return results

    def _normalize_markdown(self, content: str) -> str:
        """Normalize Markdown content for comparison."""
        lines = content.split('\n')
        normalized_lines = []

        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()

            # Normalize heading spacing
            if line.startswith('#'):
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break
                rest = line[level:].lstrip()
                if rest:
                    line = '#' * level + ' ' + rest

            # Normalize list item spacing
            elif line.lstrip().startswith(('- ', '* ', '+ ')):
                indent = len(line) - len(line.lstrip())
                marker = line.lstrip()[0]
                content = line.lstrip()[2:]
                line = ' ' * indent + marker + ' ' + content

            # Normalize table formatting
            elif '|' in line and line.strip().startswith('|'):
                cells = line.split('|')
                cleaned_cells = [cell.strip() for cell in cells]
                line = '| ' + ' | '.join(cleaned_cells[1:-1]) + ' |'

            normalized_lines.append(line)

        # Remove multiple consecutive empty lines
        result_lines = []
        prev_empty = False
        for line in normalized_lines:
            if line == '':
                if not prev_empty:
                    result_lines.append(line)
                prev_empty = True
            else:
                result_lines.append(line)
                prev_empty = False

        return '\n'.join(result_lines)

    def _generate_diff(self,
                      content1: str,
                      content2: str,
                      filename1: str,
                      filename2: str) -> List[str]:
        """Generate unified diff between two text contents."""
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)

        return list(unified_diff(
            lines1,
            lines2,
            fromfile=filename1,
            tofile=filename2,
            lineterm=''
        ))

    def _validate_markdown_syntax(self, markdown_content: str) -> Dict[str, any]:
        """Basic validation of Markdown syntax."""
        issues = []
        lines = markdown_content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for unclosed code blocks
            if line.strip().startswith('```'):
                # This is a basic check - more sophisticated parsing would be needed
                # for complete validation
                pass

            # Check for malformed links
            import re
            link_pattern = r'\[([^\]]*)\]\(([^)]*)\)'
            links = re.findall(link_pattern, line)
            for text, url in links:
                if not url.strip():
                    issues.append(f"Line {i}: Empty link URL for text '{text}'")

            # Check for malformed images
            img_pattern = r'!\[([^\]]*)\]\(([^)]*)\)'
            images = re.findall(img_pattern, line)
            for alt_text, url in images:
                if not url.strip():
                    issues.append(f"Line {i}: Empty image URL for alt text '{alt_text}'")

        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

    def generate_validation_report(self,
                                  results: List[Dict[str, any]],
                                  output_path: Union[str, Path]) -> bool:
        """
        Generate a validation report from results.

        Args:
            results: List of validation results
            output_path: Path for the output report

        Returns:
            True if report was generated successfully
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            report = {
                'validation_report': {
                    'timestamp': str(Path().cwd()),  # Could use datetime
                    'total_tests': len(results),
                    'passed': sum(1 for r in results if r.get('success', False)),
                    'failed': sum(1 for r in results if not r.get('success', False)),
                    'results': results
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(report, f, default_flow_style=False)

            return True

        except Exception:
            return False