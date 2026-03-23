# OpenLink License ASN.1 Field Reference

## ASN.1 Structure Overview

OpenLink `.lic` files are DER-encoded ASN.1 structures with this layout:

```
SEQUENCE (root)
  SEQUENCE (license data)
    INTEGER          ← version (always 0101)
    PRINTABLESTRING  ← product name (e.g. "virtuoso", "oplrqb", "oracle19")
    SEQUENCE (fields)
      SEQUENCE       ← field 1
        PRINTABLESTRING  ← field name (key)
        PRINTABLESTRING  ← field value
      SEQUENCE       ← field 2
        ...
  cont [2]           ← digital signature block
    INTEGER          ← signer info
    INTEGER          ← hash
    INTEGER          ← RSA signature (256 bytes)
```

Depth mapping:
- `d=0` — root container
- `d=1` — license payload / signature block
- `d=2` — version integer, product name, fields container
- `d=3` — individual field SEQUENCE wrappers
- `d=4` — field key and value PRINTABLESTRING pairs

---

## Known License Fields

| ASN.1 Key | Display Label | Description |
|---|---|---|
| `RegisteredTo` | Registered To | Licensee name or WebID/email URL |
| `SerialNumber` | Serial Number | License serial (base64 or internal label) |
| `NumberOfUsers` | Users | Max concurrent users |
| `NumberOfConnections` | Connections | Max concurrent connections |
| `NumberOfCPUS` | CPUs | Max CPUs (0 = unlimited) |
| `ExpireDate` | Expire Date | Expiry date string; empty = perpetual |
| `Platform` | Platform | Target OS (see Platform table below) |
| `WSType` | Edition | License tier (see WSType table below) |
| `Availability` | Availability | License enabled/disabled flag |
| `Release` | Release | Product version (e.g. "8.3", "10.0") |
| `Modules` | Modules | Comma-separated feature modules (Virtuoso) |
| `Clients` | Clients | Comma-separated client protocol access |
| `DisableSNBC` | Disable SNBC | Disable shared-nothing broadcast (Yes/No) |
| `UniqueID` | Unique ID | License instance fingerprint (MD5 hex) |
| `HostID` | Host Lock | MAC address or hostname lock (if present) |
| `Options` | Options | Additional driver-specific option flags |

---

## WSType Decode Table (Edition)

| WSType Value | Edition Label |
|---|---|
| `0` | Lite / Express |
| `1` | Personal |
| `2` | Standard |
| `3` | Enterprise / Commercial |
| `4` | Workgroup |

---

## Availability Decode Table

| Value | Meaning |
|---|---|
| `0` | Disabled |
| `1` | Enabled |

---

## Platform Decode Table

| Value | Meaning |
|---|---|
| `_ANY_` | Platform-independent (any OS) |
| `win32` | Windows 32-bit |
| `win64` | Windows 64-bit |
| `linux` | Linux |
| `macosx` | macOS |
| `solaris` | Solaris |
| `aix` | IBM AIX |
| `hpux` | HP-UX |

---

## Modules Decode Table (Virtuoso)

| Module | Description |
|---|---|
| `COLUMNSTORE` | Column-store index support |
| `CLUSTER` | Multi-server cluster mode |
| `ABAC` | Attribute-based access control |
| `BI` | Business Intelligence extensions |
| `REPL` | Replication |
| `VAL` | Virtuoso Authentication Layer |
| `VDB` | Virtual Database (ODBC/JDBC federation) |
| `SPIN` | SPIN rules / inference |
| `GEO` | Geospatial extensions |
| `FACETS` | Faceted browsing engine |

---

## Clients Decode Table

| Client | Description |
|---|---|
| `ODBC` | ODBC connectivity |
| `JDBC` | JDBC connectivity |
| `OLEDB` | OLE DB connectivity |
| `DOTNET` | .NET provider |
| `XMLA` | XML for Analysis (OLAP) |
| `ADO` | ADO.NET |

---

## Product Name Reference

| Product Name in License | Product Description |
|---|---|
| `virtuoso` | OpenLink Virtuoso Universal Server |
| `oplrqb` | OpenLink Request Broker (Multi-Tier) |
| `odbc` | OpenLink Generic ODBC Driver |
| `jdbc` | OpenLink JDBC Driver |
| `oracle19` / `ora19` | OpenLink Oracle 19.x Driver |
| `oracle12` / `ora12` | OpenLink Oracle 12.x Driver |
| `mysql8` / `mys8` | OpenLink MySQL 8.x Driver |
| `mysql5` / `mys5` | OpenLink MySQL 5.x Driver |
| `postgres` / `pgr` | OpenLink PostgreSQL Driver |
| `sqlserver` / `sql` | OpenLink SQL Server Driver |
| `informix` / `inf` | OpenLink Informix Driver |
| `ingres` / `ing` | OpenLink Ingres Driver |
| `sybase` / `syb` | OpenLink Sybase Driver |
| `db2` | OpenLink DB2 Driver |
| `progress` / `pro` | OpenLink Progress/OpenEdge Driver |
| `nodbc` | OpenLink .NET ODBC Provider |
| `jodbc` | OpenLink J/ODBC Bridge |
| `virtagent` | Virtuoso Agent License |

Suffix conventions:
- `_lt` = Lite/single-tier variant
- `-{number}` = license instance discriminator

---

## Expiry Date Format

```
Thu Mar 18 00:00:00 2027 GMT
```

Parse with Python:
```python
from datetime import datetime
dt = datetime.strptime(expire_str.strip(), '%a %b %d %H:%M:%S %Y %Z')
```

Empty `ExpireDate` value = **perpetual** license (no expiry).

---

## Signature Block

The `cont [2]` section at `d=1` contains three integers:
1. **Signer info** — 24-byte identifier encoding OpenLink Software
2. **Hash** — 16-byte MD5 hash of the license payload
3. **RSA signature** — 256-byte RSA-2048 signature (not decoded — display as-is if raw dump requested)
