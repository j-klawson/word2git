# Word2Git: Content Controls (SDT) extraction module
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
Content Controls (SDT) extraction module.
Extracts Structured Document Tags from Word documents for data-driven templates.
"""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import yaml
from lxml import etree


class SDTExtractor:
    """Extracts and processes Structured Document Tags (Content Controls) from Word documents."""

    def __init__(self):
        """Initialize the SDT extractor."""
        self.namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }

    def extract_from_docx(self, docx_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract all Content Controls from a Word document.

        Args:
            docx_path: Path to the .docx file

        Returns:
            Dictionary containing extracted Content Controls
        """
        docx_path = Path(docx_path)
        extracted_data = {}

        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # Extract main document XML
                document_xml = docx_zip.read('word/document.xml')
                root = etree.fromstring(document_xml)

                # Find all SDT elements
                sdt_elements = root.findall('.//w:sdt', self.namespaces)

                for sdt in sdt_elements:
                    sdt_data = self._extract_sdt_data(sdt)
                    if sdt_data['tag']:
                        extracted_data[sdt_data['tag']] = sdt_data

                # Also check headers and footers
                extracted_data.update(self._extract_from_headers_footers(docx_zip))

        except Exception as e:
            return {'error': str(e), 'success': False}

        return {
            'data': extracted_data,
            'success': True,
            'count': len(extracted_data)
        }

    def _extract_sdt_data(self, sdt_element) -> Dict[str, Any]:
        """
        Extract data from a single SDT element.

        Args:
            sdt_element: The SDT XML element

        Returns:
            Dictionary with SDT data
        """
        sdt_data = {
            'tag': None,
            'alias': None,
            'value': '',
            'type': 'text',
            'placeholder': None
        }

        # Get SDT properties
        sdt_pr = sdt_element.find('.//w:sdtPr', self.namespaces)
        if sdt_pr is not None:
            # Extract tag
            tag_elem = sdt_pr.find('.//w:tag', self.namespaces)
            if tag_elem is not None:
                sdt_data['tag'] = tag_elem.get(f'{{{self.namespaces["w"]}}}val')

            # Extract alias (display name)
            alias_elem = sdt_pr.find('.//w:alias', self.namespaces)
            if alias_elem is not None:
                sdt_data['alias'] = alias_elem.get(f'{{{self.namespaces["w"]}}}val')

            # Extract placeholder text
            placeholder_elem = sdt_pr.find('.//w:placeholder//w:docPart', self.namespaces)
            if placeholder_elem is not None:
                sdt_data['placeholder'] = placeholder_elem.get(f'{{{self.namespaces["w"]}}}val')

            # Determine control type
            if sdt_pr.find('.//w:dropDownList', self.namespaces) is not None:
                sdt_data['type'] = 'dropdown'
                sdt_data['options'] = self._extract_dropdown_options(sdt_pr)
            elif sdt_pr.find('.//w:date', self.namespaces) is not None:
                sdt_data['type'] = 'date'
            elif sdt_pr.find('.//w:richText', self.namespaces) is not None:
                sdt_data['type'] = 'richtext'

        # Extract current value
        sdt_content = sdt_element.find('.//w:sdtContent', self.namespaces)
        if sdt_content is not None:
            text_elements = sdt_content.findall('.//w:t', self.namespaces)
            sdt_data['value'] = ''.join(elem.text or '' for elem in text_elements)

        return sdt_data

    def _extract_dropdown_options(self, sdt_pr) -> List[Dict[str, str]]:
        """Extract options from dropdown Content Control."""
        options = []
        dropdown = sdt_pr.find('.//w:dropDownList', self.namespaces)
        if dropdown is not None:
            for item in dropdown.findall('.//w:listItem', self.namespaces):
                display_text = item.get(f'{{{self.namespaces["w"]}}}displayText', '')
                value = item.get(f'{{{self.namespaces["w"]}}}value', display_text)
                options.append({'display': display_text, 'value': value})
        return options

    def _extract_from_headers_footers(self, docx_zip) -> Dict[str, Any]:
        """Extract SDTs from headers and footers."""
        extracted = {}

        # Check for header/footer files
        for file_name in docx_zip.namelist():
            if file_name.startswith('word/header') or file_name.startswith('word/footer'):
                try:
                    xml_content = docx_zip.read(file_name)
                    root = etree.fromstring(xml_content)
                    sdt_elements = root.findall('.//w:sdt', self.namespaces)

                    for sdt in sdt_elements:
                        sdt_data = self._extract_sdt_data(sdt)
                        if sdt_data['tag']:
                            extracted[sdt_data['tag']] = sdt_data

                except Exception:
                    continue

        return extracted

    def save_to_yaml(self,
                    extracted_data: Dict[str, Any],
                    output_path: Union[str, Path],
                    values_only: bool = True) -> bool:
        """
        Save extracted data to YAML file.

        Args:
            extracted_data: Data from extract_from_docx
            output_path: Path for the output YAML file
            values_only: If True, save only values; if False, save full metadata

        Returns:
            True if successful
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if values_only and 'data' in extracted_data:
                # Save only the values for template rendering
                yaml_data = {
                    tag: data['value']
                    for tag, data in extracted_data['data'].items()
                }
            else:
                # Save full metadata
                yaml_data = extracted_data

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(yaml_data, f, default_flow_style=False, sort_keys=True)

            return True

        except Exception:
            return False

    def create_template_mapping(self,
                               extracted_data: Dict[str, Any],
                               markdown_content: str) -> str:
        """
        Replace Content Control values in Markdown with Jinja2 template variables.

        Args:
            extracted_data: Data from extract_from_docx
            markdown_content: Source Markdown content

        Returns:
            Markdown content with Jinja2 template variables
        """
        if 'data' not in extracted_data:
            return markdown_content

        template_content = markdown_content

        for tag, data in extracted_data['data'].items():
            value = data['value']
            if value and value.strip():
                # Replace the actual value with a Jinja2 variable
                variable_name = tag.replace('.', '_').replace('-', '_')
                template_content = template_content.replace(
                    value,
                    f"{{{{ {variable_name} }}}}"
                )

        return template_content

    def validate_template(self,
                         template_content: str,
                         data_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate that a Jinja2 template can be rendered with provided data.

        Args:
            template_content: Jinja2 template content
            data_file: Path to YAML data file

        Returns:
            Validation results
        """
        try:
            import jinja2

            # Load data
            with open(data_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            # Try to render template
            template = jinja2.Template(template_content)
            rendered = template.render(**data)

            # Find missing variables
            env = jinja2.Environment()
            ast = env.parse(template_content)
            template_vars = set(jinja2.meta.find_undeclared_variables(ast))
            data_vars = set(data.keys())
            missing_vars = template_vars - data_vars

            return {
                'success': True,
                'missing_variables': list(missing_vars),
                'template_variables': list(template_vars),
                'data_variables': list(data_vars),
                'rendered_length': len(rendered)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_schema(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a JSON schema for the extracted Content Controls.

        Args:
            extracted_data: Data from extract_from_docx

        Returns:
            JSON schema dictionary
        """
        if 'data' not in extracted_data:
            return {}

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {},
            "required": []
        }

        for tag, data in extracted_data['data'].items():
            prop = {"type": "string"}

            if data['type'] == 'date':
                prop["format"] = "date"
            elif data['type'] == 'dropdown' and 'options' in data:
                prop["enum"] = [opt['value'] for opt in data['options']]

            if data['alias']:
                prop["title"] = data['alias']

            if data['placeholder']:
                prop["description"] = data['placeholder']

            # Use tag as property name (replace dots with underscores for JSON compatibility)
            property_name = tag.replace('.', '_').replace('-', '_')
            schema["properties"][property_name] = prop

            # Mark as required if it has a value
            if data['value'] and data['value'].strip():
                schema["required"].append(property_name)

        return schema