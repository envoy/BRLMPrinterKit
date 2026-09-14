//
//  BRLMPrinterSearcher.h
//  BRLMPrinterKit
//
//  Copyright © 2022 Brother Industries. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <BRLMPrinterKit/BRLMPrinterSearchResult.h>
#import <BRLMPrinterKit/BRLMNetworkSearchOption.h>
#import <BRLMPrinterKit/BRLMBLESearchOption.h>

NS_ASSUME_NONNULL_BEGIN

@interface BRLMPrinterSearcher : NSObject
- (instancetype)init __unavailable;
- (instancetype)copy __unavailable;
+ (BRLMPrinterSearchResult *)startNetworkSearch:(nullable BRLMNetworkSearchOption *)searchOption callback:(nullable void (^)(BRLMChannel *channel))callback;
+ (BRLMPrinterSearchResult *)startNetworkSearch:(nullable BRLMNetworkSearchOption *)searchOption ipAddress:(NSString * _Nonnull)ipAddress;





+ (BRLMPrinterSearchResult *)startBluetoothSearch;
+ (BRLMPrinterSearchResult *)startBLESearch:(nullable BRLMBLESearchOption *)searchOption callback:(nullable void (^)(BRLMChannel *channel))callback;
+ (void)cancelNetworkSearch;
+ (void)cancelBLESearch;
+ (void)startBluetoothAccessorySearch:(void (^)(BRLMPrinterSearchResult *result))completionHandler;
@end

NS_ASSUME_NONNULL_END
