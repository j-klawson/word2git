--[[
Word2Git: Pandoc Lua filter for normalizing Word document conversion
Copyright (C) 2025 Keith Lawson

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

Pandoc Lua filter for normalizing Word document conversion.
Handles heading IDs, figure captions, table normalization, and cross-references.
]]--

local function generate_id(text)
    -- Generate stable IDs for headings and figures
    local id = text:lower()
    id = id:gsub("[^%w%s%-]", "")  -- Remove special chars except hyphens and spaces
    id = id:gsub("%s+", "-")       -- Replace spaces with hyphens
    id = id:gsub("%-+", "-")       -- Collapse multiple hyphens
    id = id:gsub("^%-", "")        -- Remove leading hyphen
    id = id:gsub("%-$", "")        -- Remove trailing hyphen
    return id
end

local function normalize_heading(elem)
    -- Ensure headings have stable IDs
    if not elem.identifier or elem.identifier == "" then
        local text = pandoc.utils.stringify(elem.content)
        elem.identifier = generate_id(text)
    end
    return elem
end

local function normalize_image(elem)
    -- Add stable IDs to images for cross-referencing
    local caption_text = pandoc.utils.stringify(elem.caption)
    if caption_text ~= "" and (not elem.identifier or elem.identifier == "") then
        -- Generate ID based on caption or filename
        local id_base = caption_text
        if id_base == "" then
            id_base = elem.src:match("([^/]+)%.[^%.]*$") or "image"
        end
        elem.identifier = "fig:" .. generate_id(id_base)
    end
    return elem
end

local function normalize_table(elem)
    -- Ensure tables have proper captions and IDs
    if elem.caption and #elem.caption > 0 then
        local caption_text = pandoc.utils.stringify(elem.caption)
        if not elem.identifier or elem.identifier == "" then
            elem.identifier = "tbl:" .. generate_id(caption_text)
        end
    end
    return elem
end

local function normalize_code_block(elem)
    -- Ensure code blocks have proper language tags
    if not elem.classes or #elem.classes == 0 then
        -- Try to detect language from content or add generic tag
        local content = elem.text:lower()
        if content:match("^%s*<%?xml") or content:match("<%w+[^>]*>") then
            elem.classes = {"xml"}
        elseif content:match("function%s+%w+") or content:match("var%s+%w+") then
            elem.classes = {"javascript"}
        elseif content:match("def%s+%w+") or content:match("import%s+%w+") then
            elem.classes = {"python"}
        else
            elem.classes = {"text"}
        end
    end
    return elem
end

local function clean_spans(elem)
    -- Remove unnecessary spans that don't add semantic value
    if elem.t == "Span" and #elem.classes == 0 and not elem.identifier and #elem.attributes == 0 then
        return elem.content
    end
    return elem
end

-- Return the filter functions
return {
    {Header = normalize_heading},
    {Image = normalize_image},
    {Table = normalize_table},
    {CodeBlock = normalize_code_block},
    {Span = clean_spans}
}