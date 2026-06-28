#!/usr/bin/env python3
"""Robust extraction of a JSON array/object from messy LLM output (prose, ```fences, etc.)."""
import json, re
def extract_json(txt):
    # 1) fenced code block ```json ... ```
    for m in re.finditer(r"```(?:json)?\s*(.+?)```", txt, re.S):
        for cand in (m.group(1),):
            try: return json.loads(cand)
            except: pass
    # 2) the largest balanced [...] or {...}
    for opener,closer in (("[","]"),("{","}")):
        start=txt.find(opener)
        while start!=-1:
            depth=0
            for i in range(start,len(txt)):
                if txt[i]==opener: depth+=1
                elif txt[i]==closer:
                    depth-=1
                    if depth==0:
                        cand=txt[start:i+1]
                        try: return json.loads(cand)
                        except: break
            start=txt.find(opener,start+1)
    # 3) direct
    try: return json.loads(txt)
    except: return None
if __name__=="__main__":
    import sys
    d=extract_json(open(sys.argv[1]).read())
    print(type(d).__name__, len(d) if hasattr(d,'__len__') else "")
