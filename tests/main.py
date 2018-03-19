import requests

url = "http://localhost:5000/api/v1"

import logging
logging.basicConfig(level=logging.DEBUG)

def sign(payload, nonce):
    return "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f"

def nonce():
    i = 0
    while True:
        i += 1
        yield i

pk1 = "bcaa384b13425644dfa8af38075a7584c522c1b312e781ccf0d319f8832cff07"
pk2 = "541c69aef08e5f18aa5006775648440d036d457ce02c551443682897cd89cd65"
pk3 = "BdWhmsVaZNhzRGnsMGOuXUcRbvO98er1v+r7969j1RXlL6ljl6WnyJvLJRXZ0OGS"

ms1 = "Gg4lVg+pF//c0NOqdmiMS9YOo01kQQJAEVk236XxIoBBZIkpC7XyrLIl7YvL5TlSENEddI5u4jb4rDZ4kXBJJJ1UjbVtN8E3wgT4QQqwWjLYHkEiaRbwYQJBAOJ8bHaj"

ms2 = "R8MUkyl4zQXSUNwlg5kAp+9NXKRNziJDXixGCIUvItb2B9OTUZEdVmyJfBniqUBzlcwgpSXM/S5EBno1aQiwWWWMmrW1AgMBAAECgYEAwfapIUS3BUXIjepFIsMI4bAY"

ms3 = "MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBANNc5olpIWw26vZv43Rkbs4tqT7/8FYYBQECQQDwPKX8kHADSfSpLx+8no6A0mzW0W06MoIxYUL3eikE"

session1 = requests.post(url + "/open_session", json={"public_key": pk1}).json()["session_id"]
session2 = requests.post(url + "/open_session", json={"public_key": pk2}).json()["session_id"]
session3 = requests.post(url + "/open_session", json={"public_key": pk3}).json()["session_id"]

def headers(payload, session):
    nonce_val = next(nonce())
    return {
        "x-nonce": str(nonce_val),
        "x-session-id": session,
        "x-signature": sign(payload, nonce_val)
    }

data = {"participants": 2, "signers": 2, "name": "NofN", "multisig_info": ms1}
walletNN = requests.post(url + "/create_wallet", headers=headers(data, session1), json=data).json()

print ("Got wallet N/N for pk1: %s" % walletNN['invite_code'])
