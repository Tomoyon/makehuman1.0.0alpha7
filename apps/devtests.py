#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module is just for internal use, to test API and ideas.
Actually it's just a random collection of functions...and
IT NOT WORK
"""


def testAnimation(self):

    # TODO: move this in a test module

    x = self.basemesh.x + .01
    print 'animation test ', x
    self.basemesh.setLoc(x, self.basemesh.y, self.basemesh.z)
    self.scene.redraw()


def testUPArrowsEvent(self):

    # TODO: move this in a test module

    print 'test up arrow'
    self.basemesh.y += .25
    self.basemesh.setLoc(self.basemesh.x, self.basemesh.y, self.basemesh.z)
    self.scene.redraw()


def testColor(self):
    """
    This method loads vertex colors on the base object.
    
    **Parameters:** This method has no parameters.

    """

    # TODO: move this in a test module

    algos3d.loadVertsColors(self.basemesh, 'data/3dobjs/base.obj.colors')


def applyTexture(self):
    """
    This method applies the texture file to either the standard mesh or the
    subdivided mesh (epending upon which is currently active).

    **Parameters:** None.

    """

    if not self.basemesh.isSubdivided:
        self.basemesh.setTexture('data/textures/texture.tga')
    else:
        sob = self.scene.getObject(self.basemesh.name + '.sub')
        sob.setTexture('data/textures/texture.tga')
    self.scene.redraw()


def analyzeTestTarget(self):
    """
    This function analyses a specific morph target file from a hardcoded
    file location that is used as part of the morph target file development
    cycle.

    **Parameters:** None.

    """

    # TODO: move this function in an utility module

    if not self.basemesh.isSubdivided:
        self.basemesh.applyDefaultColor()
        self.analyzeTarget(basemesh, 'data/targets/test.target')
        self.scene.redraw()


self.scene.connect('UP_ARROW', self.testUPArrowsEvent)
self.scene.connect('TIMER', self.testAnimation)
