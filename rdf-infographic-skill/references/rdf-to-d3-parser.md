# RDF-to-D3 Knowledge Graph Parser

This reference document provides JavaScript utilities for parsing RDF Turtle into D3.js-compatible `kgData` format for knowledge graph visualization.

## Basic Parser Function

```javascript
/**
 * Parse RDF Turtle into D3 nodes and links
 * @param {string} rdfText - RDF Turtle content
 * @param {string} baseIRI - Base IRI for the document
 * @returns {{nodes: Array, links: Array}} kgData compatible object
 */
function parseRDFToGraph(rdfText, baseIRI) {
    const nodes = new Map();
    const links = [];
    
    // Clean and split triples
    const triples = rdfText
        .replace(/@\w+/g, '')  // Remove prefixes like @en
        .split('.\n')
        .map(t => t.trim())
        .filter(t => t && !t.startsWith('#'));
    
    triples.forEach(triple => {
        // Match pattern: :subject predicate :object
        // Handles: :subject a :Class  |  :subject :property :object  |  :subject :property "literal"
        const match = triple.match(/:(\w+)\s+(\w+:?\w*)\s+(:\w+|"[^"]*"|\d+)/);
        if (!match) return;
        
        const [, subject, predicate, object] = match;
        const predLabel = predicate.replace(/^\w+:/, '');  // Remove prefix from predicate
        
        // Add subject node if not exists
        if (!nodes.has(subject)) {
            nodes.set(subject, {
                id: subject,
                label: formatLabel(subject),
                type: determineNodeType(subject, object),
                desc: `RDF entity: ${subject}`
            });
        }
        
        // Add object node if it's a resource (starts with :)
        if (object.startsWith(':')) {
            const objId = object.replace(':', '');
            if (!nodes.has(objId)) {
                nodes.set(objId, {
                    id: objId,
                    label: formatLabel(objId),
                    type: 'instance',
                    desc: `RDF entity: ${objId}`
                });
            }
            links.push({ source: subject, target: objId, label: predLabel });
        }
    });
    
    return { nodes: Array.from(nodes.values()), links };
}

function formatLabel(id) {
    // Convert camelCase to Title Case with spaces
    return id
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, s => s.toUpperCase())
        .trim();
}

function determineNodeType(subject, object) {
    // Heuristic: if object is a known class name, this is a class
    const classNames = ['Class', 'Property', 'Ontology', 'Schema', 'Concept'];
    if (classNames.some(c => object.includes(c))) return 'class';
    return 'instance';
}
```

## Parser with Type Detection from RDF Schema

A more sophisticated parser that uses RDF schema information:

```javascript
function parseRDFWithSchema(rdfText, baseIRI) {
    const classes = new Map();      // Classes from rdfs:Class
    const properties = new Map();   // Properties from rdf:Property
    const instances = new Map();    // Regular instances
    const links = [];
    
    const lines = rdfText.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'));
    
    lines.forEach(line => {
        // Detect class definitions: :X a rdfs:Class
        if (line.includes('a rdfs:Class')) {
            const cls = line.match(/:(\w+)/)?.[1];
            if (cls) classes.set(cls, { id: cls, label: cls, type: 'class', desc: 'RDF Class' });
        }
        
        // Detect property definitions: :X a rdf:Property
        if (line.includes('a rdf:Property')) {
            const prop = line.match(/:(\w+)/)?.[1];
            if (prop) properties.set(prop, { id: prop, label: prop, type: 'property', desc: 'RDF Property' });
        }
        
        // Detect instances and their types
        const instanceMatch = line.match(/:(\w+)\s+a\s+:(\w+)/);
        if (instanceMatch) {
            const [, inst, type] = instanceMatch;
            if (!instances.has(inst)) {
                const nodeType = classes.has(type) ? 'instance' : 'instance';
                instances.set(inst, { 
                    id: inst, 
                    label: formatLabel(inst), 
                    type: nodeType, 
                    desc: `Instance of ${type}` 
                });
            }
            // If type is also a class, add rdf:type link
            if (classes.has(type)) {
                links.push({ source: inst, target: type, label: 'a' });
            }
        }
        
        // Detect property relationships: :X :property :Y
        const propMatch = line.match(/:(\w+)\s+:\w+\s+:\w+/);
        if (propMatch) {
            // Additional relationship handling
        }
    });
    
    // Combine all nodes
    const nodes = [
        ...Array.from(classes.values()),
        ...Array.from(properties.values()),
        ...Array.from(instances.values())
    ];
    
    return { nodes, links };
}
```

## Usage Example

```javascript
// Embedded RDF data from the TTL file
const rdfTurtle = `
@prefix : <https://x.com/example#> .
@prefix schema: <http://schema.org/> .

:FootballTeam a rdfs:Class .
:liverpoolFC a :FootballTeam .
:arneSlot a schema:Person ; :oversaw :liverpoolFC .
:virgilVanDijk a schema:Person ; :playsFor :liverpoolFC .
:playerLoad a :PlayerLoad .
:virgilVanDijk :hasLoad :playerLoad .
`;

// Parse to kgData
const kgData = parseRDFToGraph(rdfTurtle, "https://x.com/example");

// kgData is now ready for D3.js:
// kgData.nodes = [{id: "FootballTeam", ...}, {id: "liverpoolFC", ...}, ...]
// kgData.links = [{source: "liverpoolFC", target: "FootballTeam", label: "a"}, ...]
```

## Key Principles

1. **All subjects become nodes** - Every subject in a triple is a node
2. **Resource objects become nodes** - Objects starting with `:` become nodes
3. **Literals are not nodes** - Plain literal values (strings, numbers) don't create nodes
4. **Predicates become link labels** - The predicate becomes the link label
5. **Type assertions (a/rdf:type) create special links** - Links with label "a" indicate class membership

## Validation

After parsing, always verify:
- No orphaned nodes (every node has at least one link)
- All RDF triples represented as links
- Node types correctly identified (class/property/instance)