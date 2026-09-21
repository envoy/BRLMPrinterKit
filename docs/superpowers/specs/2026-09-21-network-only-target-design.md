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
| References `EAAccessoryManager`, `EASession` | yes | **no** |
| Links `CoreBluetooth` | yes | yes |
| References `CBCentralManager`, `CBUUID` | yes | yes, identical |
| Minimum iOS | 14.0 | 14.0 |
| Built with | Swift 6.1 (effective-5.10) | Swift 6.1 (effective-5.10) |
| arm64 binary size | 4,068,856 B | 4,024,760 B |

The only meaningful difference is the dropped MFi surface. `Net` references no
`EAAccessoryManager` or `EASession`, so a consuming app needs no
`UISupportedExternalAccessoryProtocols` entry and no MFi declarations.

Brother's "Net" name is misleading and must not be repeated uncritically in our
docs. `Net` is **not** network-only: it references `CBCentralManager` and
`CBUUID` exactly as `BT_Net` does, so Bluetooth Low Energy is fully present. An
app built on the Net product still uses CoreBluetooth, so it still requires
`NSBluetoothAlwaysUsageDescription` and still shows the iOS Bluetooth
permission prompt. What it drops is MFi / Classic Bluetooth, nothing else.

`BRLMChannel` makes the split explicit. It offers three constructors, and the
MFi one is typed on `BRLMExternalAccessorySerialNumber`, so Brother's
"Bluetooth" channel *is* the ExternalAccessory path while BLE is separate:

| Constructor | `BRLMPrinterKit` | `BRLMPrinterKitNet` |
|---|---|---|
| `initWithWifiIPAddress:` | works | works |
| `initWithBLELocalName:` | works | works |
| `initWithBluetoothSerialNumber:` | works | compiles, cannot connect |

All three selectors are present in both binaries, because the headers are
identical and the Objective-C metadata ships either way. The MFi constructor
therefore still compiles and still returns a channel against the Net product;
only the machinery behind it is missing.

This is static evidence: linked frameworks, undefined symbols and selector
presence. BLE printing on the Net build has not been exercised against real
hardware, which is one thing the deferred validation should cover.

Nor does it remove Bluetooth from the API surface. The headers are identical, so
Bluetooth channel calls compile against the Net product and fail only at
runtime. The Net product is a linkage guarantee,
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

`Package.swift` in full, including the comments that carry the
mutual-exclusivity contract:

```swift
// swift-tools-version: 5.6
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

// A thin wrapper around Brother's closed-source Print SDK for iOS, vendored
// unmodified under Brother's EULA (see EULA.pdf). Downloads, release notes and
// API documentation:
// https://support.brother.com/g/s/es/dev/en/mobilesdk/ios/index.html
//
// This package vends two builds of that SDK:
//
//   BRLMPrinterKit     MFi/Classic Bluetooth + BLE + network (Brother's BT_Net)
//   BRLMPrinterKitNet  BLE + network, no MFi                 (Brother's Net)
//
// Depend on exactly one, never both. Both vend the module `BRLMPrinterKit` and
// the bundle identifier `com.brother.BRLMPrinterKit`, so linking both puts two
// copies of BRLMPrinterKit.framework in the app bundle and makes
// `import BRLMPrinterKit` ambiguous. SwiftPM cannot enforce this; it is on the
// consumer to pick one.
//
// The Net build differs only in dropping the ExternalAccessory link, so it needs
// no MFi accessory declarations. Despite Brother's name it is NOT network-only:
// it references CBCentralManager and CBUUID exactly as BT_Net does, so BLE still
// works and the app still needs NSBluetoothAlwaysUsageDescription.
//
// Neither product restricts the API at compile time. The headers are identical,
// so Bluetooth calls compile against BRLMPrinterKitNet and fail only at runtime.

let package = Package(
    name: "BRLMPrinterKit",
    platforms: [.iOS(.v14)],
    products: [
        // MFi + BLE + network. Mutually exclusive with BRLMPrinterKitNet.
        .library(
            name: "BRLMPrinterKit",
            targets: [
                "BRLMPrinterKit"
            ]),
        // BLE + network, no MFi. Mutually exclusive with BRLMPrinterKit.
        .library(
            name: "BRLMPrinterKitNet",
            targets: [
                "BRLMPrinterKitNet"
            ])
    ],
    targets: [
        .binaryTarget(
            name: "BRLMPrinterKit",
            path: "./Sources/BT_Net/BRLMPrinterKit.xcframework"),
        .binaryTarget(
            name: "BRLMPrinterKitNet",
            path: "./Sources/Net/BRLMPrinterKit.xcframework")
    ]
)
```

Product name `BRLMPrinterKit` is unchanged, so `envoy-ipad` is unaffected by the
move: it resolves by product name and the path is package-internal. Revisions
already pinned keep resolving because they point at existing commits.

A binary target's name need not match the framework inside it. The module a
consumer imports is `BRLMPrinterKit` for both products, regardless of target
name. Renaming or relocating the xcframework directory does not invalidate
Brother's signature; both were verified to still report `valid on disk` and
`satisfies its Designated Requirement` after being moved.

## Platform floor

The manifest currently declares no `platforms:` at all, so SwiftPM applies its
default minimum and nothing stops a consumer below the SDK's real floor from
resolving the package. The manifest gains:

```swift
platforms: [.iOS(.v14)],
```

14.0 is what the binaries actually support, measured on every slice of both
variants rather than taken from documentation:

| Slice | `platform` | `minos` |
|---|---|---|
| BT_Net `ios-arm64` | 2 (iOS) | 14.0 |
| BT_Net `ios-arm64_x86_64-simulator` | 7 (iOS simulator) | 14.0 |
| Net `ios-arm64` | 2 (iOS) | 14.0 |
| Net `ios-arm64_x86_64-simulator` | 7 (iOS simulator) | 14.0 |

The floor is declared as 14 because that is what the vendored binaries support,
not what any one consumer happens to target. `.iOS(.v14)` is valid at this
package's `swift-tools-version: 5.6`; it was confirmed to parse and to be
reported by `swift package describe` as `Name: ios / Version: 14.0`.

This does not break the existing consumer. `envoy-ipad`'s local `PrinterKit`
package declares `platforms: [.iOS(.v15), .macCatalyst(.v15)]`, already above
the new floor, and pins this package with `exact: "4.13.2"`. A consumer below
14 would now fail to resolve, which is the intent.

Declaring `platforms:` sets a minimum version; it cannot express "iOS only".
Platform exclusivity for a binary-only package comes from which slices the
xcframework ships, not from the manifest.

Noted and deliberately out of scope: `PrinterKit` declares `.macCatalyst(.v15)`,
but neither xcframework ships a Mac Catalyst slice. SwiftPM infers Catalyst
support from the iOS declaration, so this change neither causes nor fixes that
mismatch. It is pre-existing and should be raised separately against
`envoy-ipad`.

## Toolchain, and why `swift-tools-version` stays at 5.6

Brother builds the framework with Swift 6.1, which raises the question of
whether this package's `swift-tools-version: 5.6` should follow it. It should
not. The two numbers describe different things:

- `swift-compiler-version` in the `.swiftinterface` is the compiler Brother
  built with. It constrains the *consumer's* compiler, which must be able to
  type-check that interface.
- `swift-tools-version` is the minimum toolchain that can parse this manifest
  and the `PackageDescription` API level available inside it. It says nothing
  about the vendored binary and imposes nothing on consumer code.

Bumping it therefore would not express "needs Swift 6.1." It would only raise
the floor on which Xcode can read the manifest, an imprecise proxy, and no
tools-version means 6.1 specifically.

Nothing in the manifest needs more than 5.6 either: `platforms:` and
`.binaryTarget` both require only 5.3, and the manifest above was confirmed to
resolve at 5.6.

The interface is also far more conservative than "built with 6.1" suggests. The
entire Swift surface is one extension:

```swift
extension BRLMPrinterKit.BRLMPrinterDriver {
  public typealias PrintImageClosure = () -> Swift.Unmanaged<CoreGraphics.CGImage>?
  public func printImage(withClosures: [BRLMPrinterKit.BRLMPrinterDriver.PrintImageClosure],
                         settings: any BRLMPrinterKit.BRLMPrintSettingsProtocol) -> BRLMPrinterKit.BRLMPrintError
}
```

emitted with `swift-interface-format-version: 1.0`, `-swift-version 5` and
`-enable-library-evolution`. The only modern syntax in it is `any`, which
requires a 5.6 compiler. So the real consumer-compiler floor evidenced by the
interface is about 5.6, not 6.1, and the existing tools-version already matches
it by coincidence.

Raising the tools-version would be a breaking change for consumers on older
toolchains in exchange for no enforcement and no feature. The compiler floor
stays documented where `CLAUDE.md` already puts it: read from the
`swift-compiler-version` line of the shipped `.swiftinterface`.

## The mutual-exclusivity contract

Both products vend the same module name and the same bundle identifier. A
consumer must link exactly one. Linking both places two copies of
`BRLMPrinterKit.framework` in the app bundle and makes `import BRLMPrinterKit`
ambiguous.

SwiftPM cannot express or enforce this. There is no way to declare two products
as conflicting, and no build-time or resolution-time check will fire. Stating
the contract is therefore the whole of the mitigation, and it is stated in three
places, nearest first:

1. `Package.swift`, in a comment above `let package` and on each `.library`.
   This is the earliest point a consumer reads, and the only one that travels
   with the manifest they resolve.
2. `README.md`, for someone choosing a product.
3. `CLAUDE.md`, so the constraint survives future SDK updates.

## Documentation changes

- `Package.swift`: comments stating the mutual-exclusivity contract, what the
  Net build does and does not guarantee, and a link to Brother's SDK page, as
  shown in full above. `swift-tools-version` stays at 5.6.

- `CLAUDE.md`: replace the single hardcoded path with the two variant paths;
  restate the update workflow as two drops, from `libs/BT_Net/` and `libs/Net/`;
  add the mutual-exclusivity contract and what the Net build does and does not
  guarantee. The existing note about tag `v4.13.0` and branch
  `ms/update-version4.13.0Binary` is unrelated and stays as written.
- `README.md`: a products section with the comparison table, guidance on which
  to choose, and the mutual-exclusivity contract. Content specified below.

## README content

`README.md` gains a products section directly below the title, before the
licence reproduction. Exact content:

```markdown
## Products

This package vends two Brother builds of the same SDK. **Depend on exactly one,
never both.**

| | `BRLMPrinterKit` | `BRLMPrinterKitNet` |
|---|---|---|
| Brother build | `BT_Net` | `Net` |
| Vendored at | `Sources/BT_Net/` | `Sources/Net/` |
| Wi-Fi / network | yes | yes |
| Bluetooth Low Energy | yes | yes |
| MFi / Classic Bluetooth | yes | **no** |
| Links `ExternalAccessory` | yes | **no** |
| Links `CoreBluetooth` | yes | yes |
| Needs `UISupportedExternalAccessoryProtocols` | yes | no |
| Needs `NSBluetoothAlwaysUsageDescription` | yes | yes |
| Module you `import` | `BRLMPrinterKit` | `BRLMPrinterKit` |
| Bundle identifier | `com.brother.BRLMPrinterKit` | `com.brother.BRLMPrinterKit` |
| Public headers | 36 | 36, byte-identical |
| Minimum iOS | 14.0 | 14.0 |
| Slices | `ios-arm64`, `ios-arm64_x86_64-simulator` | same |
| arm64 binary | 4,068,856 B | 4,024,760 B |

Brother ships only these two builds. There is no Bluetooth-only build:
`BT_Net` means Bluetooth **and** network.

### Which to choose

Take `BRLMPrinterKitNet` if you do not talk to MFi / Classic Bluetooth printers.
It drops the `ExternalAccessory` link, so the app needs no MFi accessory
declarations and no `UISupportedExternalAccessoryProtocols` entry.

Despite the name, it is **not** network-only. It references `CBCentralManager`
and `CBUUID` exactly as `BT_Net` does, so Bluetooth Low Energy still works and
the app still needs `NSBluetoothAlwaysUsageDescription` and still shows the iOS
Bluetooth permission prompt. Only the MFi path is gone.

Take `BRLMPrinterKit` if you need MFi / Classic Bluetooth printers.

### Why exactly one

Both products vend the module `BRLMPrinterKit` and the bundle identifier
`com.brother.BRLMPrinterKit`. Depending on both puts two copies of
`BRLMPrinterKit.framework` in the app bundle and makes `import BRLMPrinterKit`
ambiguous. SwiftPM cannot declare two products as conflicting, so nothing fails
at resolution or build time; the contract is yours to keep.

Neither product restricts the API at compile time. The headers are identical
across both, so Bluetooth calls compile against `BRLMPrinterKitNet` and fail
only at runtime.
```

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

- `swift package describe` lists both products and both binary targets, and
  reports the platform as iOS 14.0.
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
