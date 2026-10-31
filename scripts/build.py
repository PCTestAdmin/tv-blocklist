#!/usr/bin/env python3
"""Baut die TV-Blocklisten aus sources/ in alle Ausgabeformate unter lists/.

Quellformat (eine Regel pro Zeile):
  domain.tld        Domain und alle Subdomains sperren
  @@domain.tld      Ausnahme (nur im AdGuard-Format möglich)
  a.*.domain.tld    Platzhalter (nur im AdGuard-Format möglich)
  # Text            Kommentar; die erste Kommentarzeile ist der Abschnittstitel

sources/never-block.txt listet Domains, die der Fernseher braucht. Der Build
bricht ab, wenn eine Regel eine davon sperren würde.

Aufruf:  python scripts/build.py          baut lists/
         python scripts/build.py --check  prüft nur, ob lists/ aktuell ist
"""
import datetime
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
LISTS = ROOT / "lists"

TITLE = "TV-Blockliste"
HOMEPAGE = "https://github.com/PCTestAdmin/tv-blocklist"
LABEL = re.compile(r"^[a-z0-9*]([a-z0-9*-]{0,61}[a-z0-9*])?$")

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


class Rule:
    def __init__(self, domain, allow, source, line):
        self.domain = domain
        self.allow = allow
        self.wildcard = "*" in domain
        self.where = f"{source.relative_to(ROOT).as_posix()}:{line}"


def parse(path):
    """Gibt (Titel, Regeln) einer Quelldatei zurück und bricht bei Fehlern ab."""
    title, rules, errors = None, [], []
    for no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            title = title or line.lstrip("# ").strip()
            continue
        allow = line.startswith("@@")
        domain = line[2:] if allow else line
        domain = domain.lower()
        labels = domain.split(".")
        if len(labels) < 2 or not all(LABEL.match(l) for l in labels):
            errors.append(f"{path.relative_to(ROOT).as_posix()}:{no}: ungültige Domain '{line}'")
            continue
        rules.append(Rule(domain, allow, path, no))
    if errors:
        sys.exit("\n".join(errors))
    return title or path.stem, rules


def load(tier):
    return [parse(p) for p in sorted((SOURCES / tier).glob("*.txt"))]


def blocks(rule, domain):
    """True, wenn die Sperrregel diese Domain (oder sie als Subdomain) trifft."""
    return (domain == rule.domain or domain.endswith("." + rule.domain)
            or fnmatch(domain, rule.domain) or fnmatch(domain, "*." + rule.domain))


def check(sections):
    """Bricht ab bei doppelten, überflüssigen oder geschützten Regeln."""
    rules = [r for _, rs in sections for r in rs]
    _, protected = parse(SOURCES / "never-block.txt")
    seen, errors = {}, []
    for r in rules:
        key = ("@@" if r.allow else "") + r.domain
        if key in seen:
            errors.append(f"{r.where}: doppelt (schon in {seen[key]})")
        seen[key] = r.where
        if r.allow:
            continue
        for p in protected:
            if blocks(r, p.domain):
                errors.append(f"{r.where}: sperrt '{p.domain}', das der Fernseher braucht ({p.where})")
        for other in rules:
            if other is not r and not other.allow and other.domain != r.domain and blocks(other, r.domain):
                errors.append(f"{r.where}: überflüssig, schon durch '{other.domain}' ({other.where}) gesperrt")
    if errors:
        sys.exit("\n".join(errors))


def header(comment, name, description, version, count):
    return [
        f"{comment} Title: {TITLE} – {name}",
        f"{comment} Description: {description}",
        f"{comment} Homepage: {HOMEPAGE}",
        f"{comment} Version: {version}",
        f"{comment} Rules: {count}",
        f"{comment} License: MIT",
        "",
    ]


def render(sections, fmt, name, description, version):
    comment = "!" if fmt == "adguard" else "#"
    body, count = [], 0
    for title, rules in sections:
        lines = []
        for r in rules:
            if fmt == "adguard":
                lines.append(f"{'@@' if r.allow else ''}||{r.domain}^")
            elif r.allow or r.wildcard:
                continue  # hosts und Domainlisten kennen weder Ausnahmen noch Platzhalter
            elif fmt == "hosts":
                lines.append(f"0.0.0.0 {r.domain}")
            else:
                lines.append(r.domain)
        if lines:
            body += [f"{comment} {title}", *lines, ""]
            count += sum(1 for l in lines if not l.startswith("@@"))
    return "\n".join(header(comment, name, description, version, count) + body)


def outputs(version):
    standard = load("standard")
    strict = standard + load("strict")
    check(strict)
    variants = {
        "standard": (standard, "Werbung, ACR und Tracking auf Smart-TVs. Sicher für den Alltag."),
        "strict": (strict, "Standard plus Hersteller-Telemetrie und Startseiten-Inhalte. Kann Apps oder Updates stören."),
    }
    files = {}
    for variant, (sections, desc) in variants.items():
        suffix = "" if variant == "standard" else "-strict"
        name = "Standard" if variant == "standard" else "Streng"
        files[f"adguard{suffix}.txt"] = render(sections, "adguard", name, desc, version)
        files[f"hosts{suffix}.txt"] = render(sections, "hosts", name, desc, version)
        files[f"domains{suffix}.txt"] = render(sections, "domains", name, desc, version)
    return files


def strip_version(text):
    return re.sub(r"^[!#] Version: .*$", "", text, flags=re.M)


def main():
    version = datetime.date.today().strftime("%Y.%m.%d")
    files = outputs(version)
    if "--check" in sys.argv:
        stale = [n for n, t in files.items()
                 if not (LISTS / n).exists()
                 or strip_version((LISTS / n).read_text(encoding="utf-8")) != strip_version(t)]
        if stale:
            sys.exit("Veraltet, bitte 'python scripts/build.py' ausführen: " + ", ".join(stale))
        print("lists/ ist aktuell.")
        return
    LISTS.mkdir(exist_ok=True)
    for name, text in files.items():
        (LISTS / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"lists/{name}")


if __name__ == "__main__":
    main()
