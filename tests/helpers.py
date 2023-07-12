


def non_blank_lines_list(text: str) -> list[str]:
    lines = text.splitlines()
    lines = [ln for ln in lines if not ln == '']
    return lines

def non_blank_lines_str(text: str) -> str:
    lines = text.splitlines()
    lines = [ln for ln in lines if not ln == '']
    outstr = '\n'.join(lines)
    return outstr