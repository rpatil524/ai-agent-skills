#!/usr/bin/env python3
"""
Validate the RDF infographic strict harness contract.

Usage:
  python3 validate-harness-contract.py page.html --ttl graph.ttl --jsonld graph.jsonld
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def require(html: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in html:
        fail(label, failures)


def require_regex(html: str, pattern: str, label: str, failures: list[str]) -> None:
    if not re.search(pattern, html, re.S):
        fail(label, failures)


def require_any(html: str, needles: list[str], label: str, failures: list[str]) -> None:
    if not any(needle in html for needle in needles):
        fail(label, failures)


def require_any_regex(html: str, patterns: list[str], label: str, failures: list[str]) -> None:
    if not any(re.search(pattern, html, re.S) for pattern in patterns):
        fail(label, failures)


def validate_rdf(path: str | None, fmt: str, failures: list[str]) -> None:
    if not path:
        return
    try:
        from rdflib import Graph

        Graph().parse(path, format=fmt)
    except Exception as exc:  # pragma: no cover - diagnostics script
        fail(f"RDF parse failed for {path}: {exc}", failures)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html")
    parser.add_argument("--ttl")
    parser.add_argument("--jsonld")
    args = parser.parse_args()

    html_path = Path(args.html)
    html = html_path.read_text(encoding="utf-8")
    failures: list[str] = []

    require(html, 'rel="related"', "POSH related link missing", failures)
    require(html, 'rel="alternate"', "POSH alternate link missing", failures)
    require(html, 'application/ld+json', "Embedded JSON-LD missing", failures)

    require_any(html, ['class="section-nav"', 'id="nav-panel"', 'aria-label="Section navigation"'], "Navigation panel missing", failures)
    require_any_regex(html, [r'class="nav-toggle"[^>]*(aria-label="Expand navigation"|title="Expand)', r'id="nav-toggle"', r'toggleNav\('], "Navigation collapsed expand toggle missing", failures)
    require_any(html, ['theme-toggle', 'id="theme-btn"', 'themeCycle', 'toggleTheme'], "Page theme toggle missing", failures)

    require_any(html, ['id="kg-explorer"', 'id="kg"', 'Knowledge Graph Explorer'], "KG Explorer missing", failures)
    require_any(html, ['id="kgControlsToggle"', 'id="nav-toggle"', 'btn-basic', 'btn-advanced'], "KG controls/mode controls missing", failures)
    require_any_regex(html, [r'id="kgToolbar" hidden', r'#nav-body\{[^}]*max-height:0', r'id="settings-panel"\s+style="display:none', r'#settings-panel\{display:none'], "KG controls/settings are not clearly closed by default", failures)
    require_any(html, ['id="settingsPanel" hidden', 'id="settings-panel"', 'settingsPanel.hidden=true'], "Advanced settings panel missing", failures)
    require_any(html, ['data-mode="Basic"', 'btn-basic', "switchMode('basic')"], "Basic mode toggle missing", failures)
    require_any(html, ['data-mode="Advanced"', 'btn-advanced', "switchMode('advanced')"], "Advanced mode toggle missing", failures)
    require_any(html, ['data-density="Core"', 'density-core', "setDensity('core')"], "Core density toggle missing", failures)
    require_any(html, ['data-density="Full"', 'density-full', "setDensity('full')"], "Full density toggle missing", failures)
    require_any(html, ['data-advanced-control hidden', 'settings-btn', 'display:none'], "Advanced-only controls not hidden by default", failures)
    require_any(html, ['id="predicateSelectAll"', 'selectAll', 'Select All', 'All</button>'], "Predicate Select All missing", failures)
    require_any(html, ['id="predicateDeselectAll"', 'deselectAll', 'Deselect', 'None</button>'], "Predicate Deselect All missing", failures)
    require_any(html, ['id="literalToggle"', 'literal', 'Literals'], "Literal filter missing", failures)
    require_any(html, ['id="resolverPreference"', 'resolver', 'RESOLVER'], "Resolver preference/pattern missing", failures)
    require_any(html, ['id="arrowStyle"', 'arrow', 'marker-end'], "Arrow style/directed arrows missing", failures)
    require(html, 'd3@7', "D3 runtime missing", failures)
    require_any(html, ['clickDistance(6)', 'd3.drag()', '.drag()'], "D3 drag behavior missing", failures)
    require_any_regex(html, [r'\.append\([\'"]a[\'"]\).*?(href|xlink:href)', r'<a[^>]+href="https://linkeddata\.uriburner\.com/describe/\?url='], "Resolver-backed SVG/label anchors missing", failures)
    require_any(html, ['xlink:href', '.attr(\'href\'', '.attr("href"', 'href="https://linkeddata.uriburner.com/describe/?url='], "Resolver href missing", failures)
    require_any(html, ['data-resolver-href', 'describe/?url=', 'RESOLVER'], "KG resolver href audit/pattern missing", failures)

    require_any(html, ['id="sparql-explorer"', 'sparql-explore-box', 'Explore Knowledge Graph'], "Footer SPARQL explorer missing", failures)
    require_any(html, ['id="sparqlGraph"', 'SPARQL_GRAPH', 'Named graph'], "Footer named graph selector/IRI missing", failures)
    require_any(html, ['id="sparqlRecipe"', 'exploreQueries', 'liveQueries', 'Query recipe'], "Footer query recipe selector/quick links missing", failures)
    require_any(html, ['id="sparqlText"', '<textarea', 'liveQueries', 'exploreQueries'], "Footer editable SPARQL textarea or query recipes missing", failures)
    require_any(html, ['id="sparqlFormat"', 'text/x-html+tr', 'text%2Fx-html%2Btr'], "Footer SPARQL format display/guidance missing", failures)
    require(html, 'text/x-html+tr', "SELECT result format guidance missing", failures)
    require(html, 'text/x-html-nice-turtle', "DESCRIBE/CONSTRUCT result format guidance missing", failures)
    require(html, 'encodeURIComponent', "SPARQL live link encoding missing", failures)

    for label in [
        "Source material",
        "Companion files",
        "Skills used",
        "Generation environment",
        "Linked Data runtime",
        "Named graphs",
        "Resolver pattern",
        "Extraction provenance",
    ]:
        require(html, label, f"Attribution item missing: {label}", failures)

    require(html, "https://linkeddata.uriburner.com/describe/?url=", "URIBurner resolver pattern missing", failures)
    require(html, "https://linkeddata.uriburner.com/sparql", "URIBurner SPARQL endpoint missing", failures)
    require(html, "https://virtuoso.openlinksw.com/", "OpenLink Virtuoso attribution missing", failures)

    anchors = [
        (m.group(0), m.group(1))
        for m in re.finditer(r'<a\s+[^>]*href="([^"]+)"[^>]*>', html)
    ]
    bad_external = [
        tag for tag, href in anchors if not href.startswith("#") and 'target="_blank"' not in tag
    ]
    bad_fragment = [
        tag for tag, href in anchors if href.startswith("#") and 'target="_blank"' in tag
    ]
    if bad_external:
        fail(f"{len(bad_external)} non-fragment links missing target=\"_blank\"", failures)
    if bad_fragment:
        fail(f"{len(bad_fragment)} fragment links incorrectly open in new tab", failures)

    kg_payload = re.search(r"const kgData = (\{.*?\});\s*\(\(\)=>", html, re.S)
    if kg_payload:
        import json

        data = json.loads(kg_payload.group(1))
        ids = {node["id"] for node in data.get("nodes", [])}
        orphans = [
            link for link in data.get("links", [])
            if link.get("source") not in ids or link.get("target") not in ids
        ]
        if orphans:
            fail(f"KG payload has {len(orphans)} orphan links", failures)
    else:
        fail("Embedded kgData payload missing", failures)

    validate_rdf(args.ttl, "turtle", failures)
    validate_rdf(args.jsonld, "json-ld", failures)

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("PASS: RDF infographic harness contract checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
