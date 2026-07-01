# YouID Skill

Generate, verify, and manage Web-scale verifiable digital identities (NetIDs) using semantic web standards — self-signed X.509 certificates, WebID profile documents (Turtle, JSON-LD, RDFa HTML), identity card HTML pages, vCard VCF, and complete linked-data identity bundles.

→ Full specification: [SKILL.md](SKILL.md)  
→ Usage prompts: [examples/README.md](examples/README.md)

---

## Protocol Flows

The diagrams below illustrate the two core authentication protocols that YouID credentials participate in.

**Important framing:** Both protocols are **additions to a standard TLS handshake** — not replacements for it. The standard TLS handshake (RFC 5246 / RFC 8446) completes first, establishing an encrypted channel and optionally authenticating the client via X.509 certificate (mTLS). WebID+TLS and WebID+TLS+Delegation then add **application-layer verification steps** on top of that completed handshake. The TLS layer itself is unchanged.

The additional steps are grounded in **Decentralised Public Key Infrastructure (DPKI)**: the X.509 certificate carries the identity URI (WebID/NetID) in its Subject Alternative Name (SAN), so identity trust is anchored to the published profile document rather than a central Certificate Authority hierarchy.

---

### 1 — WebID+TLS (Basic mTLS + WebID Application Layer)

Standard TLS with client authentication (mTLS) completes first. The WebID extension then adds an application-layer step: the server extracts the WebID URI from the certificate's SAN, dereferences it to fetch the published profile document, and compares the certificate's RSA public key modulus against the `cert:RSAPublicKey` declared in that profile. Match = verified identity, no CA required.

```mermaid
sequenceDiagram
    autonumber
    participant C as 👤 Client<br/>(Browser / Agent)
    participant S as 🖥 Server<br/>(Relying Party)
    participant W as 🌐 WebID Profile<br/>(Linked Data endpoint)

    Note over C: Holds X.509 cert<br/>SAN = WebID URI<br/>e.g. https://…/index.html#netid

    rect rgb(220, 220, 235)
        Note over C,S: ── Standard TLS Handshake (RFC 5246 / RFC 8446) ──────────────────<br/>This phase is unchanged. WebID adds nothing to it.
        C->>S: ClientHello (TLS version, cipher suites, random)
        S-->>C: ServerHello + Server Certificate
        S-->>C: CertificateRequest (requesting client cert)
        C->>S: Client Certificate (X.509, self-signed, WebID SAN)<br/>+ CertificateVerify (proof of private key possession)<br/>+ Finished
        S-->>C: Finished
        Note over C,S: Encrypted channel established.<br/>Server holds the client's X.509 certificate.
    end

    rect rgb(235, 242, 255)
        Note over S,W: ── WebID Extension — Phase 1: Extract identity from cert ──────────<br/>Application-layer addition. Runs after TLS completes.
        S->>S: Parse client X.509 cert<br/>Extract SAN URI → WebID/NetID
        S->>S: Extract RSA public key modulus<br/>from presented cert
    end

    rect rgb(255, 248, 235)
        Note over S,W: ── WebID Extension — Phase 2: Dereference WebID profile ──────────
        S->>W: GET {WebID URI}<br/>Accept: text/turtle
        W-->>S: Turtle profile document<br/>containing cert:RSAPublicKey declaration
        S->>S: Parse cert:modulus from profile
    end

    rect rgb(235, 255, 242)
        Note over S: ── WebID Extension — Phase 3: Cryptographic corroboration ──────
        S->>S: Compare cert modulus == profile cert:modulus?
        alt Match
            S-->>C: ✅ WebID identity verified<br/>Access granted as WebID subject
        else Mismatch
            S-->>C: ⚠️ Modulus mismatch — authentication failed
        end
    end

    Note over C,S: No CA chain required for identity trust.<br/>DPKI: trust anchored to the published WebID profile document.
```

**What is added on top of standard TLS:**
- The server **reads the SAN** from the already-presented client certificate (Phase 1) — the cert was already exchanged during the standard handshake
- The server **dereferences the SAN URI** to fetch the published WebID profile (Phase 2) — an HTTP GET that happens at the application layer
- The server **compares moduli** to confirm the cert matches the published identity (Phase 3) — a cryptographic check at the application layer

---

### 2 — WebID+TLS+Delegation (mTLS + WebID Application Layer + On-Behalf-Of)

Standard TLS with client authentication completes first (same as Protocol 1). The WebID extension then verifies the agent's identity. A further delegation layer is then added at the HTTP request level: the agent includes an `On-Behalf-Of` header declaring the principal it acts for, and the server performs a **reciprocal corroboration check** against both parties' published profiles. All three layers are cumulative.

```mermaid
sequenceDiagram
    autonumber
    participant A as 🤖 Agent<br/>(Delegate)
    participant S as 🖥 Server<br/>(Relying Party)
    participant AP as 📄 Agent Profile<br/>(WebID endpoint)
    participant UP as 📄 Principal Profile<br/>(WebID endpoint)

    Note over A: Holds agent X.509 cert<br/>SAN = agent WebID<br/>Knows principal WebID

    rect rgb(220, 220, 235)
        Note over A,S: ── Standard TLS Handshake (RFC 5246 / RFC 8446) ──────────────────<br/>Unchanged. Agent authenticates with its own certificate.
        A->>S: ClientHello
        S-->>A: ServerHello + Server Certificate + CertificateRequest
        A->>S: Agent Certificate (X.509, agent WebID SAN)<br/>+ CertificateVerify + Finished
        S-->>A: Finished
        Note over A,S: Encrypted channel established using the AGENT's certificate.<br/>The agent is authenticating as itself, not as the principal.
    end

    rect rgb(235, 242, 255)
        Note over S,AP: ── WebID Extension — Verify agent identity ────────────────────────<br/>Same application-layer steps as Protocol 1.
        S->>S: Extract agent WebID from cert SAN
        S->>AP: GET {agent WebID} — Accept: text/turtle
        AP-->>S: Agent profile (cert:RSAPublicKey)
        S->>S: cert modulus == profile modulus? ✅
    end

    rect rgb(255, 248, 235)
        Note over A,S: ── Delegation Extension — On-Behalf-Of HTTP header ────────────────<br/>Addition at the HTTP request layer, after TLS + WebID complete.
        A->>S: HTTP Request<br/>On-Behalf-Of: {principal WebID URI}
        S->>S: Extract principal WebID<br/>from On-Behalf-Of header
        Note over S: This header is a self-declaration.<br/>By itself it is not corroborated proof of delegation.
    end

    rect rgb(255, 240, 230)
        Note over S,UP: ── Delegation Extension — Reciprocal profile corroboration ─────────<br/>Both published profiles must independently declare the relationship.
        S->>UP: GET {principal WebID} — Accept: text/turtle
        UP-->>S: Principal profile document
        S->>S: Does principal profile contain<br/>oplcert:hasIdentityDelegate {agent WebID}? ✅
        S->>S: Does agent profile contain<br/>oplcert:onBehalfOf {principal WebID}? ✅
    end

    rect rgb(235, 255, 242)
        Note over S: ── Delegation decision ──────────────────────────────────────────────
        alt Both profiles declare the relationship
            S-->>A: ✅ Agent verified<br/>✅ Delegation corroborated (both profiles)<br/>Agent acts on behalf of {principal}
        else Only one profile declares
            S-->>A: ⚠️ Delegation partially corroborated<br/>(state which profile is missing the triple)
        else Neither profile declares
            S-->>A: ⚠️ On-Behalf-Of unconfirmed<br/>Treated as agent identity only
        end
    end

    Note over A,S: Three cumulative layers:<br/>1. Standard TLS — encrypted channel + client cert exchange<br/>2. WebID extension — application-layer identity corroboration via DPKI<br/>3. Delegation extension — HTTP-layer On-Behalf-Of + reciprocal profile check
```

**What is added on top of standard TLS:**
- **WebID extension** (same as Protocol 1): SAN extraction → profile dereference → modulus comparison
- **`On-Behalf-Of` HTTP header** (delegation layer 1): the agent self-declares the principal it represents — added at the HTTP request layer, not the TLS layer
- **Reciprocal profile corroboration** (delegation layer 2): the server independently checks both published profiles for matching triples — neither party can fake this without controlling the other's profile document

**Why the header alone is insufficient:** the `On-Behalf-Of` header is a self-declaration. A well-behaved relying party must confirm the corroborating triples in both profiles before treating the delegation as authorised. Skipping this step cannot distinguish authorised delegation from impersonation.

---

## Credential Bundle Structure

A YouID credential bundle (generated by `scripts/generate_identity.sh`) contains all representations needed to participate in both protocols:

| File | Role in protocol |
|------|-----------------|
| `cert.pem` / `cert.p12` | X.509 certificate — presented in TLS ClientHello (standard handshake) |
| `profile.ttl` | Published WebID profile — `cert:RSAPublicKey` for modulus check (WebID extension) |
| `profile.jsonld` | JSON-LD equivalent of profile.ttl |
| `profile_rdfa.html` | RDFa HTML equivalent — human-readable + machine-readable |
| `index.html` | Identity card — POSH + embedded JSON-LD + embedded Turtle + hidden RDFa |
| `public_key.ttl` | Standalone public key document |
| `certificate.ttl` | Standalone certificate metadata |
| `vcard.vcf` | vCard for address book import |

For delegation, `profile.ttl` and `index.html` must additionally carry:

| Party | Triple | File(s) |
|-------|--------|---------|
| Delegator (principal) | `oplcert:hasIdentityDelegate <delegate-webid>` | `profile.ttl`, `profile.jsonld`, `profile_rdfa.html`, `index.html` |
| Delegate (agent) | `oplcert:onBehalfOf <delegator-webid>` | `profile.ttl`, `profile.jsonld`, `profile_rdfa.html`, `index.html` |

See [SKILL.md § T6](SKILL.md) for the delegation workflow.
