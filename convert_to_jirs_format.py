#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Markdown paper to Journal of Intelligent & Robotic Systems (Springer) LaTeX format
"""

import re
import os
from pathlib import Path

def escape_latex(text):
    """Escape LaTeX special characters"""
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
        '\\': r'\textbackslash{}',
    }
    for char, replacement in special_chars.items():
        text = text.replace(char, replacement)
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
    
    # Extract main content (everything after Abstract and Keywords)
    main_content_match = re.search(r'---\n\n## 1\. Introduction\n\n(.*)', content, re.DOTALL)
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
\\usepackage{algorithm}
\\usepackage{algorithmicx}
\\usepackage{algpseudocode}
\\usepackage{natbib}
\\usepackage{geometry}
\\geometry{a4paper,margin=2.5cm}

% Title and author information
\\title{""" + escape_latex(title) + """}
\\author{""" + escape_latex(authors) + """\\\\
\\textit{""" + escape_latex(affiliation) + """}\\\\
\\texttt{""" + escape_latex(email) + """}}

\\date{\\today}

\\begin{document}

\\maketitle

\\begin{abstract}
""" + escape_latex(abstract) + """
\\end{abstract}

\\noindent\\textbf{Keywords:} """ + escape_latex(keywords) + """

\\section{Introduction}
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

def convert_markdown_to_latex_body(content):
    """Convert Markdown content to LaTeX body"""
    latex = content
    
    # Convert section headers
    latex = re.sub(r'^## (\d+)\. (.+)$', r'\\section{\2}', latex, flags=re.MULTILINE)
    latex = re.sub(r'^### (\d+\.\d+) (.+)$', r'\\subsection{\2}', latex, flags=re.MULTILINE)
    latex = re.sub(r'^#### (\d+\.\d+\.\d+) (.+)$', r'\\subsubsection{\2}', latex, flags=re.MULTILINE)
    
    # Convert bold text
    latex = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', latex)
    
    # Convert inline math (already in LaTeX format)
    # Keep $...$ as is
    
    # Convert citations [1] to \cite{ref1}
    def replace_citation(match):
        ref_num = match.group(1)
        return f'\\cite{{ref{ref_num}}}'
    latex = re.sub(r'\[(\d+)\]', replace_citation, latex)
    latex = re.sub(r'\[(\d+),(\d+)\]', lambda m: f'\\cite{{ref{m.group(1)},ref{m.group(2)}}}', latex)
    latex = re.sub(r'\[(\d+)-(\d+)\]', lambda m: f'\\cite{{ref{m.group(1)}--ref{m.group(2)}}}', latex)
    
    # Convert figures
    latex = re.sub(
        r'!\[(.+?)\]\((.+?)\)\n\n\*\*Figure (\d+)\.\*\* (.+)',
        lambda m: f'\\begin{{figure}}[htbp]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{{{m.group(2)}}}\n\\caption{{{escape_latex(m.group(4))}}}\n\\label{{fig:{m.group(3)}}}\n\\end{{figure}}',
        latex
    )
    
    # Convert tables (simplified)
    latex = re.sub(r'\| (.+?) \|', lambda m: ' & '.join(m.group(1).split('|')) + ' \\\\', latex)
    
    # Convert code blocks
    latex = re.sub(
        r'```\n(.*?)\n```',
        lambda m: f'\\begin{{verbatim}}\n{m.group(1)}\n\\end{{verbatim}}',
        latex,
        flags=re.DOTALL
    )
    
    # Convert itemize lists
    lines = latex.split('\n')
    result = []
    in_list = False
    for line in lines:
        if re.match(r'^[-•]\s+', line):
            if not in_list:
                result.append('\\begin{itemize}')
                in_list = True
            item_text = re.sub(r'^[-•]\s+', '', line)
            result.append(f'\\item {escape_latex(item_text)}')
        elif re.match(r'^\d+\.\s+', line):
            if not in_list:
                result.append('\\begin{enumerate}')
                in_list = True
            item_text = re.sub(r'^\d+\.\s+', '', line)
            result.append(f'\\item {escape_latex(item_text)}')
        else:
            if in_list:
                result.append('\\end{itemize}')
                in_list = False
            result.append(escape_latex(line))
    
    if in_list:
        result.append('\\end{itemize}')
    
    return '\n'.join(result)

def convert_references_to_latex(refs_content):
    """Convert Markdown references to LaTeX bibliography format"""
    lines = refs_content.strip().split('\n')
    latex_refs = []
    
    for line in lines:
        if re.match(r'^\[(\d+)\]', line):
            ref_num = re.match(r'^\[(\d+)\]', line).group(1)
            ref_text = re.sub(r'^\[\d+\]\s+', '', line)
            # Convert to LaTeX bibliography format
            latex_refs.append(f'\\bibitem{{ref{ref_num}}} {escape_latex(ref_text)}')
    
    return '\n'.join(latex_refs)

if __name__ == '__main__':
    md_file = r'C:\Users\44358\Desktop\uav-qmix\paper_sensors_ready_chinese_v2_english.md'
    output_file = r'C:\Users\44358\Desktop\uav-qmix\submissions\jirs\manuscript.tex'
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    markdown_to_latex(md_file, output_file)
    print("Conversion completed!")
