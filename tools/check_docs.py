#!/usr/bin/env python3
"""Documentation consistency checks for the TaskFlow docs repos.

Kept in sync across taskflow-docs and taskflow-api-docs; stdlib only.

Hard checks (exit 1 on any failure):
  1. SUMMARY coverage - every content page of a space is listed in that
     space's SUMMARY.md, and every SUMMARY entry points at a real file.
     A directory containing its own SUMMARY.md is its own space; a
     SUMMARY containing a GitBook `builtin:openapi` block is generated
     and is only checked for existence.
  2. Internal links - every relative Markdown link resolves to an
     existing file, and a `#anchor` matches a heading in the target
     (GitHub slug rules).
  3. README coverage - every root-space content file is mentioned in
     README.md (by name, or by its top-level directory, e.g. `adr/`),
     and every backticked `.md`/`.yaml` filename in README.md exists.

Platform files are not corpus pages: anything under a `.github/`
directory and a root-level `SECURITY.md` are ignored by every
check (GitHub reads them; GitBook does not publish them).

Soft check (report only, unless --strict-external):
  4. External links - every http(s) URL answers with a 2xx/3xx status.

Usage: check_docs.py [--external] [--external-only] [--strict-external]
Run from the repository root.
"""

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path.cwd()
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.M)
BACKTICK_FILE_RE = re.compile(r"`([^`\s]+\.(?:md|yaml))`")

failures = []
notes = []


def fail(where, msg):
    failures.append(f"{where}: {msg}")


def slugify(heading):
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\- ]", "", slug, flags=re.UNICODE)
    return slug.replace(" ", "-")


def heading_slugs(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    slugs = {}
    for h in HEADING_RE.findall(text):
        base = slugify(h)
        slug = base
        n = 0
        while slug in slugs:
            n += 1
            slug = f"{base}-{n}"
        slugs[slug] = True
    return slugs


def md_files(base):
    return sorted(
        p
        for p in base.rglob("*.md")
        if ".git" not in p.parts
        and ".github" not in p.parts
        and not (p.name == "SECURITY.md" and p.parent == ROOT)
    )


def find_spaces():
    spaces = []
    for summary in sorted(ROOT.rglob("SUMMARY.md")):
        if ".git" not in summary.parts:
            spaces.append(summary.parent)
    return spaces


def space_of(path, spaces):
    best = None
    for s in spaces:
        if path == s or s in path.parents:
            if best is None or len(s.parts) > len(best.parts):
                best = s
    return best


def rel(p):
    return str(p.relative_to(ROOT))


def check_summaries(spaces):
    for space_dir in spaces:
        summary = space_dir / "SUMMARY.md"
        text = summary.read_text(encoding="utf-8", errors="replace")
        if "builtin:openapi" in text:
            notes.append(f"{rel(summary)}: generated OpenAPI reference; existence only")
            continue
        listed = set()
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#")[0]
            listed.add((space_dir / target).resolve())
        content = {
            p.resolve()
            for p in md_files(space_dir)
            if space_of(p, spaces) == space_dir and p.name != "SUMMARY.md"
        }
        for p in sorted(content - listed):
            fail(rel(summary), f"page not listed in SUMMARY: {rel(p)}")
        for p in sorted(listed - content):
            fail(rel(summary), f"SUMMARY lists a missing page: {rel(p)}")


def check_internal_links(spaces):
    slug_cache = {}
    for path in md_files(ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            dest = path.parent / file_part if file_part else path
            if file_part and not dest.exists():
                fail(rel(path), f"broken link: {target}")
                continue
            if anchor and dest.suffix == ".md" and dest.exists():
                if dest not in slug_cache:
                    slug_cache[dest] = heading_slugs(dest)
                if anchor not in slug_cache[dest]:
                    fail(rel(path), f"broken anchor: {target}")


def check_readme(spaces):
    readme = ROOT / "README.md"
    if not readme.exists():
        fail("README.md", "missing")
        return
    text = readme.read_text(encoding="utf-8", errors="replace")
    root_space = ROOT
    for p in md_files(ROOT):
        if space_of(p, spaces) != root_space or p.name in ("README.md", "SUMMARY.md"):
            continue
        parts = p.relative_to(ROOT).parts
        covered = f"`{p.name}`" in text or (len(parts) > 1 and f"`{parts[0]}/`" in text)
        if not covered:
            fail("README.md", f"content file not covered by the contents table: {rel(p)}")
    all_files = {p.name for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
    for token in sorted(set(BACKTICK_FILE_RE.findall(text))):
        if Path(token).name not in all_files:
            fail("README.md", f"mentions a file that does not exist: {token}")


def check_external():
    urls = set()
    for path in md_files(ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        urls.update(re.findall(r"https?://[^\s)\"'<>]+", text))
    bad = []
    for url in sorted(urls):
        try:
            req = urllib.request.Request(url, method="HEAD",
                                         headers={"User-Agent": "check_docs/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                code = r.status
        except Exception as e:  # noqa: BLE001 - report any fetch failure
            code = getattr(e, "code", None) or str(e)
        if not (isinstance(code, int) and 200 <= code < 400):
            bad.append(f"{url} -> {code}")
    return bad


def main():
    args = set(sys.argv[1:])
    spaces = find_spaces()
    if "--external-only" not in args:
        check_summaries(spaces)
        check_internal_links(spaces)
        check_readme(spaces)
    external_bad = []
    if args & {"--external", "--external-only", "--strict-external"}:
        external_bad = check_external()
        for line in external_bad:
            print(f"external link problem: {line}")
    for n in notes:
        print(f"note: {n}")
    if failures:
        print(f"\n{len(failures)} consistency failure(s):")
        for f in failures:
            print(f"  FAIL {f}")
        return 1
    if external_bad and "--strict-external" in args:
        print(f"\n{len(external_bad)} external link failure(s) (strict)")
        return 1
    print("docs checks passed"
          + (f" ({len(external_bad)} external link problem(s), non-blocking)"
             if external_bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
