#!/usr/bin/env python3
"""Shows which domains your TV contacts and how this blocklist treats each one.

Input is one of:
  - AdGuard Home's query log, querylog.json (one JSON object per line). It lives
    in AdGuard Home's data folder on the machine running AdGuard Home, e.g.
    /opt/AdGuardHome/data/ (Linux), /opt/adguardhome/work/data/ (Docker)
    or AdGuardHome\\data\\ (Windows).
  - Any text containing domains, e.g. rows copied from the AdGuard Home or
    Pi-hole query log page. Pass "-" to paste it (finish with Ctrl+Z, Enter on
    Windows or Ctrl+D elsewhere).

Usage:
  python scripts/analyze_querylog.py querylog.json --client 192.168.1.50
  python scripts/analyze_querylog.py copied-log.txt
  python scripts/analyze_querylog.py -

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


DOMAIN = re.compile(r"(?<![\w/.-])(?:[a-z0-9_](?:[a-z0-9_-]*[a-z0-9_])?\.)+[a-z]{2,}(?![\w/.-])", re.I)
# File names that show up in pasted text (e.g. this script's own output), not domains
NOT_DOMAIN = re.compile(r"\.(txt|json|py|md|yml|yaml|csv|log|list|conf)$", re.I)


def read_lines(path):
    if path == "-":
        print("Paste the log, then press Ctrl+Z and Enter (Windows) or Ctrl+D:", file=sys.stderr)
        return sys.stdin.read().splitlines()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        sys.exit(f"File not found: {path}\n\n"
                 "querylog.json is on the machine that runs AdGuard Home (see --help for the usual\n"
                 "folders). If you can't get at it, copy the rows from the query log page into a\n"
                 "text file and pass that instead, or pass '-' and paste them.")


def read_domains(path, client):
    counts = Counter()
    for line in read_lines(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("{"):
            entry = json.loads(line)
            if client and entry.get("IP") != client:
                continue
            domains = [entry.get("QH", "")]
        else:
            domains = [d for d in DOMAIN.findall(line) if not NOT_DOMAIN.search(d)]
        for domain in domains:
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
    shown = [row for row in rows if args.all or row[0] == "unknown"]
    if not shown:
        print("No unknown domains: every domain is either blocked or protected.")
        print("Run again with --all to see the full list.")
        return
    print(f"{'status':<10} {'queries':>7}  domain")
    for status, n, domain in shown:
        mark = "?" if status == "unknown" and HINT.search(domain) else " "
        print(f"{status:<10} {n:>7} {mark}{domain}")
    if summary["unknown"]:
        print()
        print("'?' = name suggests ads or tracking. Check what breaks before adding it to sources/,")
        print("and add domains the TV needs to sources/never-block.txt.")


if __name__ == "__main__":
    main()
