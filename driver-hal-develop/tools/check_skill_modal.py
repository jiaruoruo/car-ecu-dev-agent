#!/usr/bin/env python3
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('D:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find skill modal specific sections and check for ## / ###
# Skill modal functions: _selectSkillL1, _renderSkillFMEditor, _renderKnAreaEditor,
#   _renderInstrEditor, _rebuildSSEditor, _renderSSMetadata

# Extract each function's content
def extract_func(name, text):
    start = text.find('function ' + name)
    if start < 0:
        start = text.find('async function ' + name)
    if start < 0:
        return None
    # Find next 'function' or end
    end = len(text)
    for m in re.finditer(r'\nfunction |\nasync function ', text[start+20:]):
        end = start + 20 + m.start()
        break
    return text[start:end]

skill_funcs = [
    '_selectSkillL1',
    '_renderSkillFMEditor', 
    '_renderKnAreaEditor',
    '_renderInstrEditor',
    '_rebuildSSEditor',
    '_renderSSMetadata',
    '_buildSkillL1Nav',
]

print("=== Checking Skills Modal Functions for ##/### ===\n")
for fname in skill_funcs:
    body = extract_func(fname, content)
    if body is None:
        print("NOT FOUND:", fname)
        continue
    hashes = re.findall(r'editor-level[^>]*>[#]+<', body)
    inline_hashes = re.findall(r'>[#]+</span>', body)
    all_hashes = hashes + inline_hashes
    if all_hashes:
        print("STILL HAS ##/###:", fname, "->", all_hashes[:5])
    else:
        print("CLEAN:", fname)
    
print("\n=== Instruction cards check ===")
# Look for ### in cardsHtml and newCardsHtml in _renderInstrEditor
instr = extract_func('_renderInstrEditor', content)
if instr:
    if '###' in instr:
        # Find the context
        idx = instr.find('###')
        print("FOUND ### in _renderInstrEditor at local pos", idx)
        print("Context:", repr(instr[max(0,idx-100):idx+200]))
    else:
        print("CLEAN: No ### in _renderInstrEditor")

print("\n=== Check _renderChildEditor (Agent modal, should keep ###) ===")
child_editor = extract_func('_renderChildEditor', content)
if child_editor and '###' in child_editor:
    print("INFO: _renderChildEditor still has ### (Agent modal, expected)")
