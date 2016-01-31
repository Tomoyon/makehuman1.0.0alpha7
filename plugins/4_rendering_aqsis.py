#!/usr/bin/python
# -*- coding: utf-8 -*-
# We need this for gui controls

import gui3d
import os
import sys
if 'nt' in sys.builtin_module_names:
    sys.path.append('./pythonmodules')
import subprocess
import mh2renderman

def which(program):
    """
    Checks whether a program exists, similar to http://en.wikipedia.org/wiki/Which_(Unix)
    """

    import os
    import sys
    
    if sys.platform == "win32" and not program.endswith(".exe"):
        program += ".exe"
        
    print "looking for", program
        
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            print exe_file
            if is_exe(exe_file):
                return exe_file

    return None

class AqsisTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Aqsis')

        self.sceneToRender = None

        optionsBox = self.addView(gui3d.GroupBox([10, 80, 9.0], 'Options', gui3d.GroupBoxStyle._replace(height=25+36*3+4+24*1+6)))
                                              
        #Sliders                            
        self.shadingRateSlider= optionsBox.addView(gui3d.Slider(value=2, min=0.1, max=10, label = "ShadingRate: %.2f"))
        self.samplesSlider= optionsBox.addView(gui3d.Slider(value=2, min=1.0, max=10, label = "Samples: %.2f"))
        self.skinOilSlider= optionsBox.addView(gui3d.Slider(value=0.3, min=0.0, max=10, label = "Skin Oil: %.2f"))
        
        #Buttons
        self.renderButton = optionsBox.addView(gui3d.Button('Render'))
            
        @self.shadingRateSlider.event
        def onChanging(value):
            self.app.settings['rendering_aqsis_shadingrate'] = value #Using global dictionary in app for global settings
            
        @self.samplesSlider.event
        def onChanging(value):
            self.app.settings['rendering_aqsis_samples'] = value
            
        @self.skinOilSlider.event
        def onChanging(value):
            self.app.settings['rendering_aqsis_oil'] = value
            
        @self.renderButton.event
        def onClicked(event):
            
            if not which("aqsis"):
                gui3d.app.prompt('Aqsis not found', 'You don\'t seem to have aqsis installed.', 'Download', 'Cancel', self.downloadAqsis)
                return
            
            if not self.sceneToRender:
                self.sceneToRender = mh2renderman.RMRScene(gui3d.app)
            self.buildShaders()
            self.sceneToRender.render()
            
    def buildShaders(self):
        
        shaders = ['hairpoly','skin2', 'envlight', 'skinbump', 'scatteringtexture', 'bakelightmap', 'eyeball', 'cornea', 'mixer', 'teeth']
        
        for shader in shaders:
            self.buildShader(shader)
        
    def buildShader(self, shader):
        
        srcPath = os.path.join('data/shaders/aqsis', shader + '.sl')
        dstPath = os.path.join(self.sceneToRender.usrShaderPath, shader + '.slx')
        
        if not os.path.exists(dstPath) or os.stat(srcPath).st_mtime > os.stat(dstPath).st_mtime:
            subprocess.Popen(u'aqsl %s -o "%s"' % (srcPath, dstPath), shell=True)
    
    def onShow(self, event):
        
        gui3d.TaskView.onShow(self, event)
        self.renderButton.setFocus()
        gui3d.app.prompt('Warning', 'The rendering is still an experimental feature since posing is not yet implemented.',
            'OK', helpId='alphaRenderWarning')

    def downloadAqsis(self):
    
        import webbrowser
        webbrowser.open('http://www.aqsis.org/')

def load(app):
    category = app.getCategory('Rendering')
    taskview = category.addView(AqsisTaskView(category))

def unload(app):
    pass


