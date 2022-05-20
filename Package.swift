// swift-tools-version: 5.6
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "BRLMPrinterKit",
    products: [
        .library(
            name: "BRLMPrinterKit",
            targets: [
                "BRLMPrinterKit"
            ])
    ],
    targets: [
        .binaryTarget(
            name: "BRLMPrinterKit",
            path: "./Sources/BRLMPrinterKit.xcframework")
    ]
)
