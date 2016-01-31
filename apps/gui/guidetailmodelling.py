#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    http://code.google.com/p/makehuman/

**Authors:**           Marc Flerackers

**Copyright(c):**      MakeHuman Team 2001-2011

**Licensing:**         GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)

**Coding Standards:**  See http://sites.google.com/site/makehumandocs/developers-guide

Abstract
--------

TODO
"""

import events3d
import gui3d
import humanmodifier
from operator import mul
from string import Template
import re
import os

class RangeDetailModifier(humanmodifier.GenderAgeRangeModifier):
    
    def __init__(self, template, parameterName, parameterRange, always=True):
    
        humanmodifier.GenderAgeRangeModifier.__init__(self, template, parameterName, parameterRange, always)
        
    def getValue(self, human):
        
        return getattr(human, self.parameterName)
        
    def setValue(self, human, value):
        
        setattr(human, self.parameterName, value)
        humanmodifier.GenderAgeRangeModifier.setValue(self, human, value)
        
class AsymmetricDetailModifier(humanmodifier.GenderAgeAsymmetricModifier):
    
    def __init__(self, template, parameterName, left, right, always=True):
    
        humanmodifier.GenderAgeAsymmetricModifier.__init__(self, template, parameterName, left, right, always)
        
    def getValue(self, human):
        
        return getattr(human, self.parameterName)
        
    def setValue(self, human, value):
        
        setattr(human, self.parameterName, value)
        humanmodifier.GenderAgeAsymmetricModifier.setValue(self, human, value)

class StomachModifier(AsymmetricDetailModifier):
    # This needs a custom modifier because tone and weight also need to be included
    
    def __init__(self):
    
        AsymmetricDetailModifier.__init__(self, 'data/targets/details/${gender}-${age}-${tone}-${weight}-stomach${stomach}.target', 'stomach', '1', '2', False)
        
    def expandTemplate(self, targets):
        
        # Build target list of (targetname, [factors])
        targets = [(Template(target[0]).safe_substitute(gender=value), target[1] + [value]) for target in targets for value in ['female', 'male']]
        targets = [(Template(target[0]).safe_substitute(age=value), target[1] + [value]) for target in targets for value in ['child', 'young', 'old']]
        targets = [(Template(target[0]).safe_substitute(tone=value), target[1] + [value or 'averageTone']) for target in targets for value in ['flaccid', '', 'muscle']]
        targets = [(Template(target[0]).safe_substitute(weight=value), target[1] + [value or 'averageWeight']) for target in targets for value in ['light', '', 'heavy']]
        targets = [(Template(target[0]).safe_substitute({self.parameterName:value}), target[1] + [value]) for target in targets for value in [self.left, self.right]]

        # Cleanup multiple hyphens and remove a possible hyphen before a dot.
        doubleHyphen = re.compile(r'-+')
        hyphenDot = re.compile(r'-\.')
        
        targets = [(re.sub(hyphenDot, '.', re.sub(doubleHyphen, '-', target[0])), target[1]) for target in targets]
        
        return targets
        
    def getFactors(self, human, value):
        
        factors = {
            'female': human.femaleVal,
            'male': human.maleVal,
            'child': human.childVal,
            'young': human.youngVal,
            'old': human.oldVal,
            'flaccid':human.flaccidVal,
            'muscle':human.muscleVal,
            'averageTone':1.0 - (human.flaccidVal + human.muscleVal),
            'light':human.underweightVal,
            'heavy':human.overweightVal,
            'averageWeight':1.0 - (human.underweightVal + human.overweightVal),
            self.left: -min(value, 0.0),
            self.right: max(0.0, value)
        }
        
        return factors
        
class BreastsModifier(humanmodifier.GenericModifier):
    # This needs a custom modifier because it has two extra dimensions
    
    def __init__(self):
    
        self.breastSizes = ['breastSize%d' % size for size in xrange(1, 3)]
        humanmodifier.GenericModifier.__init__(self,
            'data/targets/breast/female-${age}-${tone}-${weight}-cup${breastSize}-firmness${breastFirmness}.target')
            
    def setValue(self, human, value):
    
        value = self.clampValue(value)
        factors = self.getFactors(human, value)
        
        for target in self.targets:
            human.setDetail(target[0], human.femaleVal * reduce(mul, [factors[factor] for factor in target[1]]))
        
    def expandTemplate(self, targets):
        
        # Build target list of (targetname, [factors])
        targets = [(Template(target[0]).safe_substitute(age=value), target[1] + [value]) for target in targets for value in ['child', 'young', 'old']]
        targets = [(Template(target[0]).safe_substitute(tone=value), target[1] + [value or 'averageTone']) for target in targets for value in ['flaccid', '', 'muscle']]
        targets = [(Template(target[0]).safe_substitute(weight=value), target[1] + [value or 'averageWeight']) for target in targets for value in ['light', '', 'heavy']]
        targets = [(Template(target[0]).safe_substitute(breastFirmness=value), target[1] + ['breastFirmness%d' % value]) for target in targets for value in xrange(0, 2)]
        targets = [(Template(target[0]).safe_substitute(breastSize=value), target[1] + ['breastSize%d' % value]) for target in targets for value in xrange(1, 3)]

        # Cleanup multiple hyphens and remove a possible hyphen before a dot.
        doubleHyphen = re.compile(r'-+')
        hyphenDot = re.compile(r'-\.')
        
        targets = [(re.sub(hyphenDot, '.', re.sub(doubleHyphen, '-', target[0])), target[1]) for target in targets]
        
        return targets
        
    def getFactors(self, human, value):
        
        factors = {
            'child': human.childVal,
            'young': human.youngVal,
            'old': human.oldVal,
            'flaccid':human.flaccidVal,
            'muscle':human.muscleVal,
            'averageTone':1.0 - (human.flaccidVal + human.muscleVal),
            'light':human.underweightVal,
            'heavy':human.overweightVal,
            'averageWeight':1.0 - (human.underweightVal + human.overweightVal),
            'breastFirmness0': 1.0 - human.breastFirmness,
            'breastFirmness1': human.breastFirmness,
            'breastSize1': -min(human.breastSize, 0.0),
            'breastSize2': max(0.0, human.breastSize)
        }
        '''
        for factor in self.breastSizes:
            factors[factor] = 0.0
        
        v = human.breastSize * (len(self.breastSizes) - 1)
        index = int(math.floor(v))
        v = v - index
        factors[self.breastSizes[index]] = 1.0 - v
        if index+1 < len(self.breastSizes):
            factors[self.breastSizes[index+1]] = v
        '''
        return factors

class BreastSizeModifier(BreastsModifier):
    
    def __init__(self):
        
        BreastsModifier.__init__(self)
        
    def getValue(self, human):
        
        return human.breastSize
        
    def setValue(self, human, value):
        
        human.breastSize = value
        BreastsModifier.setValue(self, human, value)
        
    def clampValue(self, value):
        return max(0.0, min(1.0, value))
        
class BreastFirmnessModifier(BreastsModifier):
    
    def __init__(self):
        
        BreastsModifier.__init__(self)
    
    def getValue(self, human):
        
        return human.breastFirmness
        
    def setValue(self, human, value):
        
        human.breastFirmness = value
        BreastsModifier.setValue(self, human, value)
        
    def clampValue(self, value):
        return max(0.0, min(1.0, value))

class DetailTool(events3d.EventHandler):

    def __init__(self, app, micro, left, right):
        gui3d.app = app
        self.micro = micro
        self.left = left
        self.before = None
        self.right = right
        self.modifier = None
        self.symmetryModifier = None
        self.selectedGroups = []

    def onMouseDown(self, event):
        human = gui3d.app.selectedHuman

    # Find the target name

        if self.micro:
            folder = 'data/targets/microdetails/'
            part = gui3d.app.selectedGroup.name
        else:
            folder = 'data/targets/details/'
            part = human.getPartNameForGroupName(gui3d.app.selectedGroup.name)

    # Find the targets

        leftTarget = '%s%s%s.target' % (folder, part, self.left)
        rightTarget = '%s%s%s.target' % (folder, part, self.right)

        self.modifier = None
        if not (leftTarget and rightTarget):
            print 'No targets available'
            return

        self.modifier = humanmodifier.Modifier(leftTarget, rightTarget)

        # Save the state

        self.before = {}
        self.before[leftTarget] = human.getDetail(leftTarget)
        self.before[rightTarget] = human.getDetail(rightTarget)

        # Add symmetry targets if needed

        self.symmetryModifier = None
        if human.symmetryModeEnabled:
            symmetryPart = human.getSymmetryPart(part)
            if symmetryPart:
                if self.left.find('trans-in') != -1 or self.left.find('trans-out') != -1:
                    leftSymmetryTarget = '%s%s%s.target' % (folder, symmetryPart, self.right)
                    rightSymmetryTarget = '%s%s%s.target' % (folder, symmetryPart, self.left)
                else:
                    leftSymmetryTarget = '%s%s%s.target' % (folder, symmetryPart, self.left)
                    rightSymmetryTarget = '%s%s%s.target' % (folder, symmetryPart, self.right)
                self.symmetryModifier = humanmodifier.Modifier(leftSymmetryTarget, rightSymmetryTarget)

                # Save the state
                
                self.before[leftSymmetryTarget] = human.getDetail(leftSymmetryTarget)
                self.before[rightSymmetryTarget] = human.getDetail(rightSymmetryTarget)
                
        if human.isSubdivided():
            human.meshData.setVisibility(1)
            human.getSubdivisionMesh(False).setVisibility(0)

    def onMouseDragged(self, event):
        if not self.modifier:
            print 'No modifier available'
            
        human = gui3d.app.selectedHuman

        # check which vector we need to check

        if abs(event.dx) > abs(event.dy):
            d = event.dx
        else:
            d = -event.dy

        if d == 0.0:
            return

        value = d / 20.0

        self.modifier.updateValue(human, self.modifier.getValue(human) + value)
        if self.symmetryModifier:
            self.symmetryModifier.updateValue(human, self.modifier.getValue(human))

    def onMouseUp(self, event):
        human = gui3d.app.selectedHuman

        # Recalculate

        human.applyAllTargets(gui3d.app.progress)
        
        if human.isSubdivided():
            human.meshData.setVisibility(0)
            human.getSubdivisionMesh(False).setVisibility(1)

        # Build undo item

        after = {}

        for target in self.before.iterkeys():
            after[target] = human.getDetail(target)

        gui3d.app.did(humanmodifier.DetailAction(human, self.before, after))

    def onMouseMoved(self, event):
        human = gui3d.app.selectedHuman

        groups = []

        if self.micro:
            groups.append(event.group)
        else:
            part = human.getPartNameForGroupName(event.group.name)
            for g in human.mesh.faceGroups:
                if part in g.name:
                    groups.append(g)
                    if human.symmetryModeEnabled:
                        sg = human.getSymmetryGroup(g)
                        if sg:
                            groups.append(sg)

        for g in self.selectedGroups:
            if g not in groups:
                g.setColor([255, 255, 255, 255])

        for g in groups:
            if g not in self.selectedGroups:
                g.setColor([0, 255, 0, 255])

        self.selectedGroups = groups
        gui3d.app.redraw()

    def onMouseExited(self, event):
        for g in self.selectedGroups:
            g.setColor([255, 255, 255, 255])

        self.selectedGroups = []
        gui3d.app.redraw()


class Detail3dTool(events3d.EventHandler):

    def __init__(self, app, micro, type):
        gui3d.app = app
        self.micro = micro
        self.type = type
        if type == 'scale':
            self.x = DetailTool(app, micro, '-scale-horiz-decr', '-scale-horiz-incr')
            self.y = DetailTool(app, micro, '-scale-vert-decr', '-scale-vert-incr')
            self.z = DetailTool(app, micro, '-scale-depth-decr', '-scale-depth-incr')
        elif type == 'translation':
            self.x = DetailTool(app, micro, '-trans-in', '-trans-out')
            self.y = DetailTool(app, micro, '-trans-down', '-trans-up')
            self.z = DetailTool(app, micro, '-trans-backward', '-trans-forward')
        self.selectedGroups = []

    def onMouseDown(self, event):
        self.x.onMouseDown(event)
        self.y.onMouseDown(event)
        self.z.onMouseDown(event)

    def getCameraFraming(self):
        """
    This method return a label to identify the main
    camera framing (front, back. side, top) depending
    the camera rotations.
    
    **Parameters:** This method has no parameters.
    """

    # TODO: top and botton view

        rot = gui3d.app.selectedHuman.getRotation()

        xRot = rot[0] % 360
        yRot = rot[1] % 360

        if 315 < yRot <= 360 or 0 <= yRot < 45:
            return 'FRONTAL_VIEW'
        if 145 < yRot < 235:
            return 'BACK_VIEW'
        if 45 < yRot < 145:
            return 'LEFT_VIEW'
        if 235 < yRot < 315:
            return 'RIGHT_VIEW'

    def onMouseDragged(self, event):
        viewType = self.getCameraFraming()

        if viewType == 'FRONTAL_VIEW':
            d = event.dy
            event.dy = 0.0
            self.x.onMouseDragged(event)
            event.dy = d
            d = event.dx
            event.dx = 0.0
            self.y.onMouseDragged(event)
            event.dx = d
        elif viewType == 'BACK_VIEW':
            d = event.dy
            event.dy = 0.0
            event.dx = -event.dx
            self.x.onMouseDragged(event)
            event.dy = d
            d = -event.dx
            event.dx = 0.0
            self.y.onMouseDragged(event)
            event.dx = d
        elif viewType == 'LEFT_VIEW':
            d = event.dy
            event.dy = 0.0
            self.z.onMouseDragged(event)
            event.dy = d
            d = event.dx
            event.dx = 0.0
            self.y.onMouseDragged(event)
            event.dx = d
        elif viewType == 'RIGHT_VIEW':
            d = event.dy
            event.dy = 0.0
            event.dx = -event.dx
            self.z.onMouseDragged(event)
            event.dy = d
            d = -event.dx
            event.dx = 0.0
            self.y.onMouseDragged(event)
            event.dx = d

    def onMouseUp(self, event):
        human = gui3d.app.selectedHuman

    # Recalculate

        human.applyAllTargets(gui3d.app.progress)
        
        if human.isSubdivided():
            human.meshData.setVisibility(0)
            human.getSubdivisionMesh(False).setVisibility(1)

    # Add undo item

        before = {}

        for (target, value) in self.x.before.iteritems():
            before[target] = value
        for (target, value) in self.y.before.iteritems():
            before[target] = value
        for (target, value) in self.z.before.iteritems():
            before[target] = value

        after = {}

        for target in before.iterkeys():
            after[target] = human.getDetail(target)

        gui3d.app.did(humanmodifier.DetailAction(human, before, after))

    def onMouseMoved(self, event):
        human = gui3d.app.selectedHuman

        groups = []

        if self.micro:
            print(event.group)
            groups.append(event.group)
            if human.symmetryModeEnabled:
                sg = human.getSymmetryGroup(event.group)
                if sg:
                    groups.append(sg)
        else:
            part = human.getPartNameForGroupName(event.group.name)
            for g in human.mesh.faceGroups:
                if part in g.name:
                    groups.append(g)
                    if human.symmetryModeEnabled:
                        sg = human.getSymmetryGroup(g)
                        if sg:
                            groups.append(sg)

        for g in self.selectedGroups:
            if g not in groups:
                g.setColor([255, 255, 255, 255])

        for g in groups:
            if g not in self.selectedGroups:
                g.setColor([0, 255, 0, 255])

        self.selectedGroups = groups
        gui3d.app.redraw()

    def onMouseExited(self, event):
        for g in self.selectedGroups:
            g.setColor([255, 255, 255, 255])

        self.selectedGroups = []
        gui3d.app.redraw()

class DetailSlider(humanmodifier.ModifierSlider):
    
    def __init__(self, value, min, max, label, modifier):
        
        humanmodifier.ModifierSlider.__init__(self, value, min, max, label, modifier=modifier)

class DetailModelingTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Detail modelling', label='Micro')
        self.tool = None
        
        self.modifiers = {}
        self.oldModifiers = {}
        
        self.modifiers['genitals'] = AsymmetricDetailModifier('data/targets/details/genitals_${gender}_${genitals}_${age}.target', 'genitals', 'feminine', 'masculine', False)
        
        self.modifiers['breastSize'] = BreastSizeModifier()
        self.modifiers['breastFirmness'] = BreastFirmnessModifier()
        self.modifiers['breastPosition'] = humanmodifier.Modifier('data/targets/breast/breast-down.target',
            'data/targets/breast/breast-up.target')
        self.modifiers['breastDistance'] = humanmodifier.Modifier('data/targets/breast/breast-dist-min.target',
            'data/targets/breast/breast-dist-max.target')
        self.modifiers['breastPoint'] = humanmodifier.Modifier('data/targets/breast/breast-point-min.target',
            'data/targets/breast/breast-point-max.target')
        
        self.oldModifiers['nose'] = RangeDetailModifier('data/targets/details/neutral_${gender}-${age}-nose${nose}.target', 'nose', xrange(1, 13), False)
        self.oldModifiers['mouth'] = RangeDetailModifier('data/targets/details/neutral_${gender}-${age}-mouth${mouth}.target', 'mouth', xrange(1, 14), False)
        self.oldModifiers['eyes'] = RangeDetailModifier('data/targets/details/neutral_${gender}-${age}-eye${eyes}.target', 'eyes', xrange(1, 31), False)
        self.oldModifiers['ears'] = RangeDetailModifier('data/targets/details/${gender}-${age}-ears${ears}.target', 'ears', xrange(1, 9), False)
        self.oldModifiers['jaw'] = RangeDetailModifier('data/targets/details/${gender}-${age}-jaw${jaw}.target', 'jaw', xrange(1, 8), False)
        
        self.oldModifiers['head'] = RangeDetailModifier('data/targets/details/neutral_${gender}-${age}-head${head}.target', 'head', xrange(1, 9), False)
        
        self.modifiers['pelvisTone'] = AsymmetricDetailModifier('data/targets/details/${gender}-${age}-pelvis-tone${pelvisTone}.target', 'pelvisTone', '1', '2', False)
        self.modifiers['buttocks'] = AsymmetricDetailModifier('data/targets/details/${gender}-${age}-nates${buttocks}.target', 'buttocks', '1', '2', False)
        self.modifiers['stomach'] = StomachModifier()
        
        gui3d.app.addLoadHandler('detail', self.loadHandler)
        gui3d.app.addLoadHandler('microdetail', self.loadHandler)
        for modifier in self.modifiers:
            gui3d.app.addLoadHandler(modifier, self.loadHandler)
        for modifier in self.oldModifiers:
            gui3d.app.addLoadHandler(modifier, self.loadHandler)
        gui3d.app.addSaveHandler(self.saveHandler)
        
        self.sliders = []

        y = 80
        self.modifiersBox = self.addView(gui3d.GroupBox([10, y, 9.0], 'Modifiers', gui3d.GroupBoxStyle._replace(height=25+24*3+6)));y+=25
        
        modifierStyle = gui3d.ButtonStyle._replace(width=(112-4)/2, height=20)

        self.detailButtonGroup = []

        self.tool = Detail3dTool(gui3d.app, True, 'translation')

        self.translationButton = self.modifiersBox.addView(gui3d.RadioButton(self.detailButtonGroup, 'Move', True, modifierStyle))
        self.scaleButton = self.modifiersBox.addView(gui3d.RadioButton(self.detailButtonGroup, label='Scale', style=modifierStyle));y+=24

        @self.translationButton.event
        def onClicked(event):
            self.tool = Detail3dTool(gui3d.app, True, 'translation')
            gui3d.app.tool = self.tool
            gui3d.RadioButton.onClicked(self.translationButton, event)

        @self.scaleButton.event
        def onClicked(event):
            self.tool = Detail3dTool(gui3d.app, True, 'scale')
            gui3d.app.tool = self.tool
            gui3d.RadioButton.onClicked(self.scaleButton, event)

        self.rightSymmetryButton = self.modifiersBox.addView(gui3d.Button('Sym<', style=modifierStyle))
        self.leftSymmetryButton = self.modifiersBox.addView(gui3d.Button('Sym>', style=modifierStyle));y+=24
        self.symmetryButton = self.modifiersBox.addView(gui3d.ToggleButton('Sym', style=modifierStyle))
        #self.microButton = self.modifiersBox.addView(gui3d.ToggleButton('Micro', style=modifierStyle))

        @self.rightSymmetryButton.event
        def onClicked(event):
            human = gui3d.app.selectedHuman
            human.applySymmetryRight()

        @self.leftSymmetryButton.event
        def onClicked(event):
            human = gui3d.app.selectedHuman
            human.applySymmetryLeft()

        @self.symmetryButton.event
        def onClicked(event):
            gui3d.ToggleButton.onClicked(self.symmetryButton, event)
            human = gui3d.app.selectedHuman
            human.symmetryModeEnabled = self.symmetryButton.selected
            #self.parent.tasksByName['Micro modelling'].symmetryButton.setSelected(self.symmetryButton.selected)
        """    
        @self.microButton.event
        def onClicked(event):
            gui3d.ToggleButton.onClicked(self.microButton, event)
            self.tool = Detail3dTool(gui3d.app, self.microButton.selected, self.tool.type)
            gui3d.app.tool = self.tool
        """
    def onShow(self, event):
        gui3d.app.tool = self.tool
        self.translationButton.setFocus()
        #self.sliders[0].setFocus()
        #self.syncSliders()
        gui3d.TaskView.onShow(self, event)

    def onHide(self, event):
        gui3d.app.tool = None
        gui3d.TaskView.onHide(self, event)
        
    def onResized(self, event):
        self.modifiersBox.setPosition([event.width - 150, self.modifiersBox.getPosition()[1], 9.0])

    def syncSliders(self):

        for slider in self.sliders:
            slider.update()
        
    def onHumanChanged(self, event):
        
        human = event.human
        
        for modifier in self.modifiers.itervalues():
            modifier.setValue(human, modifier.getValue(human))
            
        if self.isVisible():
            self.syncSliders()
        
    def loadHandler(self, human, values):
        
        if values[0] == 'detail':
            human.setDetail('data/targets/details/' + values[1] + '.target', float(values[2]))
        elif values[0] == 'microdetail':
            human.setDetail('data/targets/microdetails/' + values[1] + '.target', float(values[2]))
        else:
            try:
                fval = float(values[1])
            except:
                fval = None
            if fval == None:
                print "Ignored modifier", values
                return
            modifier = self.modifiers.get(values[0], None)
            if modifier:
                modifier.setValue(human, fval)
            else:
                modifier = self.oldModifiers.get(values[0], None)
                if modifier:
                    modifier.setValue(human, fval)
       
    def saveHandler(self, human, file):
        
        for t in human.targetsDetailStack.keys():
            if '/details' in t and ('trans' in t or 'scale' in t):
                file.write('detail %s %f\n' % (os.path.basename(t).replace('.target', ''), human.targetsDetailStack[t]))
            elif '/microdetails' in t:
                file.write('microdetail %s %f\n' % (os.path.basename(t).replace('.target', ''), human.targetsDetailStack[t]))
                
        for name, modifier in self.modifiers.iteritems():
            value = modifier.getValue(human)
            file.write('%s %f\n' % (name, value))
