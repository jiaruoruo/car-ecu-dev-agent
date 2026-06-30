#!/usr/bin/env python3
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('D:/AI/myproject/driver-hal-develop/gui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("File length:", len(content))

# Check 1: arrow is on the LEFT (before delete button in ss card header)
pos = content.find("toggleSSCard('${bodyId}'")
if pos >= 0:
    snippet = content[pos:pos+600]
    arr_pos = snippet.find('ss-card-arr')
    del_pos = snippet.find('btn-wf-del')
    if arr_pos >= 0 and del_pos >= 0:
        if arr_pos < del_pos:
            print("PASS: Arrow (ss-card-arr) is LEFT of delete button")
        else:
            print("FAIL: Arrow (ss-card-arr) is still RIGHT of delete button")
    else:
        print("WARN: Could not find both in context; arr=%d del=%d" % (arr_pos, del_pos))
else:
    print("WARN: toggleSSCard not found")

# Check 2
if '<span class="editor-level">##</span><span class="editor-ttl">${cfg.icon}' not in content:
    print("PASS: ## removed from _rebuildSSEditor hdr")
else:
    print("FAIL: ## still in _rebuildSSEditor hdr")

# Check 3
needle3 = '<span class="editor-level">##</span>\n      <span class="editor-ttl">${escHtml(sec.title)}'
if needle3 not in content:
    print("PASS: ## removed from _selectSkillL1 editor")
else:
    print("FAIL: ## still in _selectSkillL1 editor")

# Check 4: ### removed
if '>###</span>' not in content:
    print("PASS: ### removed from all instruction cards")
else:
    idx = content.find('>###</span>')
    print("FAIL: ### still found at index %d" % idx)

# List all remaining editor-level spans
el_matches = re.findall(r'<span class="editor-level">([^<]+)</span>', content)
print("\nRemaining editor-level spans:", el_matches)

# Show the actual ss card header
print("\n--- SS Card header snippet ---")
pos2 = content.find("toggleSSCard('${bodyId}'")
if pos2 >= 0:
    print(content[pos2:pos2+500])
