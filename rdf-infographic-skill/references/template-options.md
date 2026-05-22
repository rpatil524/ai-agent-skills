# RDF Infographic Template Options

Use templates as visual and interaction references, not as hard dependencies. The strict harness contract defines required behavior; templates are selectable shells that must be adapted to pass validation.

## Selection Rule

- If the user names or supplies a template, use that as the visual reference and retrofit the contract features into it.
- If the user asks for the "usual" collection and gives no preference, infer the best template from the source content, audience, and nearby prior artifacts.
- If an existing artifact is being repaired, preserve its visual language unless the user asks for a redesign.
- If a helper script is convenient, use it; if the template calls for a different implementation, implement directly and run the validator.

## Available References

### Harness Reference

Asset: `scripts/rdf_infographic_harness.py`

Best for:

- New article collections where consistency matters more than a bespoke layout.
- Cases where previous KG Explorer regressions are the main risk.
- Fast generation using known IDs and validation-friendly controls.

Characteristics:

- Floating compact navigation.
- Single KG Explorer SVG with controls tray closed by default.
- Advanced-only settings panel.
- Footer SPARQL workbench with named graph and query recipe selectors.
- Full attribution card set.

### Claude Sonnet 4 Gartner Dashboard

Asset: `assets/templates/gartner-da-london-2026-claude-sonnet4-dashboard.html`

Best for:

- Dense conference reports, field notes, strategy analysis, or operational dashboards.
- Documents with many sections, metrics, tables, chips, archetypes, and quick SPARQL recipes.
- User preference for a compact top navigation bar and work-focused dashboard feel.

Characteristics worth preserving:

- Fixed top horizontal navigation with compact menu expansion.
- Dense metric/stat pills and dashboard cards.
- Top-level theme button.
- Two-pane Basic/Advanced KG Explorer pattern.
- Advanced settings drawer rather than large card controls.
- Footer quick-explore SPARQL links.

Required adaptations before reuse:

- Keep navigation collapsed by default and include the required page-level theme control.
- Ensure KG controls are closed by default. If using a two-pane Basic/Advanced layout, Advanced settings must still be hidden until Advanced mode and Settings are explicitly selected.
- Build KG data from companion RDF, not hand-authored subsets unless the RDF itself is the source of those subsets.
- Make SVG node labels and edge labels resolver-backed anchors using RDF IRIs.
- Use sticky node drag with double-click unpin.
- Replace `format=text/html` SPARQL links with query-type-specific formats: `text/x-html+tr` for SELECT and `text/x-html-nice-turtle` for DESCRIBE/CONSTRUCT.
- Add or preserve full attribution: source material, companion files, skills, generation environment, Linked Data runtime, named graph IRIs, resolver pattern, and extraction provenance.
- Ensure every non-fragment HTML link opens in a new tab with `target="_blank" rel="noopener noreferrer"`.

### Semantic Medallion Editorial Technical Template

Asset: `assets/templates/semantic-medallion-editorial-technical.html`

Best for:

- Technical explainers, architecture patterns, ontology/SPARQL tutorials, and documentation-style artifacts.
- Articles where the main story is a layered architecture, implementation path, vocabulary mapping, or executable query examples.
- Outputs that need a polished editorial feel with dense technical sections rather than a dashboard/briefing feel.

Characteristics worth preserving:

- Compact movable/resizable navigation panel that starts as a small header control.
- Separate page-level theme button.
- Narrow reading column with technical cards, architecture layers, capability cards, FAQ, glossary, and downloads.
- Strong medallion/layer visual language suitable for Bronze/Silver/Gold/Platinum or other staged architectures.
- SPARQL query accordions with syntax-styled query blocks and live-run buttons.
- Single-canvas D3 KG Explorer with legend and toolbar.
- Footer with source, companion artifact, skill, resolver, and server/platform references.

Required adaptations before reuse:

- Keep or retrofit POSH links for the companion HTML/MD/RDF set, including Markdown parity when a Markdown output is requested.
- Ensure every external link has `target="_blank" rel="noopener noreferrer"`; this template has some same-folder artifact links and source links that may need updating.
- Replace static or hand-authored KG nodes/links with graph data derived from the companion RDF, unless the static subset is programmatically derived from that RDF.
- Make KG node labels and edge labels resolver-backed anchors using RDF IRIs, not just click handlers or plain text.
- Keep controls closed by default; if the toolbar is visible, wrap it in a compact Controls tray or otherwise preserve the first visible KG state required by the contract.
- Scope settings to Advanced mode if settings are present.
- Add predicate Select All/Deselect All when predicate filtering is available.
- Preserve sticky drag and double-click unpin.
- Replace `format=text/html` SPARQL links with query-type-specific formats: `text/x-html+tr` for SELECT and `text/x-html-nice-turtle` for DESCRIBE/CONSTRUCT.
- If the footer uses a single quick SPARQL link, upgrade it to either the full workbench or an equivalent set of quick links plus editable/query recipe capability, depending on user preference.
- Include named graph IRIs and extraction/generation provenance in the attribution block.

## Validation

Run:

```bash
python3 scripts/validate-harness-contract.py path/to/page.html --ttl path/to/page.ttl --jsonld path/to/page.jsonld
```

The validator is a contract gate, not a template selector. A page may use any visual template if it passes the contract checks.
