# Word2Git: A Python module for Word-first document workflows with Git integration
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
Word2Git: A Python module for Word-first document workflows with Git integration.

Provides a two-track pipeline for maintaining Word documents as Git source of truth
while enabling round-trip editing and multi-variant rendering.
"""

__version__ = "0.1.0"
__author__ = "Keith Lawson"

from .core import Word2GitProcessor
from .ingest import WordIngester
from .render import VariantRenderer
from .extract import SDTExtractor
from .validate import RoundTripValidator

__all__ = [
    "Word2GitProcessor",
    "WordIngester",
    "VariantRenderer",
    "SDTExtractor",
    "RoundTripValidator"
]