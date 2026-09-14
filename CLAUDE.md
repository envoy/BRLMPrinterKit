# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A thin Swift Package wrapper around Brother's closed-source **Brother Print SDK (BT_Net) for iOS**. There is no source code to build, lint, or test here. The package exposes a single `.binaryTarget` pointing at `Sources/BRLMPrinterKit.xcframework`, which is a vendored, Brother-signed binary (Team ID `5HCL85FLGW`). The framework is Objective-C with a small Swift overlay; its public API is the headers under `BRLMPrinterKit.framework/Headers` (`BRLMPrinterDriver`, `BRLMPrinterSearcher`, `BRLMChannel`, `BRLM*PrintSettings`, plus the legacy `BRPtouch*` layer).

The only consumer is `envoy-ipad`, via its local `PrinterKit` package, pinned with `exact:` to a tagged version. Bumping the SDK here is only useful once the tag exists and `envoy-ipad` is updated to point at it.

## Commands

- `swift build` does **not** work on macOS and never will. The only target is an iOS binary target, so SwiftPM reports "does not contain a buildable target". This is expected, not a bug.
- Verify the package resolves: `swift package describe`
- Inspect the vendored SDK version: `plutil -p Sources/BRLMPrinterKit.xcframework/ios-arm64/BRLMPrinterKit.framework/Info.plist | grep CFBundleShortVersionString`
- List slices: `plutil -p Sources/BRLMPrinterKit.xcframework/Info.plist`
- Verify the signature is intact: `codesign --verify --deep --strict --verbose=2 Sources/BRLMPrinterKit.xcframework` (expect "valid on disk" and "satisfies its Designated Requirement")
- Read the Team ID: `codesign -dv Sources/BRLMPrinterKit.xcframework` (this only displays the signature; it does not validate it)

To actually compile against the SDK, build a consuming iOS app or package (e.g. `envoy-ipad`), not this repo.

## Versioning

Tags mirror Brother's `CFBundleShortVersionString` with a `v` prefix (`v4.6.1`, `v4.12.0`, `v4.13.0`; one early tag `4.3.1` lacks the prefix). They are **not** semver for this package's API surface: Brother removes public API in patch releases (4.13.2 dropped the entire BMS UIKit layer). Consumers must pin `exact:`, never `from:` or `.upToNextMinor`.

Toolchain floor is whatever Brother built the current xcframework with; read it from the `swift-compiler-version` line of `Sources/BRLMPrinterKit.xcframework/ios-arm64/BRLMPrinterKit.framework/Modules/BRLMPrinterKit.swiftmodule/arm64-apple-ios.swiftinterface`. Minimum iOS is in `LC_BUILD_VERSION` (`otool -l <binary> | grep minos`), currently 14.0.

## Updating the SDK (the only real workflow)

Each release is one commit that replaces the whole xcframework, done on a branch and merged via PR, then tagged. There is no CI in this repo; the checks below are run by hand.

1. Download the new BT_Net SDK from Brother's developer page (link in README).
2. Replace `Sources/BRLMPrinterKit.xcframework` wholesale. Keep the path identical because `Package.swift` hardcodes it. Do not hand-edit anything inside the xcframework; the EULA forbids modifying the redistributable and the code signature would break.
3. Confirm the new xcframework still ships `ios-arm64` and `ios-arm64_x86_64-simulator` slices and a `PrivacyInfo.xcprivacy` in each.
4. Run `codesign --verify --deep --strict` and confirm the Team ID is still `5HCL85FLGW`.
5. Diff `Headers/` against `main` and note removed or renumbered API in the PR description. Brother's implicit-value `NS_ENUM`s (e.g. `BRLMPrinterModel`, `BRLMPrinterSearchError`) shift raw values when cases are inserted before `Unknown`, so grep the consumer for persisted or transmitted `rawValue`s.
6. Commit, PR to `main`, then tag the merge commit `vX.Y.Z` and push the tag.
7. Bump the `exact:` pin in `envoy-ipad`'s `PrinterKit/Package.swift`.

### Known state to be aware of

- Tag `v4.13.0` points at `a677f6c` on branch `ms/update-version4.13.0Binary` and is not reachable from `main`, though the same 4.13.0 SDK content was merged to `main` as `830e6ae`. `envoy-ipad` pins that revision hash, so do not rebase, delete, or force-push that branch.

## Licensing constraint

The SDK is redistributed under Brother's EULA (`EULA.pdf`, also reproduced in full in `README.md`). It may be incorporated unmodified into Envoy apps that print to Brother printers. Do not reverse-engineer, patch, or strip the binary, and do not add Brother logos or trademarks to app UI.
