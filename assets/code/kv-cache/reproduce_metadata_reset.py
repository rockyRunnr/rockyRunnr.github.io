"""Reproduce PR #21757 metadata reset using unmodified headers at its exact SHA.

Run: python3 reproduce_metadata_reset.py
Requires Python 3, internet, and a C++17 compiler. Downloads public headers into
a temporary directory. Does not run a model or modify an existing checkout.
"""
from pathlib import Path
import subprocess
import tempfile
import urllib.request

SHA = "1e79a792e03b48a205e80b5eadeffabd09f6af14"
FILES = [
    "src/llama-kv-cells.h", "src/llama-cparams.h", "include/llama.h",
    *["ggml/include/" + name for name in [
        "ggml.h", "ggml-cpu.h", "ggml-backend.h", "ggml-opt.h",
        "gguf.h", "ggml-alloc.h",
    ]],
]

with tempfile.TemporaryDirectory(prefix="pr21757-metadata-") as directory:
    root = Path(directory)
    for filename in FILES:
        destination = root / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/ggml-org/llama.cpp/{SHA}/{filename}"
        with urllib.request.urlopen(url, timeout=30) as response:
            destination.write_bytes(response.read())
    source = Path(__file__).with_name("check_metadata.cpp")
    binary = root / "check_metadata"
    subprocess.run([
        "c++", "-std=c++17", f"-I{root / 'src'}",
        f"-I{root / 'include'}", f"-I{root / 'ggml/include'}",
        str(source), "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True)
