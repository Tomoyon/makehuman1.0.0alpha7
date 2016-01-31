#!/usr/bin/python
# -*- coding: utf-8 -*-
# We need this for gui controls

import gui3d
import humanmodifier

print 'Face imported'

class GroupBoxRadioButton(gui3d.RadioButton):
    def __init__(self, parent, group, label, groupBox, selected=False):
        gui3d.RadioButton.__init__(self, parent, group, label, selected, style=gui3d.ButtonStyle)
        self.groupBox = groupBox
        
    def onClicked(self, event):
        gui3d.RadioButton.onClicked(self, event)
        self.parent.parent.hideAllBoxes()
        self.groupBox.show()
        
class FaceSlider(humanmodifier.ModifierSlider):
    def __init__(self, parent, label, modifier):
        
        humanmodifier.ModifierSlider.__init__(self, parent, label=label, modifier=modifier)
        
class DetailSlider(humanmodifier.ModifierSlider):
    
    def __init__(self, parent, value, min, max, label, modifier):
        
        humanmodifier.ModifierSlider.__init__(self, parent, value, min, max, label, modifier=modifier)
        
class AsymmetricDetailModifier(humanmodifier.GenderAgeAsymmetricModifier):
    
    def __init__(self, template, parameterName, left, right, always=True):
    
        humanmodifier.GenderAgeAsymmetricModifier.__init__(self, template, parameterName, left, right, always)
        
    def getValue(self, human):
        
        return getattr(human, self.parameterName)
        
    def setValue(self, human, value):
        
        setattr(human, self.parameterName, value)
        humanmodifier.GenderAgeAsymmetricModifier.setValue(self, human, value)

class FaceTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Face')
        
        features = [
            ('eyes', ['data/targets/details/neutral_${gender}-${age}-eye%d.target' % i for i in xrange(1, 31)]),
            ('nose', ['data/targets/details/neutral_${gender}-${age}-nose%d.target' % i for i in xrange(1, 13)]),
            ('ears', ['data/targets/details/${gender}-${age}-ears%d.target' % i for i in xrange(1, 9)]),
            ('mouth', ['data/targets/details/neutral_${gender}-${age}-mouth%d.target' % i for i in xrange(1, 14)]),
            ('jaw', ['data/targets/details/${gender}-${age}-jaw%d.target' % i for i in xrange(1, 8)]),
            ('head', ['data/targets/details/neutral_${gender}-${age}-head%d.target' % i for i in xrange(1, 9)]),
            ]

        y = 80
        
        self.groupBoxes = []
        self.radioButtons = []
        self.sliders = []
        
        self.modifiers = {}
        
        self.categoryBox = gui3d.GroupBox(self, [650, y, 9.0], 'Category', gui3d.GroupBoxStyle._replace(height=25+24*sum([(len(templates[1])/10 + (len(templates[1])%10>0)) for templates in features])+6))
        y += 25
        
        for name, templates in features:
            
            for index, template in enumerate(templates):
                
                if index % 10 == 0:
                    
                    if len(templates) <= 10:
                        title = name.capitalize()
                    else:
                        title = '%s %d' % (name.capitalize(), index / 10 + 1)
                        
                    # Create box
                    box = gui3d.GroupBox(self, [10, 80, 9.0], title, gui3d.GroupBoxStyle._replace(height=25+36*min(len(templates)-index, 10)+6))
                    self.groupBoxes.append(box)
                    
                    # Create radiobutton
                    radio = GroupBoxRadioButton(self.categoryBox, self.radioButtons, title, box, selected=len(self.radioButtons) == 0)
                    y += 24
            
                # Create sliders
                modifier = humanmodifier.GenderAgeModifier(template)
                self.modifiers['%s%d' % (name, index + 1)] = modifier
                slider = FaceSlider(box, '%s %d' % (name.capitalize(), index + 1), modifier)
                self.sliders.append(slider)
                
        y += 16

        self.hideAllBoxes()
        self.groupBoxes[0].show()
        
        self.headAgeModifier = AsymmetricDetailModifier('data/targets/details/${gender}-${age}-head-age${headAge}.target', 'headAge', '1', '2', False)
        self.faceAngleModifier = humanmodifier.Modifier('data/targets/details/facial-angle1.target', 'data/targets/details/facial-angle2.target')

        self.headBox = gui3d.GroupBox(self, [650, y, 9.0], 'Head', gui3d.GroupBoxStyle._replace(height=25+36*2+6))
        self.sliders.append(DetailSlider(self.headBox, 0.0, -1.0, 1.0, "Age", self.headAgeModifier))
        self.sliders.append(DetailSlider(self.headBox, 0.0, -1.0, 1.0, "Face angle", self.faceAngleModifier))
        
    def hideAllBoxes(self):
        
        for box in self.groupBoxes:
            
            box.hide()
    
    def onShow(self, event):

        gui3d.TaskView.onShow(self, event)
        
        self.app.setFaceCamera()
        
        for slider in self.sliders:
            slider.update()
            
    def onResized(self, event):
        
        self.categoryBox.setPosition([event.width - 150, self.categoryBox.getPosition()[1], 9.0])
        self.headBox.setPosition([event.width - 150, self.headBox.getPosition()[1], 9.0])
        
    def onHumanChanged(self, event):
        
        human = event.human
        
        for slider in self.sliders:
            value = slider.modifier.getValue(human)
            if value:
                slider.modifier.setValue(human, value)
                
    def loadHandler(self, human, values):
        
        if values[0] == 'face':
            modifier = self.modifiers.get(values[1], None)
            if modifier:
                modifier.setValue(human, float(values[2]))
        elif values[0] == 'headAge':
            self.headAgeModifier.setValue(human, float(values[1]))
        elif values[0] == 'faceAngle':
            self.faceAngleModifier.setValue(human, float(values[1]))
       
    def saveHandler(self, human, file):
        
        for name, modifier in self.modifiers.iteritems():
            value = modifier.getValue(human)
            if value:
                file.write('face %s %f\n' % (name, value))
        
        file.write('headAge %f\n' % self.headAgeModifier.getValue(human))
        file.write('faceAngle %f\n' % self.faceAngleModifier.getValue(human))

def load(app):
    category = app.getCategory('Modelling')
    taskview = category.addView(FaceTaskView(category))
    
    app.addLoadHandler('face', taskview.loadHandler)
    app.addLoadHandler('headAge', taskview.loadHandler)
    app.addLoadHandler('faceAngle', taskview.loadHandler)
    app.addSaveHandler(taskview.saveHandler)

    print 'Face loaded'

def unload(app):
    pass


