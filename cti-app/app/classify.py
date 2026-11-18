import re

TYPES = [
    ("Ransomware", r"ransomware|extortion|lockbit"),
    ("Phishing", r"phishing|vishing|smishing|business email compromise|spear"),
    ("DDoS", r"\bddos\b|denial[- ]of[- ]service"),
    ("Data Breach", r"data breach|data leak|data theft|stolen data|\bbreach"),
    ("Malware", r"malware|trojan|backdoor|infostealer|stealer|spyware|rootkit|botnet|\bloader\b"),
    ("Vulnerability", r"cve-\d{4}-\d+|vulnerabilit|zero[- ]day|\bpatch|\brce\b|remote code execution|\bflaws?\b|exploit"),
]
PLATFORMS = {
    "Windows": r"\bwindows\b|outlook|ntlm|active directory|patch tuesday|sharepoint",
    "Linux": r"\blinux\b|ubuntu|debian|red hat|\bkernel\b|\bglibc\b|openssh",
    "MacOS": r"\bmacos\b|\bmac os\b|\bosx\b|safari",
    "Android": r"\bandroid\b",
    "iOS": r"\bios\b|\biphone\b|\bipados\b",
}
STATUS = [
    ("Active", r"actively exploited|in the wild|zero[- ]day|ongoing|exploited"),
    ("Resolved", r"\bpatched\b|\bfixed\b|\bfixes\b|security update|\bmitigated\b|\bresolved\b|taken down|takedown|arrested|\bseized\b"),
    ("Active", r"\battacks?\b|\bbreach|campaign|ransomware"),
    ("Evolving", r"new variant|evolv|\bupdated\b|expands?|new wave|new tactic|rising|increase"),
    ("Anticipated", r"\bwarns?\b|\bcould\b|\bmay\b|expected|upcoming|forecast|predict|\brisk|emerging|trends?"),
]
IOCS = [("cve", r"CVE-\d{4}-\d{4,7}"), ("ipv4", r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        ("sha256", r"\b[a-fA-F0-9]{64}\b"), ("md5", r"\b[a-fA-F0-9]{32}\b")]

def _has(pattern, text):
    return re.search(pattern, text, re.I) is not None

def find_iocs(text):
    found = []
    for kind, rx in IOCS:
        for v in dict.fromkeys(re.findall(rx, text, re.I)):
            if kind == "ipv4" and any(int(p) > 255 for p in v.split(".")):
                continue
            found.append({"type": kind, "value": v.upper() if kind == "cve" else v.lower()})
    return found[:20]

def classify(title, summary):
    text = f"{title} {summary}"
    kind = next((name for name, rx in TYPES if _has(rx, text)), "Other")
    if _has(r"actively exploited|zero[- ]day|in the wild|critical|remote code execution|\brce\b|ransomware", text):
        severity = "High"
    elif kind != "Other":
        severity = "Medium"
    else:
        severity = "Low"
    return {"type": kind, "severity": severity,
            "platforms": [p for p, rx in PLATFORMS.items() if _has(rx, text)],
            "status": next((s for s, rx in STATUS if _has(rx, text)), "Unclassified"),
            "iocs": find_iocs(text)}