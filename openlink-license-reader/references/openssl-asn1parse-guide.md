# openssl asn1parse Output Guide

## Command

```bash
openssl asn1parse -in {license-file} -i -inform der
```

| Flag | Purpose |
|---|---|
| `-in` | Input file path |
| `-i` | Indent output to show nesting depth visually |
| `-inform der` | Input format is binary DER (not PEM/base64) |
| `-dump` | Add hex dump of primitive values (only use on request) |

---

## Output Format

Each line follows this pattern:

```
{offset}:d={depth}  hl={header-len} l={content-len} {prim|cons}: {type}   :{value}
```

| Column | Meaning |
|---|---|
| `offset` | Byte offset from start of file |
| `d=` | Nesting depth (0=root, 1=top-level, 2=section, 3=field wrapper, 4=key or value) |
| `hl=` | Header length in bytes (ASN.1 tag + length encoding) |
| `l=` | Content length in bytes |
| `prim` | Primitive type (leaf node — has a value) |
| `cons` | Constructed type (container — holds nested elements) |
| `type` | ASN.1 type name |
| `:value` | Decoded value (for primitive types) |

---

## ASN.1 Types Used in OpenLink Licenses

| Type | Role |
|---|---|
| `SEQUENCE` | Container for ordered elements |
| `INTEGER` | Numeric value (version, signature integers) |
| `PRINTABLESTRING` | Text value (field names, field values, product name) |
| `cont [2]` | Context-specific implicit tag — wraps the digital signature block |

---

## Depth-to-Meaning Map

| Depth | Content |
|---|---|
| `d=0` | Root SEQUENCE (entire file) |
| `d=1` | License payload SEQUENCE / Signature `cont [2]` block |
| `d=2` | Version INTEGER, product name PRINTABLESTRING, fields SEQUENCE |
| `d=3` | Individual field SEQUENCE wrapper (one per key-value pair) |
| `d=4` | Field key PRINTABLESTRING (first) and value PRINTABLESTRING (second) |

---

## Reading Key-Value Pairs

Consecutive `d=4 PRINTABLESTRING` pairs are key → value:

```
 26:d=3  hl=2 l=  81 cons:    SEQUENCE
 28:d=4  hl=2 l=  12 prim:     PRINTABLESTRING   :RegisteredTo    ← key
 42:d=4  hl=2 l=  65 prim:     PRINTABLESTRING   :https://...     ← value
```

---

## Signature Block

The `cont [2]` section is the digital signature and is not human-readable license data:

```
471:d=1  hl=4 l= 304 cons:  cont [ 2 ]
475:d=2  hl=2 l=  24 prim:   INTEGER   :301602016...   ← signer ID (OpenLink Software)
501:d=2  hl=2 l=  16 prim:   INTEGER   :1044116...     ← MD5 hash of payload
519:d=2  hl=4 l= 256 prim:   INTEGER   :1BCB267...     ← RSA-2048 signature
```

Display only if user requests raw dump.

---

## Common Issues

| Issue | Cause | Fix |
|---|---|---|
| `error in loading number` | File is PEM not DER | Try `-inform pem` |
| `unable to load` | File corrupted or wrong format | Verify with `file {license}` command |
| Empty value for `ExpireDate` | Perpetual license | Display as **PERPETUAL** |
| `l=0` for a field | Field present but empty (e.g. perpetual ExpireDate) | Treat as empty/not set |
