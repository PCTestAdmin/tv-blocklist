#!/usr/bin/env python3
"""Shows which domains your TV contacts and how this blocklist treats each one.

Input is either AdGuard Home's query log (querylog.json, one JSON object per
line, found in AdGuard Home's data/ folder) or a plain text file with one
domain per line (e.g. copied from Pi-hole's query log).

Usage:
  python scripts/analyze_querylog.py querylog.json --client 192.168.178.33
  python scripts/analyze_querylog.py domains.txt

Every domain is reported as one of:
  standard   blocked by the standard list
  strict     blocked only by the strict list
  protected  on the protection list (the TV needs it)
  unknown    not covered yet; candidates for a new rule are marked with '?'
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

HINT = re.compile(r"(^|[.-])(ads?|adv|track(ing)?|log(s|sdk)?|stats?|metrics?|telemetry|analytics?|"
                  r"acr|jrnl|beacon|report|rpt|collect|events?|crash|monetization|mntz|abtest|"
                  r"recommend|imp|impr|survey)([.-]|\d|$)")


def read_domains(path, client):
    counts = Counter()
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("{"):
                entry = json.loads(line)
                if client and entry.get("IP") != client:
                    continue
                domain = entry.get("QH", "")
            else:
                domain = line.split()[-1]
            if domain:
                counts[domain.lower().rstrip(".")] += 1
    return counts


def load_rules():
    def rules(paths):
        return [r for p in paths for r in build.parse(p)[1]]
    std = rules([*sorted((build.SOURCES / "standard").glob("*.txt")),
                 *sorted(build.UPSTREAM.glob("*.standard.txt"))])
    strict = rules([*sorted((build.SOURCES / "strict").glob("*.txt")),
                    *sorted(build.UPSTREAM.glob("*.strict.txt"))])
    return std, strict, build.load_protected()


def classify(domain, std, strict, protected):
    if domain in protected or any(p.startswith("*.") and domain.endswith(p[1:]) for p in protected):
        return "protected"
    if any(r.blocks(domain) for r in std):
        return "standard"
    if any(r.blocks(domain) for r in strict):
        return "strict"
    return "unknown"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="querylog.json or a text file with one domain per line")
    ap.add_argument("--client", help="only count queries from this client IP (querylog.json only)")
    ap.add_argument("--all", action="store_true", help="list every domain, not just unknown ones")
    args = ap.parse_args()

    counts = read_domains(args.file, args.client)
    if not counts:
        sys.exit("No queries found. Check the file and --client.")
    std, strict, protected = load_rules()
    rows = [(classify(d, std, strict, protected), n, d) for d, n in counts.most_common()]

    summary = Counter(status for status, _, _ in rows)
    print(f"{len(rows)} domains, {sum(counts.values())} queries: "
          + ", ".join(f"{summary[s]} {s}" for s in ("standard", "strict", "protected", "unknown")))
    print()
    print(f"{'status':<10} {'queries':>7}  domain")
    for status, n, domain in rows:
        if status != "unknown" and not args.all:
            continue
        mark = "?" if status == "unknown" and HINT.search(domain) else " "
        print(f"{status:<10} {n:>7} {mark}{domain}")
    print()
    print("'?' = name suggests ads or tracking. Check what breaks before adding it to sources/,")
    print("and add domains the TV needs to sources/never-block.txt.")


if __name__ == "__main__":
    main()
