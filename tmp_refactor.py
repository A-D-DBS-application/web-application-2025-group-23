import re
from pathlib import Path

root = Path("app/templates")
skip = {"base.html", "marketplace.html", "login.html", "register.html", "start.html"}

flash_re = re.compile(
    r"\{\%\s*with messages = get_flashed_messages\(with_categories=true\).*?\{\%\s*endwith\s*\%\}",
    re.S,
)
css_static_re = re.compile(r"<link[^>]+rel=['\"]stylesheet['\"][^>]+url_for\([^>]*>", re.I)
meta_re = re.compile(r"<meta[^>]+>", re.I)


def extract_class(attrs: str):
    cls = ""
    new_attrs = attrs
    for quote in ('"', "'"):
        m = re.search(rf'class={quote}(.*?){quote}', new_attrs)
        if m:
            cls = m.group(1).strip()
            new_attrs = new_attrs.replace(m.group(0), "")
            break
    return cls, new_attrs.strip()


for path in root.glob("*.html"):
    if path.name in skip:
        continue
    text = path.read_text()
    body_match = re.search(r"<body([^>]*)>(.*?)</body>", text, re.S)
    if not body_match:
        continue

    body_attrs_raw = body_match.group(1)
    body_html = body_match.group(2)
    body_html = flash_re.sub("", body_html).strip()

    head_match = re.search(r"<head>(.*?)</head>", text, re.S)
    head_content = head_match.group(1) if head_match else ""
    title_match = re.search(r"<title>(.*?)</title>", head_content, re.S)
    title = title_match.group(1).strip() if title_match else "Barter.com"
    if title_match:
        head_content = head_content.replace(title_match.group(0), "")

    head_content = meta_re.sub("", head_content)
    head_content = css_static_re.sub("", head_content)
    extra_head = head_content.strip()

    body_class, other_attrs = extract_class(body_attrs_raw)

    lines = ['{% extends "base.html" %}']
    lines.append(f"{{% block title %}}{title}{{% endblock %}}")
    if extra_head:
        lines.append("\n{% block extra_head %}\n" + extra_head + "\n{% endblock %}")
    if body_class:
        lines.append(f"\n{{% block body_class %}}{body_class}{{% endblock %}}")
    if other_attrs:
        lines.append(f"\n{{% block body_attrs %}}{other_attrs}{{% endblock %}}")

    lines.append("\n{% block content %}")
    lines.append(body_html)
    lines.append("{% endblock %}")

    path.write_text("\n".join(lines))

