//
//  GeneralPreferences.mm
//  MakeHuman
//
//  Created by hdusel on 17.08.09.
//  Copyright 2009 Tangerine-Software. All rights reserved.
//

#import "GeneralPreferences.h"

NSString *kUserDefaultsKeyExportPath = @"MHExportPath";
NSString *kUserDefaultsKeyModelPath  = @"MHModelPath";
NSString *kUserDefaultsKeyGrabPath   = @"MHGrabPath";
NSString *kUserDefaultsKeyRenderPath = @"MHRendermanPath";
NSString *kUserDefaultsKeyDocumentsPath = @"MHDocumentsPath";

@interface GeneralPreferences (Private)
+(void)createPathIfNotExists:(NSString*)inPath;
-(void)updateFileSelectPopUpButton:(NSPopUpButton*)inButton fromPath:(NSString*)inPath;

-(void)updateModelPath:(NSString*)inPath;
-(void)updateExportPath:(NSString*)inPath;
-(void)updateGrabPath:(NSString*)inPath;
-(void)updateRenderPath:(NSString*)inPath;
-(void)updateDocumentsPath:(NSString*)inPath;

-(void)setModelPath:(NSString*)inPath;
-(void)setExportPath:(NSString*)inPath;
-(void)setGrabPath:(NSString*)inPath;
-(void)setRenderPath:(NSString*)inPath;
-(void)setDocumentsPath:(NSString*)inPath;

+(NSString*)defaultModelPath;
+(NSString*)defaultExportPath;
+(NSString*)defaultGrabPath;
+(NSString*)defaultRenderPath;
+(NSString*)defaultDocumentsPath;
@end // @interface GeneralPreferences (Private)

@implementation GeneralPreferences

-(void)dealloc
{
    if (mFolderIcon) [mFolderIcon release];
    [super dealloc];
}

-(void)awakeFromNib
{
    [self setModelPath: [GeneralPreferences modelPath]];
    [self setExportPath:[GeneralPreferences exportPath]];
    [self setGrabPath:  [GeneralPreferences grabPath]];
    [self setRenderPath:[GeneralPreferences renderPath]];
    [self setDocumentsPath:[GeneralPreferences documentsPath]];
}

-(IBAction)actionResetPaths:(id)inSender
{
    [self setModelPath: [GeneralPreferences defaultModelPath]];
    [self setExportPath:[GeneralPreferences defaultExportPath]];
    [self setGrabPath:  [GeneralPreferences defaultGrabPath]];
    [self setRenderPath:[GeneralPreferences defaultRenderPath]];
    [self setDocumentsPath:[GeneralPreferences defaultDocumentsPath]];
}

-(IBAction)actionSelectModelPath:(NSPopUpButton*)inSender
{
    if (1 == [inSender indexOfSelectedItem])
    {
        NSOpenPanel *directorySelectPanel = [NSOpenPanel openPanel];
        [directorySelectPanel setCanChooseFiles:NO]; // Just directories may be selected
        [directorySelectPanel setCanChooseDirectories:YES]; // Just directories may be selected
        [directorySelectPanel setCanCreateDirectories:YES];

        NSInteger rc = [directorySelectPanel runModalForDirectory:[GeneralPreferences modelPath] file:nil types:nil];

        [inSender selectItemAtIndex:0];
        
        if (NSOKButton == rc)
        {
            NSString *selectedPath = [[directorySelectPanel filenames] objectAtIndex:0];
            [self setModelPath:selectedPath];
        }
    }
}

-(IBAction)actionSelectExportPath:(id)inSender
{
    if (1 == [inSender indexOfSelectedItem])
    {
        NSOpenPanel *directorySelectPanel = [NSOpenPanel openPanel];
        [directorySelectPanel setCanChooseFiles:NO]; // Just directories may be selected
        [directorySelectPanel setCanChooseDirectories:YES]; // Just directories may be selected
        [directorySelectPanel setCanCreateDirectories:YES];
        
        NSInteger rc = [directorySelectPanel runModalForDirectory:[GeneralPreferences exportPath] file:nil types:nil];
        
        [inSender selectItemAtIndex:0];
        
        if (NSOKButton == rc)
        {
            NSString *selectedPath = [[directorySelectPanel filenames] objectAtIndex:0];
            [self setExportPath:selectedPath];
        }
    }
}

-(IBAction)actionSelectGrabPath:(id)inSender
{
    if (1 == [inSender indexOfSelectedItem])
    {
        NSOpenPanel *directorySelectPanel = [NSOpenPanel openPanel];
        [directorySelectPanel setCanChooseFiles:NO]; // Just directories may be selected
        [directorySelectPanel setCanChooseDirectories:YES]; // Just directories may be selected
        [directorySelectPanel setCanCreateDirectories:YES];
        
        NSInteger rc = [directorySelectPanel runModalForDirectory:[GeneralPreferences grabPath] file:nil types:nil];
        
        [inSender selectItemAtIndex:0];
        
        if (NSOKButton == rc)
        {
            NSString *selectedPath = [[directorySelectPanel filenames] objectAtIndex:0];
            [self setGrabPath:selectedPath];
        }
    }
}

-(IBAction)actionSelectRenderPath:(id)inSender
{
    if (1 == [inSender indexOfSelectedItem])
    {
        NSOpenPanel *directorySelectPanel = [NSOpenPanel openPanel];
        [directorySelectPanel setCanChooseFiles:NO]; // Just directories may be selected
        [directorySelectPanel setCanChooseDirectories:YES]; // Just directories may be selected
        [directorySelectPanel setCanCreateDirectories:YES];
        
        NSInteger rc = [directorySelectPanel runModalForDirectory:[GeneralPreferences renderPath] file:nil types:nil];
        
        [inSender selectItemAtIndex:0];
        
        if (NSOKButton == rc)
        {
            NSString *selectedPath = [[directorySelectPanel filenames] objectAtIndex:0];
            [self setRenderPath:selectedPath];
        }
    }
}

-(IBAction)actionSelectDocumentsPath:(id)inSender
{
    if (1 == [inSender indexOfSelectedItem])
    {
        NSOpenPanel *directorySelectPanel = [NSOpenPanel openPanel];
        [directorySelectPanel setCanChooseFiles:NO]; // Just directories may be selected
        [directorySelectPanel setCanChooseDirectories:YES]; // Just directories may be selected
        [directorySelectPanel setCanCreateDirectories:YES];
        
        NSInteger rc = [directorySelectPanel runModalForDirectory:[GeneralPreferences documentsPath] file:nil types:nil];
        
        [inSender selectItemAtIndex:0];
        
        if (NSOKButton == rc)
        {
            NSString *selectedPath = [[directorySelectPanel filenames] objectAtIndex:0];
            [self setDocumentsPath:selectedPath];
        }
    }
}

-(BOOL) isResizable
{
	return NO;
}

+(NSString*)exportPath
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];

    NSString *s = [ud stringForKey:kUserDefaultsKeyExportPath];
    if (s == nil)
    {
        s = [GeneralPreferences defaultExportPath];
    }
    [GeneralPreferences createPathIfNotExists:s];
    return s;
}

+(NSString*)modelPath
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    
    NSString *s = [ud stringForKey:kUserDefaultsKeyModelPath];
    if (s == nil)
    {
        s = [GeneralPreferences defaultModelPath];
    }
    [GeneralPreferences createPathIfNotExists:s];
    return s;
}

+(NSString*)grabPath
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    
    NSString *s = [ud stringForKey:kUserDefaultsKeyGrabPath];
    if (s == nil)
    {
        s = [GeneralPreferences defaultGrabPath];
    }
    [GeneralPreferences createPathIfNotExists:s];
    return s;
}

+(NSString*)renderPath
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    
    NSString *s = [ud stringForKey:kUserDefaultsKeyRenderPath];
    if (s == nil)
    {
        s = [GeneralPreferences defaultRenderPath];
    }
    [GeneralPreferences createPathIfNotExists:s];
    return s;
}

+(NSString*)documentsPath
{
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    
    NSString *s = [ud stringForKey:kUserDefaultsKeyDocumentsPath];
    if (s == nil)
    {
        s = [GeneralPreferences defaultDocumentsPath];
    }
    [GeneralPreferences createPathIfNotExists:s];
    return s;
}

@end // @implementation GeneralPreferences



@implementation GeneralPreferences (Private)
+(void)createPathIfNotExists:(NSString*)inPath
{
    NSFileManager *fm = [NSFileManager defaultManager];
    BOOL rc = [fm createDirectoryAtPath:inPath 
                  withIntermediateDirectories:YES 
                  attributes:nil
                  error:nil];
    NSAssert1(rc == YES, @"could not create directory %@", inPath);
}

-(void)setModelPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mModelsPathsPUB fromPath:inPath];

    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setObject:inPath forKey:kUserDefaultsKeyModelPath];
    [ud synchronize];
}

-(void)setExportPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mExportsPathsPUB fromPath:inPath];
    
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setObject:inPath forKey:kUserDefaultsKeyExportPath];
    [ud synchronize];
}

-(void)setGrabPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mGrabPathPUB fromPath:inPath];
    
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setObject:inPath forKey:kUserDefaultsKeyGrabPath];
    [ud synchronize];
}

-(void)setRenderPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mRenderPathPUB fromPath:inPath];
    
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setObject:inPath forKey:kUserDefaultsKeyRenderPath];
    [ud synchronize];
}

-(void)setDocumentsPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mDocumentsPathPUB fromPath:inPath];
    
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setObject:inPath forKey:kUserDefaultsKeyDocumentsPath];
    [ud synchronize];
}

-(void)updateModelPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mModelsPathsPUB fromPath:inPath];
}

-(void)updateExportPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mExportsPathsPUB fromPath:inPath];
}

-(void)updateGrabPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mGrabPathPUB fromPath:inPath];
}

-(void)updateRenderPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mRenderPathPUB fromPath:inPath];
}

-(void)updateDocumentsPath:(NSString*)inPath
{
    [self updateFileSelectPopUpButton:mDocumentsPathPUB fromPath:inPath];
}

-(void)updateFileSelectPopUpButton:(NSPopUpButton*)inButton fromPath:(NSString*)inPath
{
    NSMenuItem *item = [inButton itemAtIndex:0];
    [item setTitle:inPath];
    
    NSImage *folderIcon = NULL;
    
    folderIcon = [[NSWorkspace sharedWorkspace] iconForFile:inPath];
    
    if (NULL == folderIcon)
    {
        // lazy alloc?
        if (NULL == mFolderIcon)
        {
            mFolderIcon = [NSImage imageNamed:@"folder.tiff"];
        }
        folderIcon = mFolderIcon;
    }
    [item setImage:folderIcon];
}

+(NSString*)defaultModelPath
{
    return [NSString stringWithFormat:@"%@/Documents/MakeHuman/models",  NSHomeDirectory()];
}

+(NSString*)defaultExportPath
{
    return [NSString stringWithFormat:@"%@/Documents/MakeHuman/exports",  NSHomeDirectory()];
}

+(NSString*)defaultGrabPath
{
    return [NSString stringWithFormat:@"%@/Desktop",  NSHomeDirectory()];
}

+(NSString*)defaultRenderPath
{
    return [NSString stringWithFormat:@"%@/Documents/MakeHuman/renderman",  NSHomeDirectory()];
}

+(NSString*)defaultDocumentsPath
{
    return [NSString stringWithFormat:@"%@/Documents/MakeHuman",  NSHomeDirectory()];
}

@end // @implementation GeneralPreferences (Private)

