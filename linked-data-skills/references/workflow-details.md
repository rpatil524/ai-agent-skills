# Linked Data Skills — Workflow Details

Detailed tool call signatures, script templates, and procedures for Steps 3–5.
Load this file via `getSkillResource` at the start of Step 3.

---

## Step 3 — Generate TBox and ABox Views

All three generation tools use `iri_path_segment` as the primary IRI driver.
Nothing is written to the database during this step.

⛔ **Script retention rule:** The full text of each generated script must be held intact for use in Step 4. Never display the full script to the user unless explicitly requested, and never truncate it. Truncation causes Step 4 to fail because the incomplete text cannot be executed.

### 3a — Generate TBox Ontology

**Tool:** `OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES`

```javascript
OAI.DBA.RDFVIEW_ONTOLOGY_FROM_TABLES({
  tables: [
    "{qualifier}.{schema}.{TableA}",
    "{qualifier}.{schema}.{TableB}"
  ],
  iri_path_segment: "{confirmed-iri-path-segment}",
  graphql_annotations: 1
})
```

**Output:** OWL ontology in Turtle format — classes, datatype properties, object properties.
Retain in full. Do not load here.

**After receiving this output, extract and record:**
- `{actual-tbox-namespace}` — from the `@prefix kg_*: <...> .` or `prefix kg_*: <...>` declaration at the top of the Turtle output. Record the full IRI value (including trailing `#` or `/`). This is the canonical TBox namespace; it also serves as the target graph IRI when loading the ontology in Step 4b.

### 3b — Generate ABox RDF View Script

**Tool:** `OAI.DBA.RDFVIEW_FROM_TABLES`

```javascript
OAI.DBA.RDFVIEW_FROM_TABLES({
  tables: [
    "{qualifier}.{schema}.{TableA}",
    "{qualifier}.{schema}.{TableB}"
  ],
  iri_path_segment: "{confirmed-iri-path-segment}",
  generate_void: 1
})
```

**Output:** SQL script defining quad map storage and IRI class templates.
Retain in full. Do not load here.

**After receiving this output, extract and record:**
- `{actual-abox-graph-iri}` — from the first `graph iri("...")` clause in the script; replace `^{URIQADefaultHost}^` with `{protocol}://{host}` and strip the trailing `#`. This is the `FROM` graph IRI to use in Step 5.
- `{actual-tbox-namespace}` — from the `prefix kg_*: <...>` declaration at the top of the script (the prefix ending in `#` or `/`).

### 3c — Generate Linked Data Rewrite Rules

**Tool:** `OAI.DBA.RDFVIEW_GENERATE_DATA_RULES`

```javascript
OAI.DBA.RDFVIEW_GENERATE_DATA_RULES({
  iri_path_segment: "{confirmed-iri-path-segment}",
  include_ontology_rules: 1
})
```

**Output:** SQL script with `DB.DBA.URLREWRITE_CREATE_RULELIST` and `DB.DBA.VHOST_DEFINE`
calls for both TBox and ABox IRIs. Does not take a `tables` parameter — generates rules
for all quad maps created by Step 3b.
Retain in full. Do not load here.

### On Generation Error

Call `OAI.DBA.RDF_AUDIT_METADATA` with `audit_level: 1`:

```javascript
OAI.DBA.RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

Report findings and offer:
- Repair: re-run with `audit_level: 2`
- Abort

---

## Step 4 — Deploy Linked Data via Rewrite Rules

Execute the generated scripts in sequence. All steps must succeed.

### 4a — Script Validation (mandatory before any execution)

Before passing any script to `OAI.DBA.EXECUTE_SQL_SCRIPT`, verify:

1. **No unresolved placeholders** — no `{host}`, `{base-iri}`, or any `{...}` token. **`^{URIQADefaultHost}^` is NOT a placeholder — it is a Virtuoso server-side macro and must remain in the script exactly as generated.**
2. **No empty arguments** — no `''` where a value is expected, no back-to-back commas `, ,`
3. **All parameters present** — every `URLREWRITE_CREATE_RULELIST` and `VHOST_DEFINE` call has all required non-null parameters

Fail loudly if any check fails — present the problematic lines to the user for correction.

### 4b — Load TBox Ontology

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "DB.DBA.TTLP('{ontology-turtle}', '', '{actual-tbox-namespace}', 0);"
})
```

Use `{actual-tbox-namespace}` extracted from the Step 3a output — the full IRI from the `prefix` declaration. Do not substitute a path template here.

### 4c — Execute ABox RDF View Script

**Single-call execution (default):**

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{exact-rdfview-script-from-step-3b}"
})
```

Use the exact text returned by the `RDFVIEW_FROM_TABLES` tool call — do not re-type, reconstruct, or summarize it. Never modify the generated script.

**Batched execution (when the script is large or single-call fails):**

The ABox script is a sequence of SPARQL statements, each terminated by `;\n`. Split on statement boundaries and execute in two phases:

**Phase 1 — IRI class definitions** (all `SPARQL ... create iri class ...;` statements together):

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{all-create-iri-class-statements}"
})
```

**Phase 2 — Quad map definitions** (each `SPARQL ... alter quad storage ...;` block individually, or in groups of N):

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{one-or-more-alter-quad-storage-statements}"
})
```

If any individual batch call fails, report the specific failing statement(s) and continue with the remaining batches — do not abort the entire deployment for a single batch failure. Collect all errors and report them together after all batches have been attempted.

### 4d — Apply Rewrite Rules

```javascript
OAI.DBA.EXECUTE_SQL_SCRIPT({
  sql_script: "{exact-data-rules-script-from-step-3c}"
})
```

Never modify the generated script — execute exactly as returned.

### 4e — Sync to Physical Store

```javascript
OAI.DBA.RDFVIEW_SYNC_TO_PHYSICAL_STORE({})
```

### On Deployment Error

1. Call `OAI.DBA.RDF_AUDIT_METADATA` with `audit_level: 1` to identify integrity issues
2. Report error and audit findings to the user
3. Offer options:
   - **Repair:** re-run audit with `audit_level: 2`
   - **Rollback:** call `OAI.DBA.RDFVIEW_DROP_SCRIPT` for the affected graph IRI, then execute the drop script via `OAI.DBA.EXECUTE_SQL_SCRIPT`
   - **Abort**

To drop a conflicting quad map before rollback:
```sql
SPARQL DROP QUAD MAP <{quad-map-iri}>;
```

### Post-Deployment Sanity Check

After successful completion of 4a–4e:

```javascript
OAI.DBA.RDF_AUDIT_METADATA({
  audit_level: 1,
  format: "json"
})
```

Report result to the user. If issues found, offer `audit_level: 2` repair before proceeding to Step 5.

---

## Step 5 — Verify: Linked Data Compliance

Use the ACTUAL IRIs extracted from the generated scripts at Step 3b — not the Step 2 estimates:

| Variable | Value |
|----------|-------|
| `{actual-abox-graph-iri}` | extracted from `graph iri(...)` in Step 3b output |
| `{actual-tbox-namespace}` | extracted from `prefix kg_*:` in Step 3b/3a output |
| `{describe-base}` | `{protocol}://{host}/describe/?uri=` |

**Entity sampling query** — execute via `Demo.demo.execute_spasql_query`:

```sparql
SPARQL
SELECT ?type
  (SAMPLE(?entity) AS ?sampleEntity)
  (COUNT(?entity) AS ?entityCount)
FROM <{actual-abox-graph-iri}>
WHERE {
  ?entity a ?type .
  FILTER (STRSTARTS(STR(?type), '{actual-tbox-namespace}'))
}
GROUP BY ?type
ORDER BY DESC(?entityCount)
```

**If the query returns SR324 (transaction timeout):** retry with `LIMIT 100` appended inside the `WHERE` clause. Do NOT simplify by removing the `?entity a ?type` pattern — the RDF View scripts DO generate `rdf:type` triples via the `a ClassName` clause.

⛔ **Never present entity IRIs that were not returned by a live query result.** If all query attempts fail, report the error explicitly — do not fabricate sample links.

Present results as a formatted table. Every value in the table must come directly from the query result — no invented IRIs, no guessed entity keys:

| Entity Type | Sample Entity | Description URL | Count |
|-------------|---------------|-----------------|-------|
| [`{?type value from query}`](`{?type value}`) | [`{?sampleEntity value from query}`](`{?sampleEntity value}`) | [`describe`](`{describe-base}{?sampleEntity value}`) | `{?entityCount}` |

- **Entity Type** → the `?type` IRI returned by the query, hyperlinked (dereferences to ontology class)
- **Sample Entity** → the `?sampleEntity` IRI returned by the query, hyperlinked (dereferences to entity description)
- **Description URL** → `{describe-base}` + the `?sampleEntity` IRI returned by the query

If any IRI fails to dereference, report as a Linked Data compliance gap and investigate the rewrite rule registered in Step 4d.

---

## UQ1 — List Existing Quad Maps

Use at Step 2b (collision detection) and post-deployment verification.

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

Execute via `Demo.demo.execute_spasql_query`. Present results as a numbered list.
