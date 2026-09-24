#!/usr/bin/env python3
"""Verify every vendored xcframework against its own code signature.

A signed framework records a SHA-1 and a SHA-256 of every resource it carries in
_CodeSignature/CodeResources. Those digests are Brother's, produced when Brother
signed the build, so they are the only authority on what the bytes should be.
This recomputes all of them and exits non-zero on any drift.

There is nothing to compile in this repository, so a damaged artifact is
invisible until a consumer links it. That is what this is for.
"""

import hashlib
import pathlib
import plistlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "Sources"

# Brother seals two simulator .swiftmodule binaries it does not ship. The
# framework carries .swiftinterface files instead, and the omission is identical
# in both products, so it is Brother's distribution and not damage here. Any
# other absence is a resource that went missing after Brother signed it.
EXPECTED_ABSENT = frozenset(
    {
        "Modules/BRLMPrinterKit.swiftmodule/arm64-apple-ios-simulator.swiftmodule",
        "Modules/BRLMPrinterKit.swiftmodule/x86_64-apple-ios-simulator.swiftmodule",
    }
)


def sealed_resources(code_resources):
    base = code_resources.parent.parent
    recorded = plistlib.loads(code_resources.read_bytes())

    for algorithm, group in (
        ("sha1", recorded.get("files", {})),
        ("sha256", recorded.get("files2", {})),
    ):
        for path, meta in group.items():
            key = "hash2" if algorithm == "sha256" else "hash"
            digest = meta if isinstance(meta, bytes) else meta.get(key)

            if digest is None:
                continue

            yield path, base / path, algorithm, bytes(digest)


def main():
    if not SOURCES.is_dir():
        sys.exit(f"no Sources directory at {SOURCES}")

    checked, drifted, absent = 0, [], []

    for code_resources in sorted(SOURCES.rglob("_CodeSignature/CodeResources")):
        for path, resource, algorithm, digest in sealed_resources(code_resources):
            where = resource.relative_to(ROOT)

            if not resource.exists():
                if path not in EXPECTED_ABSENT:
                    absent.append(where)
                continue

            checked += 1

            if hashlib.new(algorithm, resource.read_bytes()).digest() != digest:
                drifted.append(f"{where} ({algorithm})")

    for where in sorted(set(absent)):
        print(f"sealed resource is missing: {where}", file=sys.stderr)

    for entry in sorted(set(drifted)):
        print(f"sealed resource does not match the signature: {entry}", file=sys.stderr)

    if drifted or absent:
        print(
            "\nThese artifacts are redistributed unmodified under Brother's EULA, so the "
            "fix is to restore the vendor's bytes, never to regenerate a signature.\n"
            "Line ending normalisation is the usual cause: Brother ships ten printer "
            "definition files per slice with CRLF, and git rewrites them on a checkout "
            "where core.autocrlf is set unless .gitattributes marks the tree binary.\n"
            "Re-extract the xcframework from Brother's own download. See CLAUDE.md.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{checked} sealed resources verify against their signature")


if __name__ == "__main__":
    main()
