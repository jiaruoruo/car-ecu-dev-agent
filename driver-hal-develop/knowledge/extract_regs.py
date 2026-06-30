import fitz

PDF_PATH = r'D:\AI\myproject\driver-hal-develop\knowledge\Infineon-TLF35584-DS-v02_00-EN.pdf'
OUT_PATH = r'D:\AI\myproject\driver-hal-develop\knowledge\reg_detail.txt'

pdf = fitz.open(PDF_PATH)
lines = []
for pg in [168, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 205, 206, 207, 208, 209, 210, 211, 212, 213]:
    if pg <= len(pdf):
        t = pdf[pg-1].get_text()
        lines.append('\n====== PDF PAGE %d ======\n' % pg)
        lines.append(t)
pdf.close()

content = ''.join(lines)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print('Written %d chars' % len(content))
