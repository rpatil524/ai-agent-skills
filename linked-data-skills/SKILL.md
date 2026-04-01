---
name: linked-data-skills
title: Linked Data Skills
description: Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. Covers the full pipeline from database object scope establishment (local or DSN-attached) through discovery, hostname resolution, IRI pattern confirmation, TBox/ABox generation, atomic load and rewrite rule application, and post-load verification and audit.
version: 2.6.0
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

# Linked Data Skills — Specification (v2.6.0)

## Skill Identity

| Field | Value |
|-------|-------|
| **Name** | linked-data-skills |
| **Version** | 2.6.0 |
| **Purpose** | Generate and manage RDF Views, Knowledge Graphs, and Linked Data from relational database tables using Virtuoso stored procedures. |
| **Scope** | Full KG generation pipeline: database object scope establishment → pre-flight → discovery and table selection → hostname resolution → IRI pattern confirmation → TBox/ABox generation → atomic load + rewrite rule application → post-load verification and audit. |

---

## Tools Reference

| Tool | Role | Workflow Phase |
|------|------|----------------|
| `OAI.DBA.sparql_list_entity_types` | Discover entity types (tables/views) in scope | Discovery |
| `OAI.DBA.sparql_list_entity_types_detailed` | Detailed entity type discovery with column metadata | Discovery |
| `OAI.DBA.sparql_list_entity_types_samples` | Sample data from discovered entity types | Discovery |
| `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES` | Generate TBox ontology (OWL/Turtle) from selected tables | Generation |
| `OAI.DBA.R2RML_FROM_TABLES` | Generate R2RML mappings and IRI templates from selected tables | Generation |
| `OAI.DBA.RDFVIEW_FROM_TABLES` | Generate RDF View script from selected tables | Generation |
| `OAI.DBA.R2RML_GENERATE_RDFVIEW` | Generate RDF View from R2RML mappings | Generation |
| `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES` | Generate ABox data rules (instance/fact mappings) | Generation |
| `OAI.DBA.RDF_AUDIT_METADATA` | Audit RDF metadata integrity — pre-flight and post-load | Pre-flight / Verify |
| `OAI.DBA.RDF_BACKUP_METADATA` | Snapshot RDF metadata before load | Pre-load |
| `OAI.DBA.EXECUTE_SQL_SCRIPT` | Execute SQL/Virtuoso scripts — hostname query, DSN attachment, load TBox (`DB.DBA.TTLP()`), load ABox, apply rewrite rules | Multiple |
| `OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE` | Synchronize RDF View to physical quad store | Load + Apply |
| `OAI.DBA.RDFVIEW_DROP_SCRIPT` | Drop/clean up existing RDF View scripts — collision resolution and rollback | Maintenance |
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

```
Phase 1 — Pre-flight
  Step 0 · Database Object Scope       ← Path A (DSN) or Path B (Local)
  Step 1 · Metadata Audit

Phase 2 — Discovery + IRI Pattern Establishment
  Step 2 · Discovery and Table Selection  ← hard gate: user selects tables
  Step 3 · Hostname Resolution
  Step 4 · IRI Pattern Confirmation       ← hard gate: TBox + ABox, collision-checked

Phase 3 — Generation  [nothing is loaded during this phase]
  Step 5 · TBox Generation
  Step 6 · ABox Generation

Phase 4 — Load + Apply  [atomic — all or nothing]
  Step 7  · Pre-load Backup
  Step 8  · Load TBox
  Step 9  · Load ABox
  Step 10 · Apply Rewrite Rules           ← script validated before execution
  Step 11 · Sync to Physical Store

Phase 5 — Verify
  Step 12 · Post-load Verification
  Step 13 · Audit
  Step 14 · Entity Sampling — Linked Data Compliance Proof
```

---

### Step 0 — Database Object Scope

The first question in every session is whether the target database objects are **external** (requiring DSN attachment) or **local** (already resident in the Virtuoso instance). Either way, all objects are subsequently addressed on a `database.schema.object` basis.

Ask the user:

> "Are the target database objects **local** to this Virtuoso instance, or do they reside in an **external database** that needs to be attached via a DSN?"

**Do not attempt to infer the answer from keywords alone.** A prompt such as `"postgres database objects"` names a database but does not unambiguously establish whether it is local or external — ask if not explicit.

The prompt may already answer the question unambiguously:
- `"using DSN X"` / `"connect to DSN X"` / `"attach via DSN"` → **Path A**
- `"local tables"` / `"already attached"` / `"in this instance"` → **Path B**

#### Path A — External Database (DSN Attachment)

1. Ask for the DSN name if not already provided.
2. Attach the external database to the Virtuoso instance via `EXECUTE_SQL_SCRIPT` using the appropriate `VDB_*` attachment procedure.
3. Confirm attachment succeeded — the external database's objects must be enumerable as `database.schema.object` before proceeding.

#### Path B — Local Database

Objects are already resident in the Virtuoso instance and addressable as `database.schema.object`. Proceed directly to Step 1.

---

### Step 1 — Metadata Audit

Call `RDF_AUDIT_METADATA` to check for inconsistencies or dirty state in the current RDF metadata. Report the result to the user and offer:
- Proceed anyway
- Clean up first (user-directed)
- Abort

Do not proceed to Step 2 until the user has accepted the state.

---

### Step 2 — Discovery and Table Selection (Hard Gate)

#### 2a — Enumerate Database Objects

Call `sparql_list_entity_types` and `sparql_list_entity_types_detailed` against the established scope. Present all discovered objects as a numbered list in fully qualified three-part form:

```
#   Object
──  ──────────────────────────────────
1   database.schema.table_name_1
2   database.schema.table_name_2
3   database.schema.view_name_1
…
```

Include object type (table / view) where available.

#### 2b — User Table Selection (Hard Gate)

**Halt and wait for the user to select which objects to include.**

> "Please select the tables and views to include in the Knowledge Graph. You can specify by number, name, or range (e.g., 1, 3, 5–8, all)."

Record the selected set of `database.schema.object` identifiers as the **working set**. Only the working set proceeds to Steps 3 onward. Do not proceed until the user has made an explicit selection.

---

### Step 3 — Hostname Resolution

Now that the working set of database objects is established, resolve the concrete hostname of the Virtuoso instance. Execute via `Demo.demo.execute_spasql_query`:

```sql
SELECT cfg_item_value(virtuoso_ini_path(), 'URIQA', 'DefaultHost')
```

Store the returned value as `{host}` for all subsequent steps. If the query returns null or empty, ask the user to provide the hostname explicitly.

**No IRI pattern, script, or rewrite rule generated in any subsequent step may contain an unresolved `{host}`, `^{URIQADefaultHost}^`, or `{base-iri}` token.**

---

### Step 4 — IRI Pattern Confirmation (Hard Gate)

**This is a mandatory confirmation gate. The workflow cannot advance without explicit user approval.**

Using the working set from Step 2b and the hostname from Step 3, generate the default IRI patterns for both TBox and ABox.

#### 4a — Collision Check

Before presenting defaults to the user, verify they are conflict-free:

1. **Quad map collision** — Run **UQ1** and check whether any proposed quad map IRI already exists. If a collision is found, offer: drop / rename / abort.
2. **Rewrite rule collision** — Check whether any proposed IRI namespace is already registered in the URL rewrite rule set. If a collision is found, offer: drop / rename / abort.
3. **Ontology graph collision** — Call `sparql_list_ontologies` and check whether the proposed TBox named graph IRI already exists. If a collision is found, offer: drop / rename / abort.

Resolve all collisions before presenting defaults to the user. Do not present patterns that are still in conflict.

#### 4b — TBox Namespace Confirmation

Present the proposed ontology namespace IRI:

| Item | Proposed IRI |
|------|-------------|
| Ontology named graph | `https://{host}/schemas/{qualifier}/` |
| Example class IRI | `https://{host}/schemas/{qualifier}#TableName` |
| Example property IRI | `https://{host}/schemas/{qualifier}#columnName` |

Ask the user to confirm or override.

#### 4c — ABox IRI Template Confirmation

Present the proposed subject IRI templates for each selected table, with `{host}` already substituted:

| Entity / Table | Subject IRI Template | Example IRI |
|----------------|----------------------|-------------|
| `database.schema.TableA` | `https://{host}/{qualifier}/TableA/{PK}#this` | `https://example.com/hr/Employees/1#this` |
| `database.schema.TableB` | `https://{host}/{qualifier}/TableB/{PK}#this` | `https://example.com/hr/Departments/10#this` |
| … | … | … |

Ask the user to confirm or override. Accept partial overrides — only modified rows change; the rest proceed as proposed.

Record all confirmed TBox and ABox patterns as the canonical IRI scheme for all subsequent steps.

---

### Step 5 — TBox Generation

Call `RDFVIEW_ONTOLOGY_FROM_TABLES` against the working set using the confirmed TBox namespace from Step 4b to generate the ontology (OWL classes, datatype properties, object properties) in Turtle or RDF/XML.

**Retain the generated ontology document in full.** It will be loaded in Step 8 — do not load it here.

---

### Step 6 — ABox Generation

Using the confirmed ABox IRI templates from Step 4c and the working set from Step 2b:

1. Call `RDFVIEW_FROM_TABLES` (or `R2RML_GENERATE_RDFVIEW` when working from R2RML mappings) to produce the RDF View script.
2. Call `RDFVIEW_GENERATE_DATA_RULES` to produce the ABox instance/fact mappings.

**Retain both artifacts in full.** Neither is loaded here — loading happens in Phase 4.

Present the generated scripts to the user for review before proceeding.

---

### Step 7 — Pre-load Backup

Call `RDF_BACKUP_METADATA` to take a snapshot of the current RDF metadata state. This provides a restore point if Phase 4 fails partway through.

Confirm the backup completed successfully before proceeding to Step 8.

---

### Step 8 — Load TBox

Load the ontology generated in Step 5 into the Virtuoso quad store using `EXECUTE_SQL_SCRIPT` with `DB.DBA.TTLP()` into the confirmed ontology named graph:

```sql
DB.DBA.TTLP('<ontology-turtle>', '', 'https://{host}/schemas/{qualifier}/', 0);
```

**This is the start of the atomic Load + Apply sequence.** If this step fails, do not proceed — report the error and offer rollback.

---

### Step 9 — Load ABox

Apply the RDF View script and ABox data rules generated in Step 6 via `EXECUTE_SQL_SCRIPT`.

If this step fails, execute rollback:
1. Drop the ontology graph loaded in Step 8
2. Call `RDFVIEW_DROP_SCRIPT` to remove any partially applied view script
3. Report the error and rollback outcome to the user

---

### Step 10 — Apply Rewrite Rules

Generate URL rewrite rules for both namespaces using the confirmed IRIs from Step 4:

- **TBox rewrite rules** — map ontology IRIs (e.g., `https://{host}/schemas/{qualifier}#ClassName`) to the ontology document loaded in Step 8
- **ABox rewrite rules** — map instance IRIs (e.g., `https://{host}/{qualifier}/TableA/{PK}#this`) to a SPARQL DESCRIBE endpoint so each IRI dereferences to its RDF description

#### Script Validation (mandatory before execution)

Before passing the generated script to `EXECUTE_SQL_SCRIPT`, verify:

1. **No unresolved placeholders** — no remaining `{host}`, `{base-iri}`, `^{URIQADefaultHost}^`, or `{...}` tokens. All must be substituted with the concrete values from Steps 3 and 4.
2. **No empty or NULL arguments** — no empty string `''` or back-to-back commas `, ,` where a value is expected.
3. **All parameters present** — every `DB.DBA.URLREWRITE_CREATE_RULELIST` and `DB.DBA.VHOST_DEFINE` call has all required non-null parameters filled.

Only execute the script after it passes all three checks. If any check cannot be resolved automatically, present the problematic lines to the user for manual correction before proceeding.

If execution fails despite validation, execute the same rollback as Step 9 and additionally remove any partially registered rewrite rules.

---

### Step 11 — Sync to Physical Store

Call `RDFVIEW_SYNC_TO_PHYSICAL_STORE` to materialize the RDF View into the physical quad store.

Successful completion of this step closes the atomic Load + Apply sequence.

---

### Step 12 — Post-load Verification

Run the following in sequence and confirm each:

1. `sparql_list_ontologies` — confirm the TBox ontology IRI from Step 4b is present
2. **UQ1** — confirm the new quad map IRI appears and no unintended maps were created

Report any discrepancies to the user before proceeding.

---

### Step 13 — Audit

Call `RDF_AUDIT_METADATA` to verify integrity of the fully loaded state.

Report a summary to the user:
- Named graph IRI
- Triple count
- Ontology IRI
- Active rewrite rules (TBox + ABox)
- Any warnings from the audit

---

### Step 14 — Entity Sampling: Linked Data Compliance Proof

Execute the following query via `Demo.demo.execute_spasql_query` to retrieve an aggregated sample of entities grouped by entity type from the generated KG:

```sparql
SPARQL
SELECT ?type
  (SAMPLE(?entity) AS ?sampleEntity)
  (CONCAT('https://{host}/describe/?uri=', STR(SAMPLE(?entity))) AS ?sampleEntityDescUrl)
  (COUNT(?entity) AS ?entityCount)
FROM <https://{host}/{qualifier}#>
WHERE {
  ?entity a ?type .
  FILTER (STRSTARTS(STR(?type), 'https://{host}/schemas/{qualifier}'))
}
GROUP BY ?type
ORDER BY DESC(?entityCount)
```

Substitute `{host}` and `{qualifier}` with the concrete values established in Steps 3 and 4.

#### Presentation Requirements

Present results as a formatted table. **Every IRI in the result set must be rendered as a hyperlink using its dereferenceable form:**

| Entity Type | Sample Entity | Description URL | Entity Count |
|-------------|---------------|-----------------|--------------|
| [`https://{host}/schemas/{qualifier}#TableA`](https://{host}/describe/?uri=https://{host}/schemas/{qualifier}#TableA) | [`https://{host}/{qualifier}/TableA/1#this`](https://{host}/{qualifier}/TableA/1#this) | [`describe`](https://{host}/describe/?uri=https://{host}/{qualifier}/TableA/1#this) | 42 |
| … | … | … | … |

- **Entity Type** — hyperlinked to the TBox IRI (dereferences via TBox rewrite rules to the ontology document)
- **Sample Entity** — hyperlinked directly to the ABox IRI (dereferences via ABox rewrite rules to the entity's RDF description)
- **Description URL** — hyperlinked to the `/describe/?uri=` endpoint for explicit Linked Data navigation
- **Entity Count** — total instances of that type in the graph

#### Purpose

This step constitutes proof of:
1. **KG generation** — triples are present and queryable via SPARQL
2. **TBox compliance** — entity types resolve to ontology class definitions
3. **ABox compliance** — entity IRIs dereference to their RDF descriptions
4. **Linked Data principles** — all minted IRIs are dereferenceable and hyperlinked

If any IRI in the result set fails to dereference, report it as a Linked Data compliance gap and investigate the corresponding rewrite rule registration from Step 10.

---

## Hard Gate Summary

| Gate | Step | Condition to advance |
|------|------|----------------------|
| Database Object Scope | 0 | Path A (DSN attached and objects addressable as `database.schema.object`) or Path B (local, directly addressable) — explicitly confirmed, not inferred |
| Metadata Audit | 1 | User has accepted current metadata state |
| Table Selection | 2b | User has explicitly selected the working set of `database.schema.object` identifiers |
| Hostname Resolution | 3 | Concrete hostname resolved — no unresolved `{host}` placeholders in any subsequent artifact |
| Collision Checks | 4a | All quad map, rewrite rule, and ontology graph conflicts resolved |
| TBox IRI Confirmation | 4b | User has confirmed or overridden the ontology namespace IRI |
| ABox IRI Confirmation | 4c | User has confirmed or overridden all subject IRI templates |
| Pre-load Backup | 7 | Backup confirmed before any loading begins |
| Load + Apply atomic boundary | 8–11 | All four steps succeed; any failure triggers full rollback |
| Rewrite Script Validation | 10 | No unresolved placeholders or empty arguments before execution |
| Post-load Verification | 12 | Ontology IRI and quad map IRI confirmed present after load |
| Entity Sampling | 14 | All entity type and entity IRIs in results are dereferenceable and hyperlinked |

---

## Utility Queries

### UQ1 — List Existing Quad Maps

**Use at:** Step 4a (collision detection) and Step 12 (post-load verification).

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

1. **Database object scope is always the first question.** Never call any discovery or generation tool before Step 0 is resolved — explicitly answered by the user, not inferred from keywords.
2. **External objects must be attached first.** Path A (DSN) requires confirmed attachment and `database.schema.object` addressability before Step 1.
3. **All objects use three-part naming.** Every database object is identified as `database.schema.object_name` throughout the workflow — in discovery lists, generation calls, and user-facing output.
4. **Table selection is a hard gate.** Step 2b must produce an explicit user-confirmed working set before any subsequent step proceeds. Do not assume "all tables" unless the user explicitly states it.
5. **Metadata audit before discovery.** Step 1 must complete before entering Phase 2.
6. **Hostname after working set is established.** Resolve `{host}` at Step 3 — only after the working set from Step 2b is confirmed. Never resolve hostname before table selection.
7. **Collision checks before IRI confirmation.** Step 4a must clear all conflicts before TBox (4b) and ABox (4c) patterns are presented to the user.
8. **Generation produces, does not load.** No tool call during Phase 3 (Steps 5–6) may write to the quad store.
9. **Load + Apply is atomic.** Any failure in Steps 8–11 triggers full rollback — drop the ontology graph, call `RDFVIEW_DROP_SCRIPT`, remove partial rewrite rules.
10. **No unresolved placeholders ever.** No script, IRI template, or rewrite rule executed at any step may contain `{host}`, `^{URIQADefaultHost}^`, `{base-iri}`, or any `{...}` token. All must be substituted with concrete values before execution.
11. **Validate rewrite scripts before execution.** Scan every generated rewrite/vhost script for empty arguments and unresolved placeholders before passing to `EXECUTE_SQL_SCRIPT`. Never execute a script that fails validation.
12. **Rewrite rules are not optional.** Linked Data without dereferenceable IRIs is incomplete. Both TBox and ABox rewrite rules must be applied as part of the atomic sequence.
13. **Entity sampling is mandatory.** Step 14 must be executed and its results presented as a hyperlinked table. A KG session is not complete until Linked Data compliance across TBox and ABox is demonstrated.
14. **All result IRIs must be hyperlinked.** In Step 14 output, every entity type IRI and entity IRI must be rendered as a clickable hyperlink using its dereferenceable form. Plain-text IRIs in the final report are not acceptable.
15. **Partial IRI overrides are valid.** A user who changes two out of ten ABox templates has confirmed the other eight implicitly.
16. **Scope re-use.** If the working set and path (A or B) are already established earlier in the session, do not re-ask in Step 0.
17. **Tool fallback.** If a primary tool call fails, report the error clearly before attempting `chatPromptComplete` as a fallback. Do not silently substitute.

---

## Preferences

| Setting | Value |
|---------|-------|
| **Style** | Precise and professional |
| **Object naming** | Always fully qualified as `database.schema.object_name` |
| **Confirmation prompts** | Formatted tables with example IRIs — all using concrete hostname |
| **Error reporting** | Explicit — name the tool, the error, and the step |
| **Response scope** | Strictly scoped to the KG/Linked Data generation pipeline and the tools listed above |
