import re
from pathlib import Path


def main() -> None:
    path = Path("paper_sensors_ready_chinese_v2.md")
    text = path.read_text(encoding="utf-8")

    lines = text.splitlines(keepends=True)

    # 找到参考文献标题行
    ref_start = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("## 参考文献"):
            ref_start = i
            break
    if ref_start is None:
        raise SystemExit("No reference section found")

    body = "".join(lines[:ref_start])
    refs_part = "".join(lines[ref_start:])

    # 1) 统计正文中各文献首次出现顺序
    # 支持 [6]、[6,7]、[4,8,11,12,14,15] 这类分组引用
    cite_pattern = re.compile(r"\[((?:\d+\s*,\s*)*\d+)\]")
    order: list[int] = []
    seen: set[int] = set()
    for m in cite_pattern.finditer(body):
        group = m.group(1)
        for part in group.split(","):
            idx = int(part.strip())
            if idx not in seen:
                seen.add(idx)
                order.append(idx)

    # old -> new 映射（按首次出现顺序编号，保持组内相对顺序）
    mapping = {old: new for new, old in enumerate(order, start=1)}

    # 重写正文中的编号
    def repl(m: re.Match[str]) -> str:
        group = m.group(1)
        new_nums: list[str] = []
        for part in group.split(","):
            old = int(part.strip())
            new = mapping.get(old)
            if new is None:
                # 保底：如果某个编号不在映射中，就原样保留
                new_nums.append(part.strip())
            else:
                new_nums.append(str(new))
        return "[" + ",".join(new_nums) + "]"

    body_new = cite_pattern.sub(repl, body)

    # 2) 解析参考文献条目
    refs_lines = refs_part.splitlines(keepends=True)
    header = refs_lines[0]  # “## 参考文献...”
    ref_text = "".join(refs_lines[1:]).lstrip("\n")

    blocks = []
    current: list[str] = []
    for line in ref_text.splitlines(keepends=True):
        if re.match(r"^\[\d+\]", line.strip()):
            if current:
                blocks.append("".join(current))
                current = []
        if line.strip() or current:
            current.append(line)
    if current:
        blocks.append("".join(current))

    # old_idx -> 原始 reference block
    ref_blocks: dict[int, str] = {}
    for blk in blocks:
        stripped = blk.lstrip()
        if not stripped:
            continue
        first_line = stripped.splitlines()[0]
        m = re.match(r"^\[(\d+)\]", first_line.strip())
        if not m:
            continue
        old_idx = int(m.group(1))
        ref_blocks[old_idx] = blk

    # 只保留正文中出现过且在参考文献中的条目，按首次出现顺序排序
    ordered_old = [old for old in order if old in ref_blocks]

    new_blocks: list[str] = []
    for new_idx, old_idx in enumerate(ordered_old, start=1):
        blk = ref_blocks[old_idx]
        lines_blk = blk.splitlines(keepends=True)
        if not lines_blk:
            continue
        first = lines_blk[0]
        new_first = re.sub(r"^\[\d+\]", f"[{new_idx}]", first)
        lines_blk[0] = new_first
        new_blocks.append("".join(lines_blk).rstrip() + "\n")

    refs_new = header.rstrip() + "\n\n" + "\n".join(
        b.rstrip() for b in new_blocks
    ) + "\n"

    new_content = body_new + refs_new
    path.write_text(new_content, encoding="utf-8")

    print(
        f"Renumbered references: {len(order)} unique citations in text,"
        f" {len(new_blocks)} entries in reference list."
    )


if __name__ == "__main__":
    main()


