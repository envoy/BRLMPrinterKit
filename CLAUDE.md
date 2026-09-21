# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A thin Swift Package wrapper around Brother's closed-source **Brother Print SDK for iOS**. There is no source code to build, lint, or test here. The package exposes two `.binaryTarget`s, each a vendored, Brother-signed binary (Team ID `5HCL85FLGW`):

| Product | Brother build | Path | Transports |
|---|---|---|---|
| `BRLMPrinterKit` | `BT_Net` | `Sources/BT_Net/BRLMPrinterKit.xcframework` | MFi + BLE + network |
| `BRLMPrinterKitNet` | `Net` | `Sources/Net/BRLMPrinterKit.xcframework` | BLE + network, no MFi |

Both vend the **same** module name `BRLMPrinterKit` and bundle id `com.brother.BRLMPrinterKit`, so a consumer must link **exactly one**. SwiftPM cannot enforce this; nothing fails at resolution or build time. Brother's "Net" name is misleading: `Net` is not network-only. It references `CBCentralManager`/`CBUUID` exactly as `BT_Net` does, so BLE works and `NSBluetoothAlwaysUsageDescription` is still required. It drops only `EAAccessoryManager`/`EASession`. The headers are byte-identical across both builds, so MFi calls still compile against `BRLMPrinterKitNet` and fail only at runtime. The framework is Objective-C with a small Swift overlay; its public API is the headers under `BRLMPrinterKit.framework/Headers` (`BRLMPrinterDriver`, `BRLMPrinterSearcher`, `BRLMChannel`, `BRLM*PrintSettings`, plus the legacy `BRPtouch*` layer).

The only consumer is `envoy-ipad`, via its local `PrinterKit` package, pinned with `exact:` to a tagged version. Bumping the SDK here is only useful once the tag exists and `envoy-ipad` is updated to point at it.

## Commands

- `swift build` does **not** work on macOS and never will. The only target is an iOS binary target, so SwiftPM reports "does not contain a buildable target". This is expected, not a bug.
- Verify the package resolves: `swift package describe`
- Inspect the vendored SDK version: `plutil -p Sources/BT_Net/BRLMPrinterKit.xcframework/ios-arm64/BRLMPrinterKit.framework/Info.plist | grep CFBundleShortVersionString` (and the same under `Sources/Net/`)
- List slices: `plutil -p Sources/BT_Net/BRLMPrinterKit.xcframework/Info.plist`
- Verify the signature is intact: `codesign --verify --deep --strict --verbose=2 Sources/BT_Net/BRLMPrinterKit.xcframework` (expect "valid on disk" and "satisfies its Designated Requirement"); repeat for `Sources/Net/`
- Read the Team ID: `codesign -dv Sources/BT_Net/BRLMPrinterKit.xcframework` (this only displays the signature; it does not validate it)

To actually compile against the SDK, build a consuming iOS app or package (e.g. `envoy-ipad`), not this repo.

## Versioning

Tags mirror Brother's `CFBundleShortVersionString` with a `v` prefix (`v4.6.1`, `v4.12.0`, `v4.13.0`; one early tag `4.3.1` lacks the prefix). They are **not** semver for this package's API surface: Brother removes public API in patch releases (4.13.2 dropped the entire BMS UIKit layer). Consumers must pin `exact:`, never `from:` or `.upToNextMinor`.

Toolchain floor is whatever Brother built the current xcframework with; read it from the `swift-compiler-version` line of `Sources/BT_Net/BRLMPrinterKit.xcframework/ios-arm64/BRLMPrinterKit.framework/Modules/BRLMPrinterKit.swiftmodule/arm64-apple-ios.swiftinterface`. Note this is **not** the same as `swift-tools-version`, which stays at 5.6 and only gates who can parse the manifest; do not bump one to follow the other. Minimum iOS is in `LC_BUILD_VERSION` (`otool -l <binary> | grep minos`), currently 14.0 on all four slices and declared as `platforms: [.iOS(.v14)]`.

## Updating the SDK (the only real workflow)

Each release is one commit that replaces the whole xcframework, done on a branch and merged via PR, then tagged. There is no CI in this repo; the checks below are run by hand.

1. Download the new SDK bundle from Brother's developer page (link in README). One download contains both builds, under `libs/BT_Net/` and `libs/Net/`.
2. Replace **both** xcframeworks wholesale: Brother's `libs/BT_Net/BRLMPrinterKit.xcframework` goes to `Sources/BT_Net/`, and `libs/Net/BRLMPrinterKit.xcframework` goes to `Sources/Net/`. Keep both paths and Brother's filename identical because `Package.swift` hardcodes them, and do not copy Brother's `.DS_Store` files in. Do not hand-edit anything inside either xcframework; the EULA forbids modifying the redistributable and the code signature would break.
3. Confirm each new xcframework still ships `ios-arm64` and `ios-arm64_x86_64-simulator` slices and a `PrivacyInfo.xcprivacy` in each.
4. Run `codesign --verify --deep --strict` on both and confirm the Team ID is still `5HCL85FLGW`.
5. Diff `Headers/` against `main` and note removed or renumbered API in the PR description. Also diff `BT_Net` against `Net` headers; they have been byte-identical so far, and if that ever stops being true the README table needs revisiting. Brother's implicit-value `NS_ENUM`s (e.g. `BRLMPrinterModel`, `BRLMPrinterSearchError`) shift raw values when cases are inserted before `Unknown`, so grep the consumer for persisted or transmitted `rawValue`s.
6. Commit, PR to `main`, then tag the merge commit `vX.Y.Z` and push the tag.
7. Bump the `exact:` pin in `envoy-ipad`'s `PrinterKit/Package.swift`.

### Known state to be aware of

- Tag `v4.13.0` points at `a677f6c` on branch `ms/update-version4.13.0Binary` and is not reachable from `main`, though the same 4.13.0 SDK content was merged to `main` as `830e6ae`. `envoy-ipad` pins that revision hash, so do not rebase, delete, or force-push that branch.

## Licensing constraint

The SDK is redistributed under Brother's EULA (`EULA.pdf`, also reproduced in full in `README.md`). It may be incorporated unmodified into Envoy apps that print to Brother printers. Do not reverse-engineer, patch, or strip the binary, and do not add Brother logos or trademarks to app UI.
