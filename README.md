# 📺 TV Blocklist

[![Check lists](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/check.yml/badge.svg)](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/check.yml)
[![Update upstream lists](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/update-upstream.yml/badge.svg)](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/update-upstream.yml)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

A DNS blocklist **for smart TVs only**. It blocks home-screen ads, ACR tracking (your TV reporting what you watch) and vendor telemetry, **without** breaking sign-in, the app store, streaming apps or firmware updates.

Works with **AdGuard Home**, **Pi-hole** and any DNS blocker that reads hosts or domain lists.

---

- [Quick start](#quick-start)
- [Which list?](#which-list)
- [What gets blocked, and what never does](#what-gets-blocked-and-what-never-does)
- [Supported TVs](#supported-tvs)
- [Something broke?](#something-broke)
- [Find what your TV sends](#find-what-your-tv-sends)
- [Contributing](#contributing)
- [Credits and license](#credits-and-license)

## Quick start

### AdGuard Home

1. **Filters → DNS blocklists → Add blocklist → Add a custom list**
2. Name: `TV Blocklist`, URL:
   ```
   https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/adguard.txt
   ```
3. **Save**. AdGuard Home keeps the list up to date automatically.

### Pi-hole

1. Open **Lists** (older versions: **Adlists**)
2. Add this address and click **Add**:
   ```
   https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/hosts.txt
   ```
3. **Tools → Update Gravity** (or `pihole -g`)

> **Your TV has to use your DNS server.** Set it in your router's DHCP settings or in the TV's network settings, then check the query log for requests from the TV's IP. Some TVs (Samsung, Vizio, some VIDAA models) ignore the DHCP DNS server; redirect port 53 to your blocker on the router if nothing shows up.

## Which list?

| | **Standard** (~300 rules) | **Strict** (~420 rules) |
|---|:---:|:---:|
| Home-screen ads and promo banners | ✅ | ✅ |
| ACR tracking (what you watch) | ✅ | ✅ |
| Vendor telemetry, crash reports, usage statistics | ✅ | ✅ |
| HbbTV ad proxy, tracking, audience measurement | ✅ | ✅ |
| Home-screen recommendation rows (LG, Google TV) | – | ✅ |
| HbbTV apps of commercial and shopping channels | – | ✅ |
| Telemetry of unclear purpose, generic ad networks used in TV apps | – | ✅ |
| Sign-in, app store, apps, updates | never blocked | never blocked |

**Standard** has no known side effects. **Strict** removes features on purpose: recommendation rows go empty and the red button of some commercial channels stops working.

Start with **Standard**. Switch to **Strict** if you don't want recommendations or broadcaster overlays.

### All formats

| Format | Standard | Strict | For |
|---|---|---|---|
| AdGuard | [`adguard.txt`](lists/adguard.txt) | [`adguard-strict.txt`](lists/adguard-strict.txt) | AdGuard Home, AdGuard DNS |
| Hosts | [`hosts.txt`](lists/hosts.txt) | [`hosts-strict.txt`](lists/hosts-strict.txt) | Pi-hole, routers, `/etc/hosts` |
| Domains | [`domains.txt`](lists/domains.txt) | [`domains-strict.txt`](lists/domains-strict.txt) | tools that expect plain domain lists |

Raw URL: `https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/<file>`

The AdGuard format has about 10 more rules than the others: wildcards (e.g. every regional `*-jrnl-*.vidaahub.com` endpoint) and regular expressions, which hosts files cannot express.

### Optional: allowlist

[`adguard-allowlist.txt`](lists/adguard-allowlist.txt) unblocks every domain on the protection list with `$important`. Add it **only** if a broad general-purpose list (e.g. HaGeZi Ultimate) breaks your TV. It overrides blocks from all your other lists for those domains.

## What gets blocked, and what never does

Many TV blocklists block whole vendor clouds and break sign-in, the store or updates along the way. This list works the other way round:

- **Specific hostnames, no blanket blocks** of vendor clouds.
- **Protection list.** [`sources/never-block.txt`](sources/never-block.txt) plus the allowlist of the upstream project hold over 200 domains TVs need: accounts, clock sync, app stores, home screens, firmware updates, DRM, voice control, Netflix, YouTube and broadcasters' catch-up apps. **The build fails** if one of our rules would block any of them, whether directly, via a parent domain, a wildcard or a regex.
- **Upstream rules are filtered too.** Rules imported from other lists that would hit a protected domain are dropped automatically. The build log shows each one.
- **Known troublemakers left out on purpose**, e.g. `samsungcloudsolution.com` as a whole, `lgtvsdp.com`, `nextlgsdp.com`, `myhomescreen.tv`, the Google TV launcher and Netflix's `customerevents`.

## Supported TVs

| Vendor / platform | Standard | Strict |
|---|---|---|
| **Hisense / VIDAA** (also Smart Tech, Toshiba VIDAA) | Ads, ad reporting, monetisation, logs (all regions), A/B tests, ACR | Shopping and recommendation widgets |
| **Samsung Tizen** | Ads, ACR, Smart Hub banners, Samsung Ads network, analytics, diagnostics reports | Data-intelligence collectors, config telemetry, TV Plus recommendations |
| **LG webOS** | Ads, ACR (Alphonso), customer data platform, recommendations backend | Content Store recommendations, log collector |
| **Sony Bravia** | Telemetry, measurement, ACR (Samba TV) | Config distribution |
| **Panasonic Viera** | Usage statistics, ads | Security telemetry |
| **Philips** (Titan OS / Net TV), **Toshiba**, **TCL** | Ads, telemetry, ACR (Samba TV) | Portal telemetry |
| **Vizio SmartCast** | ACR (Inscape), telemetry | Widgets |
| **TCL** | ACR (Samba TV) | – |
| **Roku** | Logs, ads, ACR | – |
| **Amazon Fire TV** | Ads, telemetry, ACR | Device metrics, surveys |
| **Xiaomi Mi TV** | Tracking, ad SDK | – |
| **Google TV / Android TV** | – | Recommendation rows |
| **HbbTV** (European broadcasters) | Ad proxy, tracking, audience measurement | Apps of commercial and shopping channels |
| **Vewd** (app platform on VIDAA, Philips, Sony) | Logging | – |
| **Streaming apps** | Netflix telemetry | – |

**Hisense / VIDAA** is tested on a Smart Tech 55UV10V1 (firmware V0302.01.00S.N0317). Every other `vidaahub.com` service, including sign-in, home screen, clock, region, voice, payments and updates, is on the protection list.

**Why not thousands of rules?** Huge lists get their size from general web ad and tracking domains. Those belong in a general list such as HaGeZi or OISD, which you can run alongside this one. This list only contains domains that TVs contact, and there are only a few hundred of those.

## Something broke?

1. Filter your query log by the **TV's IP address**.
2. Look at the blocked domains around the time it failed.
3. **Unblock** the suspect and try again.
4. If that fixed it, [open an issue](https://github.com/PCTestAdmin/tv-blocklist/issues/new?template=something-broke.yml) with **model, firmware and domain**. It will be removed and added to the protection list.

If it only happens with **Strict**, switch back to **Standard**.

## Find what your TV sends

[`scripts/analyze_querylog.py`](scripts/analyze_querylog.py) shows how this list treats every domain your TV contacted. It reads either AdGuard Home's `querylog.json` or any text with domains in it, such as rows copied from the query log page.

`querylog.json` lives on the machine that runs AdGuard Home, in its data folder (`/opt/AdGuardHome/data/` on Linux, `/opt/adguardhome/work/data/` in Docker). Copy it next to the script, then:

```bash
python scripts/analyze_querylog.py querylog.json --client 192.168.1.50
```

No access to that machine? Filter the query log page by your TV, select the rows, copy them, and paste them in:

```bash
python scripts/analyze_querylog.py -
```

```
41 domains, 1873 queries: 9 standard, 2 strict, 24 protected, 6 unknown

status     queries  domain
unknown        212 ?rpt-xyz.vidaahub.com
unknown         31  epg.example-tv.com
```

Unknown domains whose names suggest ads or tracking are marked with `?`. Please [report them](https://github.com/PCTestAdmin/tv-blocklist/issues/new?template=new-domain.yml).

## Contributing

Rules live in [`sources/standard/`](sources/standard) and [`sources/strict/`](sources/strict), sorted by vendor, one per line:

```
domain.tld          block the domain and all subdomains
a.*.domain.tld      wildcard (AdGuard format only)
/^regex$/           regular expression (AdGuard format only)
# comment           the first comment line is the section title
```

Domains a TV needs go into [`sources/never-block.txt`](sources/never-block.txt). Rebuild after every change and commit both:

```bash
python scripts/build.py
```

The build and the GitHub Action check that every rule is valid, that there are no duplicates or rules already covered by another one, that no rule hits a protected domain, and that `lists/` is up to date.

Please only add domains your own TV contacted, together with the model, and say whether the TV kept working with them blocked.

### Upstream lists

[`scripts/update_upstream.py`](scripts/update_upstream.py) imports curated, MIT-licensed TV lists into [`sources/upstream/`](sources/upstream). A GitHub Action runs it every Monday and commits the result. Files in `sources/upstream/` are generated; don't edit them by hand.

## Credits and license

MIT, see [LICENSE](LICENSE). Built on the work of:

- [Okazakee/tv-dns-blocklist](https://github.com/Okazakee/tv-dns-blocklist) (MIT): imported unchanged and filtered through the protection list. Its [SOURCES.md](https://github.com/Okazakee/tv-dns-blocklist/blob/main/SOURCES.md) documents the evidence for each rule.
- [Perflyst/PiHoleBlocklist](https://github.com/Perflyst/PiHoleBlocklist) (MIT): many of the hand-picked rules and most of the breakage reports behind the protection list.
- [THectic-NL/Blocklists](https://github.com/THectic-NL/Blocklists) (MIT): additional hand-picked Samsung, LG and Vizio rules. Its smart-TV list is not imported as a whole because it blocks several domains on our protection list.
- [Watching TV with the Second-Party](https://arxiv.org/abs/2409.06203) (Anselmi et al., IMC 2024): ACR measurements on Samsung and LG TVs.
