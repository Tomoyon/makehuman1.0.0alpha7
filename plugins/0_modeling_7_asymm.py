import os.path
#!/usr/bin/python
# -*- coding: utf-8 -*-
# We need this for gui controls

import gui3d
import os
import humanmodifier
import events3d

class AssymSlider(gui3d.Slider):
    
    def __init__(self, bodypart, label):
        gui3d.Slider.__init__(self, value=0.0, min=-1.0, max=1.0, label=label)
        self.bodypart = bodypart
        
    def onChange(self, value):
        self.parent.parent.changeValue(self.bodypart, value)
        
    def onChanging(self, value):
        self.parent.parent.changeValue(self.bodypart, value, True)

class AsymmTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Asymmetry')

        #Sliders
        self.leftBox = self.addView(gui3d.GroupBox([10, 80, 9.0], 'Face', gui3d.GroupBoxStyle._replace(height=25+36*9+6)))
        self.asymmBrowSlider = self.leftBox.addView(AssymSlider("brown", "Brow asymmetry"))
        self.asymmCheekSlider = self.leftBox.addView(AssymSlider("cheek", "Cheek asymmetry"))
        self.asymmEarsSlider = self.leftBox.addView(AssymSlider("ear", "Ears asymmetry"))
        self.asymmEyeSlider = self.leftBox.addView(AssymSlider("eye", "Eye asymmetry"))
        self.asymmJawSlider = self.leftBox.addView(AssymSlider("jaw", "Jaw asymmetry"))
        self.asymmMouthSlider = self.leftBox.addView(AssymSlider("mouth", "Mouth asymmetry"))
        self.asymmNoseSlider = self.leftBox.addView(AssymSlider("nose", "Nose asymmetry"))
        self.asymmTempleSlider = self.leftBox.addView(AssymSlider("temple", "Temple asymmetry"))
        self.asymmTopSlider = self.leftBox.addView(AssymSlider("top", "Top asymmetry"))

        self.rightBox = self.addView(gui3d.GroupBox([650, 80, 9.0], 'Body', gui3d.GroupBoxStyle._replace(height=25+36*2+6)))
        self.asymmTrunkSlider = self.rightBox.addView(AssymSlider("trunk", "Trunk asymmetry"))
        self.asymmBreastSlider = self.rightBox.addView(AssymSlider("breast", "Breast asymmetry"))

        #Get a list with all targes (complete with path) used in asymm library
        self.asymmDataPath = "data/targets/asym/"
        self.asymmTargets = []
        for f in os.listdir(self.asymmDataPath):
            if os.path.isfile(os.path.join(self.asymmDataPath, f)):
                self.asymmTargets.append(os.path.join(self.asymmDataPath, f))

        #The human mesh
        self.human = gui3d.app.selectedHuman

        #Random factor from Slider
        self.randomVal = 0.5
        
        # Modifiers
        self.modifiers = {}
        for bodypart in ["brown", "cheek","ear","eye", "jaw", "mouth","nose","temple","top","trunk","breast"]:
            self.getModifiers(bodypart)
        
        # Undo memory
        self.before = None

    def changeValue(self, bodyPartName, value, realtime=False):
        """
        This function apply the targets, and inform the undo system about the changes.
        @return: None
        @type  bodyPartName: String
        @param bodyPartName: Name of the body part to asymmetrise
        @type  value: Float
        @param value: The amount of asymmetry
        """
        if realtime:
            if not self.before:
                self.before = self.getTargetsAndValues(bodyPartName)
                
            self.calcAsymm(value,bodyPartName, realtime)
            self.human.updateProxyMesh()
        else:
            self.calcAsymm(value,bodyPartName, realtime)
            self.human.applyAllTargets(gui3d.app.progress)
            
            after = self.getTargetsAndValues(bodyPartName)
            
            gui3d.app.did(humanmodifier.DetailAction(self.human, self.before, after, self.syncSliders))
            
            self.before = None

    def buildListOfTargetPairs(self, name):
        """
        This function scan all targets and build a list of list:
        [[target1-left,target1-right],...,[targetN-left,targetN-right]]
        @return: List of lists
        @type  name: String
        @param targets: Name of the body part to asymmetrise
        """
        pairs = []
        for f in self.asymmTargets:
            if name in f:
                dirPath = os.path.dirname(f)
                targetName = os.path.splitext(os.path.basename(f))[0]
                prefix = targetName[:-2]
                suffix = targetName[-2:]
                if suffix == "-r":
                    f2 = dirPath + "/" + prefix + "-l.target"
                    pair = [f,f2]
                    pairs.append(pair)
        return pairs


    def getTargetsAndValues(self, bodypart):
        """
        This function return a dictionary with "targetPath:val" items, getting them
        from the human details stack.
        It's used to get both "before" and "after" dictionaries.
        @return: Dictionary
        @type  targets: List
        @param targets: List of targets to get
        """
        modifiers = self.getModifiers(bodypart)
           
        targetsAndValues = {}
        for modifier in modifiers:                
            targetsAndValues[modifier.left] = self.human.getDetail(modifier.left)
            targetsAndValues[modifier.right] = self.human.getDetail(modifier.right)
        return targetsAndValues

    def calcAsymm(self, value, bodypart, realtime=False):
            """
            This function load all asymmetry targets for the specified part of body
            (for example brown, eyes, etc..) and return a dictionary with
            the applied targets, used as "after" parameter in undo system
            @return: Dictionary
            @type  value: Float
            @param value: The amount of asymmetry
            @type  bodypart: String
            @param bodypart: The name of part to asymmetrize.
            """
            modifiers = self.getModifiers(bodypart)
            human = gui3d.app.selectedHuman
           
            for modifier in modifiers:
                if realtime:
                    modifier.updateValue(human, value)
                else:
                    modifier.setValue(human, value)
                
    def getModifiers(self, bodypart):
        modifiers = self.modifiers.get(bodypart, None)
        if not modifiers:
            modifiers = []
            targets = self.buildListOfTargetPairs(bodypart)
            for pair in targets:
                modifier = humanmodifier.Modifier(pair[0], pair[1])
                modifiers.append(modifier)
            self.modifiers[bodypart] = modifiers
        return modifiers
        
    def getSliderValue(self, bodypart):
        modifiers = self.modifiers[bodypart]
        if modifiers:
            human = gui3d.app.selectedHuman
            return modifiers[0].getValue(human)
        else:
            return 0.0
            
    def onShow(self, event):

        gui3d.TaskView.onShow(self, event)
        self.asymmBrowSlider.setFocus()
        self.syncSliders()
        
    def onResized(self, event):
        
        self.rightBox.setPosition([event.width - 150, self.rightBox.getPosition()[1], 9.0])
            
    def syncSliders(self):
        self.asymmBrowSlider.setValue(self.getSliderValue('brown'))
        self.asymmCheekSlider.setValue(self.getSliderValue('cheek'))
        self.asymmEarsSlider.setValue(self.getSliderValue('ear'))
        self.asymmEyeSlider.setValue(self.getSliderValue('eye'))
        self.asymmJawSlider.setValue(self.getSliderValue('jaw'))
        self.asymmMouthSlider.setValue(self.getSliderValue('mouth'))
        self.asymmNoseSlider.setValue(self.getSliderValue('nose'))
        self.asymmTempleSlider.setValue(self.getSliderValue('temple'))
        self.asymmTopSlider.setValue(self.getSliderValue('top'))
        self.asymmTrunkSlider.setValue(self.getSliderValue('trunk'))
        self.asymmBreastSlider.setValue(self.getSliderValue('breast'))
        
    def onKeyDown(self, event):

        # Undo redo
        if event.key == events3d.SDLK_y:
            gui3d.app.redo()
        elif event.key == events3d.SDLK_z:
            gui3d.app.undo()
            
        gui3d.TaskView.onKeyDown(self, event)

def load(app):
    """
    Plugin load function, needed by design.
    """
    category = app.getCategory('Modelling')
    taskview = category.addView(AsymmTaskView(category))
    
    print 'Asymmetry loaded'

def unload(app):
    pass
