# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A thin Swift Package wrapper around Brother's closed-source **Brother Print SDK (BT_Net) for iOS**. There is no source code to build, lint, or test here. The package exposes a single `.binaryTarget` pointing at `Sources/BRLMPrinterKit.xcframework`, which is a vendored, Brother-signed binary (Team ID `5HCL85FLGW`). The framework is Objective-C with a small Swift overlay; its public API is the 140-odd headers under `BRLMPrinterKit.framework/Headers` (`BRLMPrinterDriver`, `BRLMPrinterSearcher`, `BRLMChannel`, `BRLM*PrintSettings`, etc.).

Consumed by `envoy-ipad` via its local `PrinterKit` package, pinned with `exact:` to a tagged version. Bumping the SDK here is only useful once the tag exists and `envoy-ipad` is updated to point at it.

## Commands

- `swift build` does **not** work on macOS and never will. The only target is an iOS binary target, so SwiftPM reports "does not contain a buildable target". This is expected, not a bug.
- Verify the package resolves: `swift package describe`
- Inspect the vendored SDK version: `plutil -p Sources/BRLMPrinterKit.xcframework/ios-arm64/BRLMPrinterKit.framework/Info.plist | grep CFBundleShortVersionString`
- List slices: `plutil -p Sources/BRLMPrinterKit.xcframework/Info.plist`
- Check signature: `codesign -dv Sources/BRLMPrinterKit.xcframework`

To actually compile against the SDK, build a consuming iOS app or package (e.g. `envoy-ipad`), not this repo.

## Updating the SDK (the only real workflow)

Each release is one commit that replaces the whole xcframework and bumps the version in `README.md`, done on a branch and merged via PR, then tagged `vX.Y.Z` (semver, `v` prefix, matching Brother's `CFBundleShortVersionString`). Past releases: `v4.6.1`, `v4.12.0`, `v4.13.0`.

1. Download the new BT_Net SDK from Brother's developer page (link in README).
2. Replace `Sources/BRLMPrinterKit.xcframework` wholesale. Keep the path identical because `Package.swift` hardcodes it. Do not hand-edit anything inside the xcframework; the EULA forbids modifying the redistributable and the code signature would break.
3. Confirm the new xcframework still ships `ios-arm64` and `ios-arm64_x86_64-simulator` slices and a `PrivacyInfo.xcprivacy`.
4. Update the version line in `README.md`.
5. Commit, PR to `main`, then tag the merge commit `vX.Y.Z` and push the tag.
6. Bump the `exact:` pin in `envoy-ipad/PrinterKit/Package.swift`.

### Known state to be aware of

- Tag `v4.13.0` currently points at commit `a677f6c` on branch `ms/update-version4.13.0Binary`, which is **not merged to `main`**. `main` is still at `v4.12.0`. `envoy-ipad` already depends on `4.13.0` by that revision, so it works, but the tag is not reachable from `main`. Do not rebase or force-push that branch; the pinned revision hash must stay valid.
- An untracked, gitignored-by-accident `BRLMPrinterKit.xcframework/` sits at the repo root. It is a stale older build with `armv7`/`i386` slices and is **not** what the package uses. Ignore it; the real one is under `Sources/`.
- `Sources/BrotherPrinterKit/` is an empty leftover directory with no role.

## Licensing constraint

The SDK is redistributed under Brother's EULA (`EULA.pdf`, also reproduced in full in `README.md`). It may be incorporated unmodified into Envoy apps that print to Brother printers. Do not reverse-engineer, patch, or strip the binary, and do not add Brother logos or trademarks to app UI.
