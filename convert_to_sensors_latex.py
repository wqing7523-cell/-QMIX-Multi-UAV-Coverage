#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将Markdown论文转换为Sensors期刊格式的LaTeX文件
"""

import subprocess
import os
import re
from pathlib import Path

# 文件路径
source_md = r"C:\Users\44358\Desktop\uav-qmix\paper_sensors_ready_chinese - 副本 (2).md"
output_tex = r"C:\Users\44358\Desktop\uav-qmix\submissions\sensors\manuscript_updated.tex"
template_tex = r"C:\Users\44358\Desktop\uav-qmix\submissions\sensors\manuscript.tex"

print("=" * 60)
print("Markdown to Sensors LaTeX Format")
print("=" * 60)

# 检查源文件
if not os.path.exists(source_md):
    print(f"Error: Source file not found: {source_md}")
    exit(1)

print(f"\n[OK] Source file: {source_md}")

# 步骤1: 使用pandoc将Markdown转换为LaTeX
print("\n[步骤1] 使用pandoc转换为LaTeX...")
temp_tex = r"C:\Users\44358\Desktop\uav-qmix\submissions\sensors\temp_converted.tex"

try:
    cmd = [
        "pandoc",
        source_md,
        "-o", temp_tex,
        "--from", "markdown+pipe_tables+tex_math_dollars",
        "--to", "latex",
        "--standalone",
        "--wrap=none"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print("✗ Pandoc转换失败")
        print(f"错误信息: {result.stderr}")
        exit(1)
    
    print("[OK] Pandoc conversion completed")
    
except FileNotFoundError:
    print("[ERROR] pandoc command not found")
    print("Please install pandoc and add it to PATH")
    exit(1)
except Exception as e:
    print(f"[ERROR] Conversion failed: {e}")
    exit(1)

# 步骤2: 读取转换后的LaTeX内容
print("\n[Step 2] Reading LaTeX content...")
try:
    with open(temp_tex, 'r', encoding='utf-8') as f:
        latex_content = f.read()
    print("[OK] LaTeX content read")
except Exception as e:
    print(f"[ERROR] Failed to read LaTeX file: {e}")
    exit(1)

# 步骤3: 读取Sensors模板
print("\n[Step 3] Reading Sensors template...")
try:
    with open(template_tex, 'r', encoding='utf-8') as f:
        template_content = f.read()
    print("[OK] Template read")
except Exception as e:
    print(f"[ERROR] Failed to read template: {e}")
    # 如果模板不存在，创建一个基本的Sensors模板
    template_content = """% Sensors Manuscript Template
\\documentclass[11pt]{article}
\\usepackage[margin=1in]{geometry}
\\usepackage{graphicx}
\\usepackage{booktabs}
\\usepackage{amsmath,amssymb}
\\usepackage{hyperref}
\\usepackage[UTF8]{ctex}

\\title{Multi-UAV Coverage Path Planning via QMIX: Scalability Study under Large Grids and Obstacles}
\\author{[Authors to be completed]}
\\date{}

\\begin{document}
\\maketitle

% Content will be inserted here

\\end{document}
"""

# 步骤4: 提取LaTeX文档主体内容（去除documentclass等）
print("\n[步骤4] 提取文档主体内容...")
# 查找\begin{document}和\end{document}之间的内容
doc_start = latex_content.find('\\begin{document}')
doc_end = latex_content.find('\\end{document}')

if doc_start != -1 and doc_end != -1:
    body_content = latex_content[doc_start+len('\\begin{document}'):doc_end].strip()
    print("[OK] Document body extracted")
else:
    # 如果没有找到，使用全部内容
    body_content = latex_content
    print("[WARNING] Document environment not found, using full content")

# 步骤5: 创建符合Sensors格式的LaTeX文件
print("\n[Step 5] Generating Sensors format LaTeX...")

# 从模板中提取前导部分（documentclass等）
template_doc_start = template_content.find('\\begin{document}')
if template_doc_start != -1:
    template_preamble = template_content[:template_doc_start]
    template_end = template_content[template_content.find('\\end{document}'):]
else:
    template_preamble = template_content
    template_end = "\\end{document}"

# 组合新的LaTeX文件
new_latex = template_preamble + "\n\\begin{document}\n\\maketitle\n\n" + body_content + "\n\n" + template_end

# 步骤6: 保存新文件
print("\n[Step 6] Saving Sensors format file...")
try:
    with open(output_tex, 'w', encoding='utf-8') as f:
        f.write(new_latex)
    print(f"[OK] File saved: {output_tex}")
except Exception as e:
    print(f"[ERROR] Failed to save file: {e}")
    exit(1)

# 清理临时文件
if os.path.exists(temp_tex):
    try:
        os.remove(temp_tex)
        print("[OK] Temporary file cleaned")
    except:
        pass

print("\n" + "=" * 60)
print("Conversion completed!")
print("=" * 60)
print(f"\nOutput file: {output_tex}")
print("\nNotes:")
print("1. Please check the generated LaTeX file for correct formatting")
print("2. Download official Sensors template (mdpi.cls) from MDPI website")
print("3. Integrate generated LaTeX content into official template")
print("4. Check figure/table paths are correct")
print("5. Add author information, references, etc.")

