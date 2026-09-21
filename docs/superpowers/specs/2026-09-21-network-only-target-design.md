# Network-only product in BRLMPrinterKit

Date: 2026-09-21
Branch: `ms/feature-includeNetFramework`
SDK version in scope: Brother Print SDK 4.13.2

## Goal

Expose Brother's network-only (`Net`) build of the Print SDK as a second SwiftPM
product in this package, alongside the existing Bluetooth+network (`BT_Net`)
build. Both products are first-class and permanent; consumers choose one.

## What the two builds actually differ by

Measured against `libs/Net` and `libs/BT_Net` of the 4.13.2 download:

| | BT_Net | Net |
|---|---|---|
| Public headers | 36 | 36, byte-identical |
| Swift module name | `BRLMPrinterKit` | `BRLMPrinterKit` |
| Bundle identifier | `com.brother.BRLMPrinterKit` | `com.brother.BRLMPrinterKit` |
| Links `ExternalAccessory` | yes | **no** |
| Links `CoreBluetooth` | yes | yes |
| Minimum iOS | 14.0 | 14.0 |
| Built with | Swift 6.1 (effective-5.10) | Swift 6.1 (effective-5.10) |
| arm64 binary size | 4,068,856 B | 4,024,760 B |

The only meaningful difference is the dropped `ExternalAccessory` link. That
removes the MFi accessory surface, so a consuming app needs no
`UISupportedExternalAccessoryProtocols` entry and no MFi declarations.

It does **not** remove Bluetooth from the API. The headers are identical and
`CoreBluetooth` is still linked, so Bluetooth channel calls compile against the
Net product and fail only at runtime. The Net product is a linkage guarantee,
not a compile-time one.

The repo's current `Sources/BRLMPrinterKit.xcframework` is byte-identical to the
download's `libs/BT_Net/BRLMPrinterKit.xcframework`, so this change is purely
additive to the binary content.

## Package structure

Both xcframeworks sit under variant folders mirroring Brother's own `libs/`
layout, each keeping Brother's shipped filename:

```
Sources/
├── BT_Net/BRLMPrinterKit.xcframework
└── Net/BRLMPrinterKit.xcframework
```

The existing xcframework moves with `git mv` so history follows it. Moving it
supersedes the previous "keep the path identical" rule in `CLAUDE.md`, which
must be rewritten to name both paths.

`Package.swift`:

```swift
products: [
    .library(name: "BRLMPrinterKit",    targets: ["BRLMPrinterKit"]),
    .library(name: "BRLMPrinterKitNet", targets: ["BRLMPrinterKitNet"]),
],
targets: [
    .binaryTarget(name: "BRLMPrinterKit",
                  path: "./Sources/BT_Net/BRLMPrinterKit.xcframework"),
    .binaryTarget(name: "BRLMPrinterKitNet",
                  path: "./Sources/Net/BRLMPrinterKit.xcframework"),
]
```

Product name `BRLMPrinterKit` is unchanged, so `envoy-ipad` is unaffected by the
move: it resolves by product name and the path is package-internal. Revisions
already pinned keep resolving because they point at existing commits.

A binary target's name need not match the framework inside it. The module a
consumer imports is `BRLMPrinterKit` for both products, regardless of target
name. Renaming or relocating the xcframework directory does not invalidate
Brother's signature; both were verified to still report `valid on disk` and
`satisfies its Designated Requirement` after being moved.

## The mutual-exclusivity contract

Both products vend the same module name and the same bundle identifier. A
consumer must link exactly one. Linking both places two copies of
`BRLMPrinterKit.framework` in the app bundle and makes `import BRLMPrinterKit`
ambiguous.

SwiftPM cannot express or enforce this. Documentation is the only enforcement
available, so it is stated in both `README.md` and `CLAUDE.md`.

## Documentation changes

- `CLAUDE.md`: replace the single hardcoded path with the two variant paths;
  restate the update workflow as two drops, from `libs/BT_Net/` and `libs/Net/`;
  add the mutual-exclusivity contract and what the Net build does and does not
  guarantee. The existing note about tag `v4.13.0` and branch
  `ms/update-version4.13.0Binary` is unrelated and stays as written.
- `README.md`: document the two products, when to choose each, and the
  mutual-exclusivity contract.

## Repository impact

The xcframeworks are committed as plain files; there is no git-lfs in this repo.
`Sources/` is currently 275 tracked files and about 14 MB. Adding the Net
xcframework roughly doubles both, taking `.git` from about 52 MB to about 66 MB.
This is accepted.

Brother's `.DS_Store` files inside the download must not be copied in; the repo
already ignores `.DS_Store`.

## Verification

`swift build` does not work in this package and is not part of verification.
The following checks are settled, and follow the existing by-hand process in
`CLAUDE.md`:

- `swift package describe` lists both products and both binary targets.
- `codesign --verify --deep --strict --verbose=2` passes on both xcframeworks.
- `codesign -dv` reports Team ID `5HCL85FLGW` on both.
- The Net xcframework ships `ios-arm64` and `ios-arm64_x86_64-simulator` slices,
  each containing `PrivacyInfo.xcprivacy`.

One decision is deliberately deferred to before implementation: how to prove the
renamed binary target genuinely links, given that `swift package describe` does
not validate an iOS artifact on macOS. The two candidates are a throwaway
`xcodebuild` iOS target that imports the module and touches `BRLMPrinterDriver`,
or validating against a branch of `envoy-ipad`. Implementation should not be
called complete until one of them has run.

## Out of scope

- Tagging a release and bumping the `exact:` pin in `envoy-ipad`. That is the
  existing release workflow and happens after this merges.
- Any change to the vendored binaries themselves. The EULA forbids modifying the
  redistributable, and it would break the signature.
- Removing or deprecating the `BRLMPrinterKit` product.
