//
//  GeneralPreferences.h
//  MakeHuman
//
//  Created by hdusel on 16.08.09.
//  Copyright 2009 Tangerine-Software. All rights reserved.
//

#import <Cocoa/Cocoa.h>
#import "NSPreferences.h"
        
@class SUUpdater;

@interface GeneralPreferences : NSPreferencesModule 
{
    IBOutlet NSPopUpButton *mModelsPathsPUB;
    IBOutlet NSPopUpButton *mExportsPathsPUB;
    IBOutlet NSPopUpButton *mGrabPathPUB;
    IBOutlet NSPopUpButton *mRenderPathPUB;
    IBOutlet NSPopUpButton *mDocumentsPathPUB;

@private
    NSImage *mFolderIcon;
}


-(IBAction)actionResetPaths:(id)inSender;
-(IBAction)actionSelectModelPath:(NSPopUpButton*)inSender;
-(IBAction)actionSelectExportPath:(id)inSender;
-(IBAction)actionSelectGrabPath:(id)inSender;
-(IBAction)actionSelectRenderPath:(id)inSender;
-(IBAction)actionSelectDocumentsPath:(id)inSender;

+(NSString*)exportPath;
+(NSString*)modelPath;
+(NSString*)grabPath;
+(NSString*)renderPath;
+(NSString*)documentsPath;

@end
