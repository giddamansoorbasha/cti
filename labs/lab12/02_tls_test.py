from pathlib import Path
from cryptography import x509
from pymongo import MongoClient
from pymongo.errors import PyMongoError

CERTS = Path(__file__).resolve().parent / "certs"

print("[1] Plain connection to TLS server (expect rejection)")
try:
    MongoClient("localhost", 27201, serverSelectionTimeoutMS=3000).admin.command("ping")
    print("  FAIL | plain connection was accepted")
except PyMongoError as e:
    print(f"  PASS | rejected ({type(e).__name__})")

print("\n[2] Mutual TLS connection")
c = MongoClient(
    "localhost", 27201,
    tls=True,
    tlsCAFile=str(CERTS / "ca.crt"),
    tlsCertificateKeyFile=str(CERTS / "client.pem"),
    serverSelectionTimeoutMS=5000,
)
c.cti_tls.test.drop()
c.cti_tls.test.insert_one({"hello": "encrypted"})
print(f"  doc={c.cti_tls.test.find_one({}, {'_id': 0})}")

print("\n[3] Certificate Chain")
for name in ("ca.crt", "server.pem", "client.pem"):
    cert = x509.load_pem_x509_certificate((CERTS / name).read_bytes())
    print(f"  {name:<11} | subject={cert.subject.rfc4514_string()} | issuer={cert.issuer.rfc4514_string()}")