"""
提取 TLF35584 PDF 中 ABIST/INITERR/MONSF2 寄存器相关文本
"""
import fitz
import re

PDF_PATH = r'D:\AI\myproject\driver-hal-develop\knowledge\Infineon-TLF35584-DS-v02_00-EN.pdf'
OUT_PATH = r'D:\AI\myproject\driver-hal-develop\knowledge\bist_regs.txt'

pdf = fitz.open(PDF_PATH)
pages_text = []
for i in range(len(pdf)):
    pages_text.append((i + 1, pdf[i].get_text()))
pdf.close()

keywords = [
    'ABIST', 'INITERR', 'MONSF2', 'MONSF0', 'MONSF1',
    'Logic BIST', 'Analog BIST', 'BIST',
    'ROM_FAIL', 'REG_FAIL', 'LOGIC_FAIL',
    'ABIST_CTRL', 'ABIST_SELECT',
    'Interrupt Flag', '0x1E', '0x1F', '0x26', '0x27', '0x28',
    'IF register', 'ABIST_INT',
]

results = []
for kw in keywords:
    found_pages = [(p, t) for p, t in pages_text if kw in t]
    if found_pages:
        results.append(f'\n{"="*60}')
        results.append(f'KEYWORD: [{kw}]  found on pages: {[p for p, _ in found_pages]}')
        # Show first 2 occurrences
        for p, t in found_pages[:2]:
            idx = t.find(kw)
            snippet = t[max(0, idx - 200):idx + 800]
            results.append(f'\n--- Page {p} ---')
            results.append(snippet)

output = '\n'.join(results)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'Written {len(output)} chars to {OUT_PATH}')
print(f'Total pages processed: {len(pages_text)}')
