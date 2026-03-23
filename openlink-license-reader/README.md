# OpenLink License Reader Skill

Parse and display OpenLink Software `.lic` license files in a clean, human-readable format.

## What It Does

- Reads ASN.1 DER-encoded OpenLink license files using `openssl asn1parse`
- Extracts all license fields: product, registrant, serial, expiry, edition, connections, CPUs, modules, clients, and more
- Flags **EXPIRED** licenses visually; shows **PERPETUAL** for non-expiring licenses
- Scans an entire directory and produces a summary table across all `.lic` files
- Shows raw ASN.1 dump only on explicit request

## Supported Platforms

| OS | Default License Path |
|---|---|
| macOS | `/Library/Application Support/openlink/Licenses` |
| Linux | `/etc/oplmgr/` |
| Windows | `C:\Program Files\OpenLink Software\UDA\bin\` |

`$OPL_LICENSE_DIR` env var overrides the default path. An explicit filename always takes precedence.

## Requirements

- `openssl` CLI (standard on macOS and Linux)
- Read access to the license file(s)

## Usage Examples

- "Read my Virtuoso license"
- "Check all OpenLink licenses"
- "Is my oplrqb.lic expired?"
- "Show me the license at /etc/oplmgr/oracle19.lic"
- "List all licenses in the default directory"

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main skill definition and execution steps |
| `references/asn1-field-map.md` | Field decode tables (WSType, Availability, Modules, Clients, Platform) |
| `references/openssl-asn1parse-guide.md` | Guide to reading raw openssl asn1parse output |

## Version

**1.0.0** — Initial release.
