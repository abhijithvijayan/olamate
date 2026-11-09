"""
Fix generated gRPC stubs to use relative imports.

protoc generates `import wifican_pb2 as ...` (absolute), but inside the
collector package we need `from . import wifican_pb2 as ...` (relative).

This script patches the generated file in-place. Works on all platforms
(unlike the `sed -i ''` variant which is macOS-only).

Usage:
    python scripts/fix_grpc_imports.py
"""

import sys
from pathlib import Path

STUB = Path(__file__).resolve().parent.parent / "collector" / "wifican_pb2_grpc.py"

OLD = "import wifican_pb2 as wifican__pb2"
NEW = "from . import wifican_pb2 as wifican__pb2"


def main() -> int:
    if not STUB.exists():
        print(f"Stub not found: {STUB}")
        print("Run protoc first to generate the gRPC stubs.")
        return 1

    text = STUB.read_text()
    if NEW in text:
        print("Import already fixed.")
        return 0

    if OLD not in text:
        print(f"Expected import line not found in {STUB}")
        return 1

    STUB.write_text(text.replace(OLD, NEW, 1))
    print(f"Fixed import in {STUB.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
