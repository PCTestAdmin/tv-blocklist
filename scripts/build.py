#!/usr/bin/env python3
"""Builds every list under lists/ from sources/.

Source format (one rule per line):
  domain.tld        block the domain and all its subdomains
  a.*.domain.tld    wildcard (AdGuard format only)
  /^regex$/         regular expression (AdGuard format only)
  # text            comment; the first comment line is the section title

sources/never-block.txt lists domains a TV needs ("*.domain.tld" protects every
subdomain). Together with the upstream *.allow.txt files it forms the
protection list:
  - our own rules must never hit a protected domain, or the build fails;
  - upstream rules that would hit one are dropped and reported.

Usage:  python scripts/build.py          build lists/
        python scripts/build.py --check  only verify that lists/ is up to date
"""
import datetime
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
UPSTREAM = SOURCES / "upstream"
LISTS = ROOT / "lists"

TITLE = "TV Blocklist"
HOMEPAGE = "https://github.com/PCTestAdmin/tv-blocklist"
LABEL = re.compile(r"^[a-z0-9_*]([a-z0-9_*-]{0,61}[a-z0-9_*])?$")

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


class Rule:
    def __init__(self, text, source, line):
        self.text = text
        self.regex = re.compile(text[1:-1]) if text.startswith("/") else None
        self.wildcard = self.regex is None and "*" in text
        self.where = f"{source.relative_to(ROOT).as_posix()}:{line}"

    @property
    def plain(self):
        """True if the rule can be written to hosts and domain lists."""
        return self.regex is None and not self.wildcard

    def blocks(self, domain):
        """True if this rule blocks the domain (directly or as a subdomain)."""
        if self.regex:
            return bool(self.regex.search(domain))
        return (domain == self.text or domain.endswith("." + self.text)
                or fnmatch(domain, self.text) or fnmatch(domain, "*." + self.text))

    def hits(self, protected):
        """True if this rule would block a protected entry ("*.x" = every subdomain of x)."""
        if not protected.startswith("*."):
            return self.blocks(protected)
        base = protected[2:]
        if self.blocks(base):
            return True
        if self.regex:
            return bool(self.regex.search("probe." + base))
        return fnmatch(self.text, protected)


def valid(text):
    if text.startswith("/"):
        if not text.endswith("/") or len(text) < 3:
            return False
        try:
            re.compile(text[1:-1])
        except re.error:
            return False
        return True
    labels = text.split(".")
    return len(labels) >= 2 and all(LABEL.match(l) for l in labels)


def parse(path):
    """Returns (title, rules) of a source file and exits on invalid lines."""
    title, rules, errors = None, [], []
    for no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            title = title or line.lstrip("# ").strip()
            continue
        text = line if line.startswith("/") else line.lower()
        if not valid(text):
            errors.append(f"{path.relative_to(ROOT).as_posix()}:{no}: invalid rule '{line}'")
            continue
        rules.append(Rule(text, path, no))
    if errors:
        sys.exit("\n".join(errors))
    return title or path.stem, rules


def load_protected():
    files = [SOURCES / "never-block.txt", *sorted(UPSTREAM.glob("*.allow.txt"))]
    protected = {}
    for f in files:
        for r in parse(f)[1]:
            protected.setdefault(r.text, r.where)
    return protected


def check_own(sections, protected):
    """Exits on duplicate, redundant or protected-domain rules in our own sources."""
    rules = [r for _, rs in sections for r in rs]
    seen, errors = {}, []
    for r in rules:
        if r.text in seen:
            errors.append(f"{r.where}: duplicate (already in {seen[r.text]})")
        seen[r.text] = r.where
        for p, where in protected.items():
            if r.hits(p):
                errors.append(f"{r.where}: blocks '{p}', which TVs need ({where})")
        if r.plain:
            for other in rules:
                if other is not r and other.plain and other.text != r.text and other.blocks(r.text):
                    errors.append(f"{r.where}: redundant, already blocked by '{other.text}' ({other.where})")
    if errors:
        sys.exit("\n".join(errors))


def filter_upstream(sections, protected, existing):
    """Drops upstream rules that hit protected domains or that we already cover."""
    kept, dropped = [], []
    for title, rules in sections:
        out = []
        for r in rules:
            if r.text in existing:
                continue
            if r.plain and any(e.plain and e.blocks(r.text) for e in existing.values()):
                continue
            hit = next((p for p in protected if r.hits(p)), None)
            if hit:
                dropped.append(f"{r.where}: '{r.text}' would block '{hit}'")
                continue
            existing[r.text] = r
            out.append(r)
        kept.append((title, out))
    return kept, dropped


def header(comment, name, description, version, count):
    return [
        f"{comment} Title: {TITLE} – {name}",
        f"{comment} Description: {description}",
        f"{comment} Homepage: {HOMEPAGE}",
        f"{comment} Version: {version}",
        f"{comment} Rules: {count}",
        f"{comment} License: MIT (see LICENSE for upstream credits)",
        "",
    ]


def render(sections, fmt, name, description, version):
    comment = "!" if fmt == "adguard" else "#"
    body, count = [], 0
    for title, rules in sections:
        lines = []
        for r in rules:
            if fmt == "adguard":
                lines.append(r.text if r.regex else f"||{r.text}^")
            elif not r.plain:
                continue  # hosts and domain lists support neither wildcards nor regex
            elif fmt == "hosts":
                lines.append(f"0.0.0.0 {r.text}")
            else:
                lines.append(r.text)
        if lines:
            body += [f"{comment} {title}", *lines, ""]
            count += len(lines)
    return "\n".join(header(comment, name, description, version, count) + body)


def render_allowlist(protected, version):
    domains = sorted(p for p in protected if "*" not in p)
    lines = header("!", "Allowlist",
                   "Optional. Unblocks domains TVs need when other, broader lists block them.",
                   version, len(domains))
    return "\n".join(lines + [f"@@||{d}^$important" for d in domains]) + "\n"


def outputs(version, report=False):
    protected = load_protected()
    own_std = [parse(p) for p in sorted((SOURCES / "standard").glob("*.txt"))]
    own_strict = [parse(p) for p in sorted((SOURCES / "strict").glob("*.txt"))]
    check_own(own_std + own_strict, protected)

    existing = {r.text: r for _, rs in own_std + own_strict for r in rs}
    up_std, dropped_std = filter_upstream(
        [parse(p) for p in sorted(UPSTREAM.glob("*.standard.txt"))], protected, existing)
    up_strict, dropped_strict = filter_upstream(
        [parse(p) for p in sorted(UPSTREAM.glob("*.strict.txt"))], protected, existing)
    if report:
        for d in dropped_std + dropped_strict:
            print(f"  dropped upstream rule {d}")

    standard = own_std + up_std
    strict = standard + own_strict + up_strict
    variants = {
        "": ("Standard", standard,
             "Smart-TV ads, ACR tracking and telemetry. No known side effects."),
        "-strict": ("Strict", strict,
                    "Standard plus home-screen recommendations, broadcaster HbbTV apps and "
                    "telemetry of unclear purpose. Removes some features."),
    }
    files = {}
    for suffix, (name, sections, desc) in variants.items():
        for fmt in ("adguard", "hosts", "domains"):
            files[f"{fmt}{suffix}.txt"] = render(sections, fmt, name, desc, version)
    files["adguard-allowlist.txt"] = render_allowlist(protected, version)
    return files


def strip_version(text):
    return re.sub(r"^[!#] Version: .*$", "", text, flags=re.M)


def main():
    version = datetime.date.today().strftime("%Y.%m.%d")
    check = "--check" in sys.argv
    files = outputs(version, report=not check)
    if check:
        stale = [n for n, t in files.items()
                 if not (LISTS / n).exists()
                 or strip_version((LISTS / n).read_text(encoding="utf-8")) != strip_version(t)]
        if stale:
            sys.exit("Out of date, run 'python scripts/build.py': " + ", ".join(stale))
        print("lists/ is up to date.")
        return
    LISTS.mkdir(exist_ok=True)
    for old in LISTS.glob("*.txt"):
        if old.name not in files:
            old.unlink()
    for name, text in files.items():
        (LISTS / name).write_text(text, encoding="utf-8", newline="\n")
        count = re.search(r"Rules: (\d+)", text).group(1)
        print(f"lists/{name}: {count} rules")


if __name__ == "__main__":
    main()
