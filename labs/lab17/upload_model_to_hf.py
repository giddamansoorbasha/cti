import json
import os
import re
import subprocess

from huggingface_hub import HfApi

USER = "gmansoor"
MODEL = "llama3.2:3b"
REPO = f"{USER}/Llama-3.2-3B-CTI-GGUF"
GGUF_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"


def ollama(*args):
    return subprocess.run(["ollama", *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


modelfile = ollama("show", MODEL, "--modelfile")
blob = re.search(r"^FROM (.+)$", modelfile, re.M).group(1).strip()            # the .gguf inside Ollama
template = re.search(r'TEMPLATE """(.*?)"""', modelfile, re.S).group(1)        # chat template
stops = re.findall(r"^PARAMETER stop (.+)$", modelfile, re.M)
license_text = ollama("show", MODEL, "--license")

readme = f"""---
license: llama3.2
base_model: meta-llama/Llama-3.2-3B-Instruct
pipeline_tag: text-generation
tags:
- gguf
- ollama
---
# Llama 3.2 3B Instruct (GGUF, Q4_K_M) for the CTI Platform

Built with Llama.

Run it: `ollama run hf.co/{REPO}`
"""
notice = ("Llama 3.2 is licensed under the Llama 3.2 Community License, "
          "Copyright © Meta Platforms, Inc. All Rights Reserved.\n")

api = HfApi(token=os.environ["HF_TOKEN"])
api.create_repo(REPO, repo_type="model", exist_ok=True)
for name, content in [("README.md", readme), ("NOTICE", notice), ("LICENSE", license_text),
                      ("template", template), ("params", json.dumps({"stop": stops}))]:
    api.upload_file(path_or_fileobj=content.encode("utf-8"), path_in_repo=name, repo_id=REPO)
print("small files uploaded, now the 2 GB model file...")
api.upload_file(path_or_fileobj=blob, path_in_repo=GGUF_NAME, repo_id=REPO)
print("done: https://huggingface.co/" + REPO)