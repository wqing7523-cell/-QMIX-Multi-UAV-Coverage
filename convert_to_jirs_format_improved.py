#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Markdown paper to Journal of Intelligent & Robotic Systems (Springer) LaTeX format
Improved version with better LaTeX handling
"""

import re
import os
from pathlib import Path

def escape_latex_special(text):
    """Escape only LaTeX special characters, but preserve LaTeX commands and placeholders"""
    # Protect placeholders first (they contain underscores that shouldn't be escaped)
    placeholders = {}
    placeholder_pattern = r'(__[A-Z_]+_\d+__)'
    matches = re.findall(placeholder_pattern, text)
    for i, match in enumerate(set(matches)):  # Use set to avoid duplicates
        placeholder_key = f"__PLACEHOLDERPROTECT{i}__"
        placeholders[placeholder_key] = match
        text = text.replace(match, placeholder_key)
    
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
    }
    
    # Don't escape if inside math mode
    result = []
    in_math = False
    i = 0
    while i < len(text):
        if i < len(text) - 1 and text[i:i+2] == '$$':
            in_math = not in_math
            result.append('$$')
            i += 2
        elif text[i] == '$' and not in_math:
            in_math = True
            result.append('$')
            i += 1
        elif text[i] == '$' and in_math:
            in_math = False
            result.append('$')
            i += 1
        elif not in_math and text[i] in special_chars:
            result.append(special_chars[text[i]])
            i += 1
        else:
            result.append(text[i])
            i += 1
    
    text = ''.join(result)
    
    # Restore placeholders
    for placeholder_key, original in placeholders.items():
        text = text.replace(placeholder_key, original)
    
    return text

def markdown_to_latex(md_file, output_file):
    """Convert Markdown to LaTeX format for JIRS"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Title"
    
    # Extract authors and affiliation (placeholder)
    authors = "[Your Name], [Collaborator 1], [Collaborator 2]"
    affiliation = "[Your Affiliation]"
    email = "[Email]"
    
    # Extract abstract
    abstract_match = re.search(r'## Abstract\n\n(.*?)(?=\n\n---|\n\n##)', content, re.DOTALL)
    abstract = abstract_match.group(1).strip() if abstract_match else ""
    
    # Extract keywords
    keywords_match = re.search(r'\*\*Keywords\*\*\n\n(.+?)(?=\n\n---|\n\n##)', content, re.DOTALL)
    keywords = keywords_match.group(1).strip() if keywords_match else ""
    
    # Extract main content (everything after Abstract and Keywords, including section headers)
    main_content_match = re.search(r'---\n\n(## 1\. Introduction\n\n.*?)(?=\n\n---\n\n## References)', content, re.DOTALL)
    main_content = main_content_match.group(1) if main_content_match else ""
    
    # Extract references
    refs_match = re.search(r'## References\n\n(.*)', content, re.DOTALL)
    refs_content = refs_match.group(1) if refs_match else ""
    
    # Convert main content
    latex_body = convert_markdown_to_latex_body(main_content)
    
    # Convert references
    latex_refs = convert_references_to_latex(refs_content)
    
    # Build LaTeX document
    latex_doc = """\\documentclass[12pt,a4paper]{article}

% Springer JIRS format
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{amsmath,amssymb,amsfonts}
\\usepackage{graphicx}
\\usepackage{booktabs}
\\usepackage{array}
\\usepackage{algorithm}
\\usepackage{algorithmicx}
\\usepackage{algpseudocode}
\\usepackage{natbib}
\\usepackage{geometry}
\\geometry{a4paper,margin=2.5cm}

% Title and author information
\\title{""" + escape_latex_special(title) + """}
\\author{""" + escape_latex_special(authors) + """\\\\
\\textit{""" + escape_latex_special(affiliation) + """}\\\\
\\texttt{""" + escape_latex_special(email) + """}}

\\date{\\today}

\\begin{document}

\\maketitle

\\begin{abstract}
""" + process_abstract(abstract) + """
\\end{abstract}

\\noindent\\textbf{Keywords:} """ + escape_latex_special(keywords) + """

""" + latex_body + """

\\bibliographystyle{spbasic}
\\begin{thebibliography}{99}
""" + latex_refs + """
\\end{thebibliography}

\\end{document}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_doc)
    
    print(f"LaTeX file created: {output_file}")

def process_abstract(abstract):
    """Process abstract text, preserving math and converting properly"""
    # Split into paragraphs
    paragraphs = abstract.split('\n\n')
    processed = []
    for para in paragraphs:
        para = para.strip()
        if para:
            # Convert citations
            para = re.sub(r'\[(\d+)\]', r'\\cite{ref\1}', para)
            para = re.sub(r'\[(\d+),(\d+)\]', r'\\cite{ref\1,ref\2}', para)
            para = re.sub(r'\[(\d+)-(\d+)\]', r'\\cite{ref\1--ref\2}', para)
            # Escape special chars but preserve math
            para = escape_latex_special(para)
            processed.append(para)
    return '\n\n'.join(processed)

def convert_markdown_to_latex_body(content):
    """Convert Markdown content to LaTeX body"""
    lines = content.split('\n')
    result = []
    in_code_block = False
    in_table = False
    in_list = False
    list_type = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Handle code blocks
        if line.strip().startswith('```'):
            if not in_code_block:
                result.append('\\begin{verbatim}')
                in_code_block = True
            else:
                result.append('\\end{verbatim}')
                in_code_block = False
            i += 1
            continue
        
        if in_code_block:
            result.append(line)
            i += 1
            continue
        
        # Handle section headers
        if re.match(r'^## (\d+)\. (.+)$', line):
            match = re.match(r'^## (\d+)\. (.+)$', line)
            section_num = match.group(1)
            section_title = match.group(2)
            # Special handling for Introduction
            if section_num == '1' and 'Introduction' in section_title:
                result.append(f'\\section{{{escape_latex_special(section_title)}}}')
            else:
                result.append(f'\\section{{{escape_latex_special(section_title)}}}')
            i += 1
            continue
        
        if re.match(r'^### (\d+\.\d+) (.+)$', line):
            match = re.match(r'^### (\d+\.\d+) (.+)$', line)
            subsection_title = match.group(2)
            result.append(f'\\subsection{{{escape_latex_special(subsection_title)}}}')
            i += 1
            continue
        
        if re.match(r'^#### (\d+\.\d+\.\d+) (.+)$', line):
            match = re.match(r'^#### (\d+\.\d+\.\d+) (.+)$', line)
            subsubsection_title = match.group(2)
            result.append(f'\\subsubsection{{{escape_latex_special(subsubsection_title)}}}')
            i += 1
            continue
        
        # Handle horizontal rules
        if line.strip() == '---':
            i += 1
            continue
        
        # Handle figures
        if re.match(r'^!\[', line) and i + 1 < len(lines):
            fig_match = re.match(r'^!\[(.+?)\]\((.+?)\)', line)
            if fig_match:
                fig_caption = fig_match.group(1)
                fig_path = fig_match.group(2)
                # Look for Figure caption in next lines
                fig_num = None
                fig_desc = None
                for j in range(i+1, min(i+3, len(lines))):
                    fig_cap_match = re.match(r'\*\*Figure (\d+)\.\*\* (.+)', lines[j])
                    if fig_cap_match:
                        fig_num = fig_cap_match.group(1)
                        fig_desc = fig_cap_match.group(2)
                        break
                
                if fig_num:
                    result.append(f'\\begin{{figure}}[htbp]')
                    result.append(f'\\centering')
                    result.append(f'\\includegraphics[width=0.8\\textwidth]{{{fig_path}}}')
                    result.append(f'\\caption{{{escape_latex_special(fig_desc)}}}')
                    result.append(f'\\label{{fig:{fig_num}}}')
                    result.append(f'\\end{{figure}}')
                    # Skip the figure caption line
                    if fig_cap_match:
                        i += 2
                    else:
                        i += 1
                    continue
        
        # Handle tables (simplified - needs manual adjustment)
        if line.strip().startswith('|') and '---' not in line:
            if not in_table:
                result.append('\\begin{table}[htbp]')
                result.append('\\centering')
                result.append('\\begin{tabular}')
                in_table = True
            # Convert table row
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                latex_row = ' & '.join([escape_latex_special(c) for c in cells]) + ' \\\\'
                result.append(latex_row)
            i += 1
            continue
        
        if in_table and not line.strip().startswith('|'):
            result.append('\\end{tabular}')
            result.append('\\end{table}')
            in_table = False
        
        # Handle lists
        if re.match(r'^[-•]\s+', line):
            if not in_list or list_type != 'itemize':
                if in_list:
                    result.append(f'\\end{{{list_type}}}')
                result.append('\\begin{itemize}')
                in_list = True
                list_type = 'itemize'
            item_text = re.sub(r'^[-•]\s+', '', line)
            item_text = process_text_line(item_text)
            result.append(f'\\item {item_text}')
            i += 1
            continue
        
        if re.match(r'^\d+\.\s+', line):
            if not in_list or list_type != 'enumerate':
                if in_list:
                    result.append(f'\\end{{{list_type}}}')
                result.append('\\begin{enumerate}')
                in_list = True
                list_type = 'enumerate'
            item_text = re.sub(r'^\d+\.\s+', '', line)
            item_text = process_text_line(item_text)
            result.append(f'\\item {item_text}')
            i += 1
            continue
        
        # Close list if needed
        if in_list and line.strip() and not (re.match(r'^[-•]\s+', line) or re.match(r'^\d+\.\s+', line)):
            result.append(f'\\end{{{list_type}}}')
            in_list = False
            list_type = None
        
        # Process regular text line
        if line.strip():
            processed_line = process_text_line(line)
            result.append(processed_line)
        else:
            result.append('')
        
        i += 1
    
    # Close any open environments
    if in_list:
        result.append(f'\\end{{{list_type}}}')
    if in_table:
        result.append('\\end{tabular}')
        result.append('\\end{table}')
    
    return '\n'.join(result)

def process_text_line(line):
    """Process a single line of text"""
    # Convert citations first
    line = re.sub(r'\[(\d+)\]', r'\\cite{ref\1}', line)
    line = re.sub(r'\[(\d+),(\d+)\]', r'\\cite{ref\1,ref\2}', line)
    line = re.sub(r'\[(\d+)-(\d+)\]', r'\\cite{ref\1--ref\2}', line)
    
    # Convert bold
    line = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', line)
    
    # Convert italic (single asterisk, but not if it's part of **)
    line = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', line)
    
    # Now escape special characters, but skip LaTeX commands
    line = escape_latex_special_skip_commands(line)
    
    return line

def escape_latex_special_skip_commands(text):
    """Escape LaTeX special characters but skip LaTeX commands"""
    special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
    }
    
    result = []
    i = 0
    in_math = False
    in_command = False
    brace_depth = 0
    
    while i < len(text):
        char = text[i]
        
        # Handle math mode
        if i < len(text) - 1 and text[i:i+2] == '$$':
            in_math = not in_math
            result.append('$$')
            i += 2
            continue
        elif char == '$':
            in_math = not in_math
            result.append('$')
            i += 1
            continue
        
        # Handle LaTeX commands (don't escape inside them)
        if char == '\\' and not in_math:
            # Find the command name
            cmd_end = i + 1
            while cmd_end < len(text) and text[cmd_end].isalpha():
                cmd_end += 1
            result.append(text[i:cmd_end])
            i = cmd_end
            
            # Check if command has arguments
            if i < len(text) and text[i] == '{':
                in_command = True
                brace_depth = 1
                result.append('{')
                i += 1
                continue
            else:
                continue
        
        # Handle braces in commands
        if in_command:
            if char == '{':
                brace_depth += 1
                result.append('{')
            elif char == '}':
                brace_depth -= 1
                result.append('}')
                if brace_depth == 0:
                    in_command = False
            else:
                result.append(char)
            i += 1
            continue
        
        # Escape special characters (but not in math or commands)
        if not in_math and not in_command and char in special_chars:
            result.append(special_chars[char])
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)

def convert_references_to_latex(refs_content):
    """Convert Markdown references to LaTeX bibliography format"""
    lines = refs_content.strip().split('\n')
    latex_refs = []
    
    for line in lines:
        if re.match(r'^\[(\d+)\]', line):
            ref_num = re.match(r'^\[(\d+)\]', line).group(1)
            ref_text = re.sub(r'^\[\d+\]\s+', '', line)
            
            # Convert Markdown formatting to LaTeX
            # Convert **text** to \textbf{text}
            ref_text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', ref_text)
            # Convert *text* to \textit{text} (but not if it's part of **)
            ref_text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'\\textit{\1}', ref_text)
            
            # Escape special characters but preserve LaTeX commands
            ref_text = escape_latex_special_skip_commands(ref_text)
            
            latex_refs.append(f'\\bibitem{{ref{ref_num}}} {ref_text}')
    
    return '\n'.join(latex_refs)

if __name__ == '__main__':
    md_file = r'C:\Users\44358\Desktop\uav-qmix\paper_sensors_ready_chinese_v2_english.md'
    output_file = r'C:\Users\44358\Desktop\uav-qmix\submissions\jirs\manuscript.tex'
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    markdown_to_latex(md_file, output_file)
    print("Conversion completed!")
