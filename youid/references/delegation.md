# YouID Delegation Reference

## Overview

WebID delegation allows one agent (the **Delegate**) to act on behalf of another agent (the **Delegator**). This is expressed using two OPL-cert ontology properties:

- `oplcert:hasIdentityDelegate` — Declared on the **Delegator**, pointing to the **Delegate**
- `oplcert:onBehalfOf` — Declared on the **Delegate**, pointing back to the **Delegator**

## Deployment Strategies

### A. SPARQL UPDATE (distinct graphs)

The delegator's graph receives only `oplcert:hasIdentityDelegate`. The delegate's graph receives only `oplcert:onBehalfOf`. Inverse relations are not stored — a SPARQL endpoint resolves the delegation by querying the appropriate graph.

### B. Local file deployment (split per entity)

Each identity's local documents declare only their side of the relation:

- **Delegator's files** — `oplcert:hasIdentityDelegate` only (grants authority)
- **Delegate's files** — `oplcert:onBehalfOf` only (acknowledges authority)

Both sets of files must carry the triple in EVERY RDF representation they contain:
- `profile.ttl` — Turtle triples
- `profile.jsonld` — JSON-LD graph entry
- `profile_rdfa.html` — RDFa inline + embedded JSON-LD
- `index.html` — POSH hero header, embedded JSON-LD, embedded Turtle, hidden RDFa annotations

See T6 in `SKILL.md` for the full step-by-step.

## Delegation Roles

| Role | Semantics | Use Case |
|------|-----------|----------|
| `identify` | Delegate may assert the delegator's identity | ID verification, login assertion |
| `inform` | Delegate may receive information intended for the delegator | Notification forwarding, email delegation |
| `consult` | Delegate may be consulted on behalf of the delegator | Decision support, advisory |
| `authority` | Delegate has full authority to act as the delegator | Legal signing, contractual authority |

## SPARQL UPDATE Pattern

Delegator and delegate graphs are distinct. Each graph contains only its side of the relation — never the inverse.

### Insert Delegation (grant)

Insert into the **delegator's** WebID graph:

```sparql
PREFIX foaf:     <http://xmlns.com/foaf/0.1/>
PREFIX oplcert:  <http://www.openlinksw.com/schemas/cert#>
PREFIX schema:   <http://schema.org/>

INSERT INTO <delegator-graph-iri> {
  <delegator-webid>
      a foaf:Agent ;
      schema:additionalType "Delegator" ;
      schema:description "Delegates {ROLE} authority to <delegate-webid>" ;
      oplcert:hasIdentityDelegate <delegate-webid> .
}
```

Insert into the **delegate's** WebID graph:

```sparql
PREFIX foaf:     <http://xmlns.com/foaf/0.1/>
PREFIX oplcert:  <http://www.openlinksw.com/schemas/cert#>
PREFIX schema:   <http://schema.org/>

INSERT INTO <delegate-graph-iri> {
  <delegate-webid>
      a foaf:Agent ;
      schema:additionalType "Delegate" ;
      schema:description "Acts on behalf of <delegator-webid> with {ROLE} authority" ;
      oplcert:onBehalfOf <delegator-webid> .
}
```

### Revoke Delegation (remove)

```sparql
PREFIX oplcert: <http://www.openlinksw.com/schemas/cert#>

DELETE FROM <delegator-graph-iri> {
  <delegator-webid> oplcert:hasIdentityDelegate <delegate-webid> .
};

DELETE FROM <delegate-graph-iri> {
  <delegate-webid> oplcert:onBehalfOf <delegator-webid> .
};
```

## HTTP Header Injection

The **Delegate's** browser must send the `On-Behalf-Of` header with every authenticated request to signal the delegation. This is accomplished via Chrome's `declarativeNetRequest` API.

### Rule Structure

```json
{
  "id": 1,
  "priority": 1,
  "condition": {
    "urlFilter": "*",
    "resourceTypes": ["xmlhttprequest"]
  },
  "action": {
    "type": "modifyHeaders",
    "requestHeaders": [
      {
        "header": "On-Behalf-Of",
        "operation": "set",
        "value": "<delegate-webid>"
      }
    ]
  }
}
```

### Install in Chrome

1. Open `chrome://extensions/`
2. Enable Developer mode
3. Load unpacked extension with the rule in its `rules.json`
4. The extension must have `declarativeNetRequest` permission

## Deployment

### Via SPARQL Endpoint (curl)

For a Virtuoso SPARQL endpoint:

```bash
curl -X POST <endpoint-url> \
  -H 'Content-Type: application/sparql-update' \
  --data-binary @delegation.sparql
```

With authentication:

```bash
# Basic auth
curl -X POST <endpoint-url> \
  -H 'Content-Type: application/sparql-update' \
  -u <username>:<password> \
  --data-binary @delegation.sparql

# Bearer token
curl -X POST <endpoint-url> \
  -H 'Content-Type: application/sparql-update' \
  -H 'Authorization: Bearer <token>' \
  --data-binary @delegation.sparql
```

### Via URIBurner SPASQL

```bash
curl -X POST 'https://linkeddata.uriburner.com/SPARQL' \
  -H 'Content-Type: application/sparql-update' \
  -u <username>:<password> \
  --data-binary @delegation.sparql
```

## Verification

Query the delegator's WebID profile after deployment:

```sparql
PREFIX oplcert: <http://www.openlinksw.com/schemas/cert#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?delegate ?role
WHERE {
  <delegator-webid> oplcert:hasIdentityDelegate ?delegate .
  OPTIONAL { ?delegate schema:additionalType ?role }
}
```

Or to verify from the delegate's side:

```sparql
PREFIX oplcert: <http://www.openlinksw.com/schemas/cert#>

SELECT ?delegator
WHERE {
  <delegate-webid> oplcert:onBehalfOf ?delegator .
}
```
