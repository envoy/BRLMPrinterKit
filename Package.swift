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
