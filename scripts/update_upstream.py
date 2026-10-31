#!/usr/bin/env python3
"""Fetches the upstream TV lists into sources/upstream/.

Only lists under a licence compatible with MIT are imported. Each upstream
list becomes three files:
  <name>.standard.txt   block rules for the standard tier
  <name>.strict.txt     block rules that upstream only ships in its strict tier
  <name>.allow.txt      domains upstream marks as required (added to the protection list)

build.py merges these with our own sources and drops every upstream rule that
would hit a protected domain, so upstream can never break what we protect.

Usage:  python scripts/update_upstream.py
"""
import datetime
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sources" / "upstream"

UPSTREAM = [
    {
        "name": "okazakee",
        "home": "https://github.com/Okazakee/tv-dns-blocklist",
        "license": "MIT, Copyright (c) 2026 okazakee",
        "standard": "https://raw.githubusercontent.com/Okazakee/tv-dns-blocklist/main/blocklist.txt",
        "strict": "https://raw.githubusercontent.com/Okazakee/tv-dns-blocklist/main/blocklist-strict.txt",
    },
]

BLOCK = re.compile(r"^\|\|([a-z0-9_*.-]+)\^$")
ALLOW = re.compile(r"^@@\|\|?([a-z0-9_*.-]+)\^(\$important)?$")
REGEX = re.compile(r"^/.+/$")
PLAIN = re.compile(r"^[a-z0-9_.-]+\.[a-z]{2,}$")

sys.stdout.reconfigure(encoding="utf-8")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tv-blocklist-updater"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse(text):
    """Returns (block rules, allowed domains, skipped lines) in upstream order."""
    block, allow, skipped = [], [], []
    for raw in text.splitlines():
        line = raw.strip().lower()
        if not line or line.startswith(("!", "#")):
            continue
        if m := ALLOW.match(line):
            allow.append(m.group(1))
        elif m := BLOCK.match(line):
            block.append(m.group(1))
        elif REGEX.match(line) or PLAIN.match(line):
            block.append(line)
        else:
            skipped.append(line)
    return block, allow, skipped


def unique(items):
    return list(dict.fromkeys(items))


def write(path, header, rules):
    path.write_text("\n".join(header + rules) + "\n", encoding="utf-8", newline="\n")
    print(f"{path.relative_to(ROOT).as_posix()}: {len(rules)}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    for src in UPSTREAM:
        std_block, std_allow, std_skip = parse(fetch(src["standard"]))
        strict_block, strict_allow, strict_skip = parse(fetch(src["strict"]))
        std = unique(std_block)
        strict = [r for r in unique(strict_block) if r not in set(std)]
        allow = unique(std_allow + strict_allow)
        for line in unique(std_skip + strict_skip):
            print(f"  skipped (unsupported syntax): {line}")

        def header(title):
            return [
                f"# {src['name']}: {title}",
                f"# Imported from {src['home']} on {today} by scripts/update_upstream.py.",
                f"# Licence: {src['license']}. Do not edit by hand.",
            ]

        write(OUT / f"{src['name']}.standard.txt", header("standard tier"), std)
        write(OUT / f"{src['name']}.strict.txt", header("strict-only rules"), strict)
        write(OUT / f"{src['name']}.allow.txt", header("domains marked as required"), allow)


if __name__ == "__main__":
    main()
