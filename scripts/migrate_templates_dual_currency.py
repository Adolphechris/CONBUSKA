#!/usr/bin/env python3
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / 'templates'

FLOAT_RE = re.compile(r"(\{\{\s*([A-Za-z0-9_\.]+)\s*\|\s*floatformat(?:\s*:\s*\d+)?\s*\}\})\s*FC\b")
SIMPLE_RE = re.compile(r"(\{\{\s*([A-Za-z0-9_\.]+)\s*\}\})\s*FC\b")

def ensure_load_caisse_tags(text):
    if '{% load caisse_tags %}' in text:
        return text
    # prefer inserting after an existing load line
    m = re.search(r"(\{%\s*load\s+[A-Za-z0-9_\s]+%\})", text)
    if m:
        return text[:m.end()] + '\n{% load caisse_tags %}' + text[m.end():]
    # else insert after extends or at top
    m2 = re.search(r"(\{%\s*extends\s+.*?%\})", text)
    if m2:
        return text[:m2.end()] + '\n{% load caisse_tags %}' + text[m2.end():]
    return '{% load caisse_tags %}\n' + text

def replace_floatformat(match):
    whole = match.group(1)
    var = match.group(2)
    usd_var = var + '_usd'
    replacement = (
        "{% if " + usd_var + " %}{% autoescape off %}{{ " + usd_var + "|dual_amount }}{% endautoescape %}{% else %}" + whole + " FC{% endif %}"
    )
    return replacement

def migrate_file(path: Path):
    text = path.read_text(encoding='utf-8')
    new_text = FLOAT_RE.sub(replace_floatformat, text)
    new_text = SIMPLE_RE.sub(replace_floatformat, new_text)
    if new_text != text:
        new_text = ensure_load_caisse_tags(new_text)
        path.write_text(new_text, encoding='utf-8')
        return True
    return False

def main():
    changed = []
    for p in sorted(TEMPLATES_DIR.rglob('*.html')):
        try:
            if migrate_file(p):
                changed.append(str(p.relative_to(TEMPLATES_DIR.parent)))
        except Exception as e:
            print('ERROR', p, e)
    # Second pass: remove redundant nested ifs like {% else %}{% if X_usd %}...{% endif %}
    nested_re = re.compile(r"{%\s*else\s*%}\s*{%\s*if\s+([A-Za-z0-9_\.]+)_usd\s*%}(.*?){%\s*endif\s*%}", re.S)
    normalized = []
    for p in sorted(TEMPLATES_DIR.rglob('*.html')):
        txt = p.read_text(encoding='utf-8')
        new_txt = txt
        # apply until stable
        while True:
            newer = nested_re.sub(r"{% else %}\2", new_txt)
            if newer == new_txt:
                break
            new_txt = newer
        if new_txt != txt:
            p.write_text(new_txt, encoding='utf-8')
            normalized.append(str(p.relative_to(TEMPLATES_DIR.parent)))
    if normalized:
        print('Normalized nested conditionals in %d files:' % len(normalized))
        for c in normalized:
            print(' -', c)
    # Additional cleanup: collapse repeated tags created by multiple passes
    re_if_repeat = re.compile(r'({%\s*if\s+([A-Za-z0-9_\.]+?_usd)\s*%}\s*){2,}')
    re_autoescape_repeat = re.compile(r'({%\s*autoescape\s+off\s*%}\s*\{\{\s*[A-Za-z0-9_\.]+\|dual_amount\s*\}\}\s*{%\s*endautoescape\s*%}\s*{%\s*else\s*%})+', re.S)
    re_else_repeat = re.compile(r'({%\s*else\s*%}\s*){2,}')
    cleaned = []
    for p in sorted(TEMPLATES_DIR.rglob('*.html')):
        txt = p.read_text(encoding='utf-8')
        new_txt = txt
        new_txt = re_if_repeat.sub(r'{% if \2 %}', new_txt)
        new_txt = re_autoescape_repeat.sub(r'{% else %}', new_txt)
        new_txt = re_else_repeat.sub(r'{% else %}', new_txt)
        if new_txt != txt:
            p.write_text(new_txt, encoding='utf-8')
            cleaned.append(str(p.relative_to(TEMPLATES_DIR.parent)))
    if cleaned:
        print('Cleaned redundant tag sequences in %d files:' % len(cleaned))
        for c in cleaned:
            print(' -', c)
    # Restore missing dual_amount in empty if blocks like: {% if X_usd %}{% else %}
    empty_if_re = re.compile(r"{%\s*if\s+([A-Za-z0-9_\.]+?_usd)\s*%}\s*{%\s*else\s*%}")
    restored = []
    for p in sorted(TEMPLATES_DIR.rglob('*.html')):
        txt = p.read_text(encoding='utf-8')
        def repl(m):
            var = m.group(1)
            return "{% if " + var + " %}{% autoescape off %}{{ " + var + "|dual_amount }}{% endautoescape %}{% else %}"
        new_txt = empty_if_re.sub(repl, txt)
        if new_txt != txt:
            p.write_text(new_txt, encoding='utf-8')
            restored.append(str(p.relative_to(TEMPLATES_DIR.parent)))
    if restored:
        print('Restored dual_amount in %d files:' % len(restored))
        for c in restored:
            print(' -', c)
    if changed:
        print('Modified %d files:' % len(changed))
        for c in changed:
            print(' -', c)
    else:
        print('No files modified')

if __name__ == '__main__':
    main()
