---
name: linked-data-skills
title: Linked Data Skills
description: Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. Covers the full pipeline from scope detection and pre-flight checks through TBox/ABox generation, atomic load and rewrite rule application, and post-load verification and audit.
version: 2.2.0
type: skill
created: 2026-03-26T18:30:49.078Z
updated: 2026-04-01T00:00:00.000Z
tools:
  - OAI.DBA.chatPromptComplete
  - OAI.DBA.sparql_list_entity_types_detailed
  - OAI.DBA.EXECUTE_SQL_SCRIPT
  - DB.DBA.graphqlQuery
  - DB.DBA.graphqlEndpointQuery
  - OAI.DBA.sparql_list_ontologies
  - OAI.DBA.sparql_list_entity_types
  - OAI.DBA.sparql_list_entity_types_samples
  - OAI.DBA.R2RML_FROM_TABLES
  - OAI.DBA.R2RML_GENERATE_RDFVIEW
  - OAI.DBA.RDF_BACKUP_METADATA
  - OAI.DBA.RDF_AUDIT_METADATA
  - OAI.DBA.SPONGE_URL
  - OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES
  - OAI.DBA.RDFVIEW_DROP_SCRIPT
  - OAI.DBA.RDFVIEW_FROM_TABLES
  - OAI.DBA.RDFVIEW_GENERATE_DATA_RULES
  - OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE
  - OAI.DBA.sparqlRemoteQuery
  - OAI.DBA.getAssistantConfiguration
  - Demo.demo.execute_spasql_query
  - OAI.DBA.getSkillResource
---

# Linked Data Skills — Specification (v2.2.0)

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | linked-data-skills |
| **Version** | 2.2.0 |
| **Purpose** | Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. |
| **Scope** | Full KG generation pipeline: scope detection → pre-flight checks → TBox/ABox generation → atomic load + rewrite rule application → post-load verification and audit. |

---

## Tools Reference

| Tool | Role | Workflow Phase |
|------|------|----------------|
| `OAI.DBA.sparql_list_entity_types` | Discover entity types (tables/views) in scope | Generation |
| `OAI.DBA.sparql_list_entity_types_detailed` | Detailed entity type discovery with column metadata | Generation |
| `OAI.DBA.sparql_list_entity_types_samples` | Sample data from discovered entity types | Generation |
| `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` | Generate TBox ontology (OWL/Turtle) from relational tables | Generation |
| `OAI.DBA.R2RML_FROM_TABLES` | Generate R2RML mappings and IRI templates from tables | Generation |
| `OAI.DBA.RDFVIEW_FROM_TABLES` | Generate RDF View script from tables | Generation |
| `OAI.DBA.R2RML_GENERATE_RDFVIEW` | Generate RDF View from R2RML mappings | Generation |
| `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` | Generate ABox data rules (instance/fact mappings) | Generation |
| `OAI.DBA.RDF_AUDIT_METADATA` | Audit RDF metadata integrity — pre-flight and post-load | Pre-flight / Verify |
| `OAI.DBA.RDF_BACKUP_METADATA` | Snapshot RDF metadata before load | Pre-load |
| `OAI.DBA.EXECUTE_SQL_SCRIPT` | Execute SQL/Virtuoso scripts — load TBox (`DB.DBA.TTLP()`), load ABox, apply rewrite rules | Load + Apply |
| `OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE` | Synchronize RDF View to physical quad store | Load + Apply |
| `OAI.DBA.RDFVIEW_DROP_SCRIPT` | Drop/clean up existing RDF View scripts — used in collision resolution and rollback | Maintenance |
| `OAI.DBA.sparql_list_ontologies` | Verify loaded ontologies in the quad store | Verify |
| `OAI.DBA.sparqlRemoteQuery` | Execute SPARQL against remote endpoints | Query / Verify |
| `Demo.demo.execute_spasql_query` | Execute SPASQL (SQL + SPARQL hybrid) queries | Query / Verify |
| `DB.DBA.graphqlQuery` | Execute GraphQL queries against Virtuoso | Query / Verify |
| `DB.DBA.graphqlEndpointQuery` | Execute GraphQL against a specific endpoint | Query / Verify |
| `OAI.DBA.SPONGE_URL` | Fetch and ingest external URLs into the quad store | Data ingestion |
| `OAI.DBA.chatPromptComplete` | LLM-mediated fallback for complex reasoning tasks | Fallback |
| `OAI.DBA.getAssistantConfiguration` | Retrieve assistant/session configuration | Session |
| `OAI.DBA.getSkillResource` | Retrieve skill resource files | Session |

---

## Session Workflow

The pipeline is divided into four phases. Generation produces all artifacts without loading anything. Load + Apply is an atomic sequence — if any step fails, the entire phase rolls back. Verify and Audit confirm the outcome.

```
Phase 1 — Pre-flight
  Step 0 · Scope Detection Gate
  Step 1 · Pre-flight Checks (metadata audit + collision detection)

Phase 2 — Generation  [nothing is loaded during this phase]
  Step 2 · Discovery
  Step 3 · TBox Generation
  Step 4 · IRI Template Confirmation       ← hard gate
  Step 5 · ABox Generation

Phase 3 — Load + Apply  [atomic — all or nothing]
  Step 6 · Pre-load Backup
  Step 7 · Load TBox
  Step 8 · Load ABox
  Step 9 · Apply Rewrite Rules
  Step 10 · Sync to Physical Store

Phase 4 — Verify
  Step 11 · Post-load Verification
  Step 12 · Audit
```

---

### Step 0 — Scope Detection Gate

**Before any other work begins**, determine whether the starting scope is established.

**Scope is considered established if the user prompt contains any of:**
- A named database qualifier (e.g., `"using qualifier Northwind"`, `"from database HR"`)
- A named DSN (e.g., `"using DSN sales_db"`, `"connect to MyDSN"`)
- A specific table reference (e.g., `"from table Demo.demo.Orders"`)
- A named graph or IRI base already active in the session
- Prior session context in which tables or a database have already been identified

**If scope is established:** proceed to Step 1.

**If scope is NOT established:** ask the user:

> "To begin generating the Knowledge Graph, I need to know the starting point:
> - Are we working with database tables **already attached to this session**? If so, which qualifier or schema should I use?
> - Or do you need to **attach a new data source via a DSN**? If so, please provide the DSN name and connection details."

Do not proceed until scope is resolved to either an existing qualifier/schema or a confirmed DSN attachment.

---

### Step 1 — Pre-flight Checks

Run all three checks before any generation work begins. Present a consolidated report to the user and require a decision before continuing.

#### 1a — Metadata Audit

Call `RDF_AUDIT_METADATA`. If the audit reports inconsistencies or dirty state, inform the user and offer:
- Proceed anyway
- Clean up first (user-directed)
- Abort

#### 1b — Quad Map Collision Detection

Run **UQ1** (see Utility Queries) to list all existing quad maps. Compare against the intended quad map IRI for this session. If a collision is found:

> "A quad map with IRI `<{proposed-qm-iri}>` already exists. Choose an action:
> 1. **Drop it** — `SPARQL DROP QUAD MAP <{proposed-qm-iri}>` will be executed before proceeding
> 2. **Rename** — provide a new IRI for the quad map to be created
> 3. **Abort** — stop here"

Execute the chosen action and confirm resolution (re-run UQ1) before continuing.

#### 1c — Ontology Graph Collision Detection

Call `sparql_list_ontologies`. If an ontology graph matching the intended `{base-iri}/ontology` IRI already exists, inform the user and offer the same three options (drop / rename / abort).

**Do not proceed to Step 2 until all three checks pass or the user has explicitly accepted the state.**

---

### Step 2 — Discovery

Call `sparql_list_entity_types` and `sparql_list_entity_types_detailed` to enumerate tables and views within the established scope. Use `sparql_list_entity_types_samples` to retrieve representative row samples where needed to inform IRI template decisions.

Present a summary of discovered entities to the user before proceeding.

---

### Step 3 — TBox Generation

Call `RDFVIEW_ONTOLOGY_FROM_TABLES` against the discovered tables to generate the TBox ontology (OWL classes, datatype properties, object properties) in Turtle or RDF/XML.

**Retain the generated ontology document in full.** It will be loaded in Step 7 — do not load it here.

---

### Step 4 — IRI Template Confirmation (Hard Gate)

**This is a mandatory confirmation gate. The workflow cannot advance without explicit user approval.**

From the R2RML mappings produced by `R2RML_FROM_TABLES`, extract and present the proposed IRI templates as a formatted table:

| Entity / Table | Subject IRI Template | Example IRI |
|----------------|----------------------|-------------|
| `Demo.demo.Orders` | `{base-iri}/Orders/{OrderID}` | `https://example.org/Orders/1001` |
| `Demo.demo.Customers` | `{base-iri}/Customers/{CustomerID}` | `https://example.org/Customers/ALFKI` |
| … | … | … |

Then ask:

> "These are the proposed IRI templates derived from the table structure. Please confirm:
> 1. **Proceed with these templates as shown**, or
> 2. **Specify overrides** for any row (provide the table name and your preferred template pattern)."

Accept partial overrides — only the rows the user modifies are changed; the rest proceed as proposed. Record the confirmed (and any overridden) templates as the canonical IRI scheme for all subsequent steps.

---

### Step 5 — ABox Generation

Using the confirmed IRI templates from Step 4:

1. Call `RDFVIEW_FROM_TABLES` (or `R2RML_GENERATE_RDFVIEW` when working from R2RML mappings) to produce the RDF View script.
2. Call `RDFVIEW_GENERATE_DATA_RULES` to produce the ABox instance/fact mappings.

**Retain both artifacts in full.** Neither is loaded here — loading happens in Phase 3.

Present the generated scripts to the user for review before proceeding.

---

### Step 6 — Pre-load Backup

Call `RDF_BACKUP_METADATA` to take a snapshot of the current RDF metadata state. This provides a restore point if Phase 3 fails partway through.

Confirm the backup completed successfully before proceeding to Step 7.

---

### Step 7 — Load TBox

Load the ontology generated in Step 3 into the Virtuoso quad store using `EXECUTE_SQL_SCRIPT` with `DB.DBA.TTLP()` into the session-scoped ontology named graph:

```sql
DB.DBA.TTLP('<ontology-turtle>', '', '<{base-iri}/ontology>', 0);
```

**This is the start of the atomic Load + Apply sequence.** If this step fails, do not proceed — report the error and offer rollback.

---

### Step 8 — Load ABox

Apply the RDF View script and ABox data rules generated in Step 5 via `EXECUTE_SQL_SCRIPT`.

If this step fails, execute rollback:
1. Drop the ontology graph loaded in Step 7
2. Call `RDFVIEW_DROP_SCRIPT` to remove any partially applied view script
3. Report the error and the rollback outcome to the user

---

### Step 9 — Apply Rewrite Rules

Generate and apply URL rewrite rules via `EXECUTE_SQL_SCRIPT` covering two namespaces:

- **TBox rewrite rules** — map ontology IRIs (e.g., `{base-iri}/ontology#ClassName`) to the ontology document loaded in Step 7
- **ABox rewrite rules** — map instance IRIs (e.g., `{base-iri}/Orders/{OrderID}`) to a SPARQL DESCRIBE endpoint so each IRI dereferences to its RDF description

If this step fails, execute the same rollback as Step 8 and additionally remove any partially registered rewrite rules.

---

### Step 10 — Sync to Physical Store

Call `RDFVIEW_SYNC_TO_PHYSICAL_STORE` to materialize the RDF View into the physical quad store.

Successful completion of this step closes the atomic Load + Apply sequence.

---

### Step 11 — Post-load Verification

Run the following in sequence and confirm each:

1. `sparql_list_ontologies` — confirm the ontology IRI from Step 3 is present
2. **UQ1** — confirm the new quad map IRI appears and no unintended maps were created

Report any discrepancies to the user before proceeding.

---

### Step 12 — Audit

Call `RDF_AUDIT_METADATA` to verify integrity of the fully loaded state.

Report a summary to the user:
- Named graph IRI
- Triple count
- Ontology IRI
- Active rewrite rules (TBox + ABox)
- Any warnings from the audit

---

## Hard Gate Summary

| Gate | Step | Condition to advance |
|------|------|----------------------|
| Scope Gate | 0 | Database/qualifier/DSN established from prompt or user response |
| Pre-flight | 1 | Metadata audit passed; all collision checks resolved by user decision |
| IRI Template Confirmation | 4 | User has explicitly confirmed or overridden all proposed templates |
| Pre-load Backup | 6 | Backup confirmed before any loading begins |
| Load + Apply atomic boundary | 7–10 | All four steps succeed; any failure triggers full rollback |
| Post-load Verification | 11 | Ontology IRI and quad map IRI confirmed present after load |

---

## Utility Queries

### UQ1 — List Existing Quad Maps

**Use at:** Step 1b (collision detection) and Step 11 (post-load verification).

```sparql
SPARQL
DEFINE input:storage ""

SELECT ?qm
FROM <http://www.openlinksw.com/schemas/virtrdf#>
WHERE {
  [] virtrdf:qsUserMaps ?maps .
  ?maps ?p ?qm .
  ?qm a virtrdf:QuadMap .
}
```

Execute via `Demo.demo.execute_spasql_query`. Present results as a numbered list of quad map IRIs.

**Cleanup:** To drop an existing quad map, execute via `EXECUTE_SQL_SCRIPT`:

```sql
SPARQL DROP QUAD MAP <{quad-map-iri}>;
```

Confirm the map no longer appears in a subsequent UQ1 run before proceeding.

---

## Operational Rules

1. **Scope first.** Never call any discovery or generation tool before Step 0 scope is resolved.
2. **Pre-flight is mandatory.** Steps 1a, 1b, and 1c must all be executed and resolved before entering Phase 2.
3. **Generation produces, does not load.** No tool call during Phase 2 (Steps 2–5) may write to the quad store.
4. **Load + Apply is atomic.** Any failure in Steps 7–10 triggers full rollback — drop the ontology graph, call `RDFVIEW_DROP_SCRIPT`, remove partial rewrite rules.
5. **No silent defaults.** Do not assume an IRI base, qualifier, or template — always surface proposed values and wait for confirmation at designated gates.
6. **Rewrite rules are not optional.** Linked Data without dereferenceable IRIs is incomplete. Both TBox and ABox rewrite rules must be applied as part of the atomic sequence.
7. **Partial IRI overrides are valid.** A user who changes two out of ten templates has confirmed the other eight implicitly.
8. **Scope re-use.** If database/qualifier is already established in the session, do not re-ask in Step 0.
9. **Tool fallback.** If a primary tool call fails, report the error clearly before attempting `chatPromptComplete` as a fallback. Do not silently substitute.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Precise and professional |
| **Confirmation prompts** | Formatted tables with example IRIs |
| **Error reporting** | Explicit — name the tool, the error, and the step |
| **Response scope** | Strictly scoped to the KG/Linked Data generation pipeline and the tools listed above |
