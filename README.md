# 📺 TV-Blockliste

[![Listen prüfen](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/check.yml/badge.svg)](https://github.com/PCTestAdmin/tv-blocklist/actions/workflows/check.yml)
![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-blue)

Eine DNS-Blockliste **nur für Smart-TVs**. Sie sperrt Werbung auf dem Startbildschirm, ACR-Tracking (der Fernseher meldet dem Hersteller, was du gerade schaust) und Telemetrie – **ohne** Anmeldung, App-Store, Streaming-Apps oder Updates zu blockieren.

Für **AdGuard Home** und **Pi-hole**.

---

## Inhalt

- [Schnellstart](#schnellstart)
- [Welche Liste?](#welche-liste)
- [Was wird gesperrt – und was nie](#was-wird-gesperrt--und-was-nie)
- [Unterstützte Fernseher](#unterstützte-fernseher)
- [Wenn etwas nicht mehr geht](#wenn-etwas-nicht-mehr-geht)
- [Mitmachen](#mitmachen)
- [Lizenz](#lizenz)

## Schnellstart

### AdGuard Home

1. **Filter → DNS-Sperrlisten → Sperrliste hinzufügen → Benutzerdefinierte Liste hinzufügen**
2. Name: `TV-Blockliste`, URL:
   ```
   https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/adguard.txt
   ```
3. **Speichern** – fertig. AdGuard Home aktualisiert die Liste automatisch.

### Pi-hole

1. **Lists** (ältere Versionen: **Adlists**) öffnen
2. Adresse eintragen und **Add** klicken:
   ```
   https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/hosts.txt
   ```
3. **Tools → Update Gravity** (oder `pihole -g`)

> **Wichtig:** Der Fernseher muss deinen AdGuard bzw. Pi-hole auch als DNS-Server benutzen. Trage ihn im Router (z. B. FRITZ!Box: *Heimnetz → Netzwerk → Netzwerkeinstellungen → IPv4 → Lokaler DNS-Server*) oder direkt in den Netzwerkeinstellungen des Fernsehers ein. Prüfen kannst du das im Abfrageprotokoll: Dort müssen Anfragen von der IP des Fernsehers auftauchen.

## Welche Liste?

| | **Standard** (~120 Regeln) | **Streng** (~155 Regeln) |
|---|---|---|
| Werbung und Werbe-Banner auf dem Startbildschirm | ✅ | ✅ |
| ACR-Tracking (was du schaust) | ✅ | ✅ |
| Hersteller-Telemetrie, Fehlerberichte, Nutzungsstatistik | ✅ | ✅ |
| HbbTV-Werbung, Tracking und Reichweitenmessung | ✅ | ✅ |
| Empfehlungsreihen auf LG- und Google-TV-Startseiten | – | ✅ |
| HbbTV-Apps privater Sender und Shopping-Kanäle | – | ✅ |
| Telemetrie mit unklarem Zweck | – | ✅ |
| Anmeldung, App-Store, Apps, Updates | nie gesperrt | nie gesperrt |

**Standard** hat keine bekannten Nebenwirkungen. **Streng** nimmt bewusst Funktionen weg: Empfehlungsreihen bleiben leer, und der rote Knopf von z. B. RTL II, SAT.1 oder QVC startet nicht mehr.

**Empfehlung:** Mit **Standard** anfangen. Wer keine Empfehlungen und keine Sender-Einblendungen will, wechselt auf **Streng**.

### Alle Formate

| Format | Standard | Streng | Für |
|---|---|---|---|
| AdGuard | [`adguard.txt`](lists/adguard.txt) | [`adguard-strict.txt`](lists/adguard-strict.txt) | AdGuard Home, AdGuard DNS |
| Hosts | [`hosts.txt`](lists/hosts.txt) | [`hosts-strict.txt`](lists/hosts-strict.txt) | Pi-hole, Router, `/etc/hosts` |
| Domains | [`domains.txt`](lists/domains.txt) | [`domains-strict.txt`](lists/domains-strict.txt) | Tools, die reine Domainlisten erwarten |

Rohdaten-Adresse: `https://raw.githubusercontent.com/PCTestAdmin/tv-blocklist/main/lists/<datei>`

## Was wird gesperrt – und was nie

Viele TV-Blocklisten sperren ganze Hersteller-Domains und legen damit Anmeldung, App-Store oder Updates lahm. Diese Liste geht den umgekehrten Weg:

- **Nur einzelne, eindeutig zugeordnete Domains** – keine pauschalen Sperren ganzer Hersteller-Clouds, keine Ausnahme-Konstrukte.
- **Schutzliste [`sources/never-block.txt`](sources/never-block.txt):** Domains, die Fernseher nachweislich brauchen (Konto, Uhrzeit, App-Store, Startbildschirm, Firmware-Updates, Netflix, YouTube, Mediatheken). Der Build **bricht ab**, sobald eine Regel eine davon treffen würde – auch über Subdomains oder Platzhalter.
- **Bekannte Fehlerquellen bewusst weggelassen**, z. B. `samsungcloudsolution.com` (pauschal), `lgtvsdp.com`, `api.*.hismarttv.com`, die Google-TV-Startseite und die Netflix-Telemetrie `customerevents.netflix.com`.
- **Keine allgemeinen Werbenetzwerke** wie `doubleclick.net` – die gehören in eine normale Werbeblockliste und bringen manche werbefinanzierte TV-App zum Hängen.

## Unterstützte Fernseher

| Hersteller / System | Standard | Streng |
|---|---|---|
| Samsung (Tizen) | Werbung, ACR, Smart-Hub-Banner, Fehlerberichte | – |
| LG (webOS) | Werbung, ACR, Datensammlung (CDP) | Empfehlungsreihen |
| Hisense / VIDAA (auch Smart Tech, Toshiba) | Werbe-Empfehlungen, Protokoll-Upload | Telemetrie |
| Sony Bravia | Telemetrie, ACR (Samba TV) | Konfigurations-Telemetrie |
| Panasonic Viera | Nutzungsstatistik, Werbung | Sicherheits-Telemetrie |
| Philips, Toshiba, TCL | Werbung, ACR (Samba TV) | Portal-Telemetrie |
| Vizio | ACR (Inscape) | – |
| Roku, Amazon Fire TV, Xiaomi | Werbung, Telemetrie | Amazon-Protokolle |
| Google TV / Android TV | – | Empfehlungsreihen |
| HbbTV (deutsche Sender) | Werbe-Proxy, Tracking, Reichweitenmessung | Apps privater Sender |
| Netflix | Telemetrie | – |

**Hisense / VIDAA:** Getestet auf einem Smart Tech 55UV10V1 (Firmware V0302.01.00S.N0317). Gesperrt werden die Empfehlungs-Kacheln (`recommend-ui-eu`) und der Protokoll-Upload (`policy-jrnl-eu`). Alle anderen `vidaahub.com`-Dienste – Anmeldung, Startbildschirm, Uhrzeit, Region, Sprachsteuerung, Updates – stehen in der Schutzliste. Wer weitere eindeutige Werbedomains im Abfrageprotokoll findet: bitte melden!

**Warum nicht tausende Einträge?** Große Listen erreichen ihre Größe mit allgemeinen Werbe- und Tracking-Domains aus dem Web. Die gehören in eine normale Blockliste (z. B. HaGeZi), die du parallel nutzen kannst. Diese Liste enthält nur Domains, die Fernseher selbst aufrufen – und davon gibt es nur einige hundert.

## Wenn etwas nicht mehr geht

1. Im Abfrageprotokoll nach der **IP des Fernsehers** filtern.
2. Die gesperrten Domains rund um den Zeitpunkt des Fehlers ansehen.
3. Verdächtige Domain **entsperren** und testen.
4. Hat das geholfen, bitte ein [Issue](https://github.com/PCTestAdmin/tv-blocklist/issues) anlegen mit **Modell, Firmware-Version und Domain**. Die Domain wird dann aus der Liste entfernt und in die Schutzliste aufgenommen.

Tritt der Fehler nur mit **Streng** auf: auf **Standard** zurückwechseln.

## Mitmachen

Die Regeln stehen nach Hersteller sortiert in [`sources/standard/`](sources/standard) und [`sources/strict/`](sources/strict), eine Domain pro Zeile:

```
domain.tld          Domain und alle Subdomains sperren
a.*.domain.tld      Platzhalter (nur im AdGuard-Format)
# Kommentar         die erste Kommentarzeile ist der Abschnittstitel
```

Nach jeder Änderung die Listen neu bauen und beides committen:

```bash
python scripts/build.py
```

Der Build und die GitHub Action prüfen bei jedem Push:

- Ist jede Domain gültig?
- Gibt es Duplikate oder Regeln, die schon durch eine andere abgedeckt sind?
- Trifft eine Regel eine Domain aus der Schutzliste?
- Sind die Dateien in `lists/` aktuell?

**Neue Domains** bitte nur, wenn sie im eigenen Abfrageprotokoll vom Fernseher kamen und nachweislich Werbung oder Tracking liefern – mit Gerätemodell im Pull Request. Eine Domain, die etwas kaputt macht, gehört in [`never-block.txt`](sources/never-block.txt).

## Lizenz

MIT, siehe [LICENSE](LICENSE). Viele Einträge und die Hinweise auf unverzichtbare Domains stammen aus [Perflyst/PiHoleBlocklist](https://github.com/Perflyst/PiHoleBlocklist) (MIT).
