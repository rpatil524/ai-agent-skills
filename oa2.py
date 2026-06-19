#!/usr/bin/env python3
import http.server, urllib.parse, json, sys, os, uuid, base64
from urllib.request import Request, urlopen

ISSUER = "https://linkeddata.uriburner.com"
REDIRECT_URI = "http://localhost:12345/callback"

# --- Step 1: Register dynamic client ---
print("[1/5] Registering dynamic OAuth2 client ...", flush=True)
body = json.dumps({
    "client_name": "CLI OAuth Flow",
    "redirect_uris": [REDIRECT_URI],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
    "scope": "openid webid"
}).encode()
req = Request(f"{ISSUER}/OAuth2/register", data=body,
              headers={"Content-Type": "application/json"})
resp = urlopen(req).read()
reg = json.loads(resp)
cid  = reg["client_id"]
sec  = reg["client_secret"]
print(f"  client_id: {cid}", flush=True)

# --- Step 2: Build authorize URL ---
state = uuid.uuid4().hex[:12]
auth_url = (f"{ISSUER}/OAuth2/authorize?response_type=code"
            f"&client_id={cid}&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
            f"&scope=openid%20webid&state={state}")

# --- Step 3: Thread to handle server ---
exchange_done = False

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(p.query)
        r = {'path': self.path, 'params': {k: v[0] for k, v in params.items()}}
        with open('/tmp/oauth_callback.json', 'w') as f:
            json.dump(r, f, indent=2)

        if 'code' not in params:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(r).encode())
            return

        code = params['code'][0]
        print(f"\n[4/5] Code captured. Exchanging for Bearer token ...", flush=True)

        # Exchange immediately
        global exchange_done
        token_url = f"{ISSUER}/OAuth2/token"
        creds_b64 = base64.b64encode(f"{cid}:{sec}".encode()).decode()
        b = f"grant_type=authorization_code&code={code}&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
        try:
            req = Request(token_url, data=b.encode(),
                          headers={
                              "Content-Type": "application/x-www-form-urlencoded",
                              "Authorization": f"Basic {creds_b64}"
                          })
            resp = urlopen(req).read()
            token_data = json.loads(resp)
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token", "")

            with open('/tmp/ub_bearer_token.sh', 'w') as f:
                f.write(f"TOKEN={access_token}\n")
                f.write(f"CLIENT_ID={cid}\n")
                f.write(f"CLIENT_SECRET={sec}\n")
                f.write(f"REFRESH={refresh_token}\n")
                f.write(f"EXPIRES_AT=$(( $(date +%s) + {token_data['expires_in']} ))\n")

            print(f"[5/5] Bearer token obtained!\n", flush=True)
            print(f"Token: {access_token}", flush=True)
            print(f"Expires: {token_data['expires_in']}s", flush=True)
            print(f"Refresh: {refresh_token}", flush=True)
            print(f"\nSaved to: /tmp/ub_bearer_token.sh", flush=True)
            exchange_done = True
        except Exception as e:
            print(f"Token exchange failed: {e}", flush=True)

        resp_body = ("<html><body style='font-family:sans-serif;text-align:center;"
                     "padding:60px'><h1>Authentication complete</h1>"
                     "<p>You can close this tab and return to the terminal.</p></body></html>")
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body.encode())
        os._exit(0)

    def log_message(self, *a): pass

server = http.server.HTTPServer(('0.0.0.0', 12345), Handler)

print(f"\n[2/5] Capture server listening on http://localhost:12345", flush=True)
print(f"\n[3/5] OPEN THIS URL IN YOUR BROWSER:\n", flush=True)
print(f"  {auth_url}\n", flush=True)
print("  (Authenticate via Digest prompt, then consent on OAuth page)", flush=True)
print("  (After redirect, you'll see 'Authentication complete' - close the tab)\n", flush=True)

server.handle_request()
