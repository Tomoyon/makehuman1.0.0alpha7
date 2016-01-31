#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
:Authors:    
    Marc Flerackers

:Version: 1.0
:Copyright: MakeHuman Team 2001-2011
:License: GPL3 

Abstract
--------

This module contains all of the base classes needed to manage the 3D MakeHuman
data structures at runtime. This includes the data structures themselves as well
as methods to handle their manipulation in memory. For example, the Vert class
defines the data structures to hold information about mesh vertex objects,
while the Face class defines data structures to hold information about mesh face
objects.

These base classes implement a nested hierarchical structure for the objects
that make up the scene that is shown to the user. An Object3D contains one or more
FaceGroup objects. A FaceGroup contains one or more Face objects, which themselves
refer to one or more Vert objects (depending on the kind of primitives that are used).
The Vert objects themselves are actually owned by the Object3D.

"""

__docformat__ = 'restructuredtext'

import mh
import aljabr
import time
from types import *
import os
import weakref
from fastmath import vnorm3d

textureCache = {}


class Texture(mh.Texture):

    """
    A subclass of the base texture class extended to hold a modification date.
    """

    def __init__(self, *args, **kwargs):
        mh.Texture.__init__(self, *args, **kwargs)
        self.modified = None
        
def getTexture(path, cache=None):

    texture = None
    cache = cache or textureCache
    
    if path in cache:
        
        texture = cache[path]
        
        if os.stat(path).st_mtime != texture.modified:
            
            print ('reloading ', path)	# TL: unicode problems unbracketed
            
            try:
                img = mh.Image(path=path)
                texture.loadImage(img)
            except RuntimeError, text:
                print text
                return
            else:
                texture.modified = os.stat(path).st_mtime
    else:
        
        try:
            img = mh.Image(path=path)
            texture = Texture(img)
            #texture.loadSubImage('data/themes/default/images/slider_focused.png', 0, 0)
        except RuntimeError, text:
            print text
        else:
            texture.modified = os.stat(path).st_mtime
            cache[path] = texture
            
    return texture
    
def reloadTextures():
        print 'Reloading textures'
        for path in textureCache:
            try:
                textureCache[path].loadImage(path)
            except RuntimeError, text:
                print text

class Vert:

    """
    A vertex object. This object holds the 3D location and surface normal
    of the vertex and an RGBA color value. It also has references to
    other related data structures.

    Vertex information from this object is passed into the OpenGL 3D
    engine via the C code in *glmodule.c*, which uses the glDrawArray
    OpenGL function to draw objects.

    A single Python Vert object is used for all of the faces within a 
    given face group that share that same vertex. This is why the uv coordinates
    are stored in the Face object instead. This way one vertex might have more
    than one uv coordinate pair depending on the face. It is similar to using an
    uv layer.
    
    However, the OpenGL code considers a vertex shared by multiple faces with different
    uv to be different vertices. So, a Vert object that appears once on the Python
    vertex list may appear multiple times on the C vertex list.

    For example: Two faces share the edge 'v2-v3'. One face is defined by
    vertices v1, v2 and v3, and the other face is defined by vertices
    v3, v2, and v4. The Python vertex list could contain four vertices:

      [v1,v2,v3,v4]

    However, the C vertex list will repeat vertices that are shared by more
    than one face in the faces do not belong to the same group. So, the C
    vertex list will be based on the list:

      [v1,v2,v3,v4]
      
      or
      
      [v1,v2,v3,v3,v2,v4]

    Each Python Vert object contains a list attribute, *__indicesInFullVertArray*,
    listing the various locations where the vertex appears in the C vertex list.
    This allows information held against a single Vert object in Python to be
    copied to multiple locations in the coordinate and color lists in the
    C-based OpenGL world.
    
    .. py:attribute:: co
    
        The coordinates of the vertex. [float, float, float]
        
    .. py:attribute:: no
    
        The normal of this vertex. [float, float, float]
        
    .. py:attribute:: object
    
        The object of which this vertex is a part. :py:class:`module3d.Object3D`
        
    .. py:attribute:: sharedFaces
    
        The list of faces that share this vertex. [:py:class:`module3d.Face`, ..]
        
    .. py:attribute:: idx
    
        The index of this vertex in the vertices list. int
        
    .. py:attribute:: color
    
        The color of the vertex in rgba. [byte, byte, byte, byte]
    
    :param co: The coordinates for this face.
    :type co: [float, float, float]
    :param idx: The index in the mesh for this face.
    :type idx: int
    :param object: The object which will own this face.
    :type object: :py:class:`module3d.Object3d`
    """

    def __init__(self, co=[0, 0, 0], idx=0, object=None):

        self.co = co
        self.no = [0, 0, 0]
        self.object = object
        self.sharedFaces = []
        self.idx = idx
        self.color = [255, 255, 255, 255]
        self.weights = None
        
        self.__indicesInFullVertArray = []
    
    def setCoordinates(self, co):
        """
        Replaces the coordinates.
        
        :param co: The coordinates for this face.
        :type co: [float, float, float]
        """
        self.co = co
        self.update(False, True, False)
        
    def setNormal(self, no):
        """
        Replaces the normal.
        
        :param no: The normal for this face.
        :type no: [float, float, float]
        """
        self.no = no
        self.update(True, False, False)
    
    def setColor(self, color):
        """
        Replaces the color.
        
        :param no: The color for this face.
        :type no: [byte, byte, byte, byte]
        """
        self.color = color
        self.update(False, False, True)

    def update(self, updateNor=True, updateCoo=True, updateCol=False):
        """
        This method updates the coordinates, normal and/or color of a vertex in the C
        OpenGL world, based upon the values currently held in the Python Vert class.

        The vertex indexing system in the Python code differs from the
        OpenGL vertex indexing system used in the C code, as discussed in the description
        of this *Vert* class (see above).

          - In Python, a single vertex can be shared by multiple faces. In OpenGL, there
            are always multiple copies of any such vertex.

        Because one Python Vert object can appear multiple times in the C vertex list,
        each Python Vert object has an attribute, *__indicesInFullVertArray*, which lists
        the conceptual 'index' in the C lists of coordinates and colors.

        From this 'conceptual' index, we can find where the vertex's coordinates lie in the full C
        coordinate list. Because each vertex has three coordinates (x, y, and z), the
        coordinate list will be three times as long as this 'conceptual' index. So, a vertex
        listed in the *__indicesInFullVertArray* at positions 1 and 4 (the second and fifth
        positions) will have its coordinates listed on the C coordinates list at
        positions 3, 4, and 5, and again at positions 12, 13, and 14. Or:

          (n*3), (n*3)+1, (n*3)+2   for both n = 1 and n = 4.

        The C color list is similar to the coordinate list. As each color is defined by
        four components 'red, green, blue, and alpha (transparency)' the C color list is
        four times as long as this 'conceptual' index. So, a vertex listed in the
        *__indicesInFullVertArray* at positions 1 and 4 will have its color component values listed in the C
        color list at positions 4, 5, 6, and 7, and again at positions 16, 17, 18, and
        19. Or:

          (n*4), (n*4)+1, (n*4)+2, (n*4)+3   for both n = 1 and n = 4.

        The color passed into this method can originate from various sources, depending upon what the
        color is to represent at this moment in time. Colors can be manipulated to indicate 
        faces or vertices that have been selected, to indicate morph target strengths at different 
        locations on the model or control or to show base colors.
        
        When updating the color information, this method usually sets all vertex colors in the C array
        that were derived from a single Python Vert object to be the same color.

        :param updateNor: Whether the normal needs to be updated.
        :type updateNor: Boolean
        :param updateCoo: Whether the coordinates needs to be updated.
        :type updateCoo: Boolean
        :param updateCol: Whether the color needs to be updated.
        :type updateCol: Boolean
        """
        
        if not self.object.object3d:
            return

        if updateCoo:
            for i in self.__indicesInFullVertArray:
                self.object.object3d.setVertCoord(i, self.co)
        if updateNor:
            for i in self.__indicesInFullVertArray:
                self.object.object3d.setNormCoord(i, self.no)
        if updateCol:
            for i in self.__indicesInFullVertArray:
                self.object.object3d.setColorComponent(i, self.color)

    def calcNorm(self):
        """
        This method calculates the vertex surface normal based upon a mathematical average
        of the physical normals of all faces sharing this vertex. This results in a smooth surface.

        .. image:: _static/vert_norm.png

        The physical normal of a surface is a direction vector at right angles
        to that surface. Although the triangular mesh consists of a series of flat
        faces, the surface normal calculated for a vertex averages out the
        physical normals of the faces that share that vertex, enabling the
        rendering engine (OpenGL) to shade the object so that the surface looks
        like a single, smooth shape.

        Because the actual 3D engine uses optimized glDrawElements,
        where each vertex can have only one normal, it is impossible
        in MakeHuman to draw the geometry in a \"flat\" mode.

        MakeHuman is organically oriented, so the benefits of using this optimized technique
        outweigh potential performance costs.

        """

        no = [0.0, 0.0, 0.0]
        for f in self.sharedFaces:
            no[0] += f.no[0]
            no[1] += f.no[1]
            no[2] += f.no[2]
        self.no = vnorm3d(no)

    def vertsShared(self):
        """
        This method returns a list of the vertices of all faces that share this vertex.

        .. image:: _static/vert_shared.png

        If processing the vector V in the image above this function would return [v1,v2,v3,v4,v5,v6,v7]

        """

        sharedVertices = set()
        for f in self.sharedFaces:
            for v in f.verts:
                sharedVertices.add(v)
        return list(sharedVertices)

    def __str__(self):

        return 'vert num %s, coord(%s,%s,%s)' % (self.idx, self.co[0], self.co[1], self.co[2])


class Face:

    """
    An object representing a point, line, triangle or quad.
    
    .. py:attribute:: no
        
        The normal of the face. [float, float, float]
        
    .. py:attribute:: verts
    
        A list of vertices that represent the corners of this face. [:py:class:`module3d.Vert`, ..]
        
    .. py:attribute:: idx
    
        The index of this face in the list of faces. int
        
    .. py:attribute:: group
    
        The face group that is the parent of this face. :py:class:`module3d.FaceGroup`
        
    .. py:attribute:: color
    
        A list of rgba colors, one for each vertex. [[byte, byte, byte, byte], ..]
        
    .. py:attribute:: uv
    
        A list of indices to uv coordinates, one for each vertex. [int, ..]
      
    :param verts: The vertices for this face.
    :type: :py:class:`module3d.Vert`, ..
    """

    def __init__(self, *verts):

        self.no = [0.0, 0.0, 0.0]
        self.verts = verts[:]
        self.uv = None
        self.color = None
        self.idx = None
        self.group = None

    def setColor(self, color):
        """
        Sets the color for this face.
        
        :param color: The color in rgba.
        :type: [byte, byte, byte, byte]
        """
        self.color = [color for v in self.verts]
        self.updateColors()

    def calcNormal(self):
        """
        This method calculates the physical surface normal of the face using the :py:func:`aljabr.planeNorm` function from
        the aljabr module. This results in a direction vector at right angles to the
        two edges vt2_vt1 and vt2_vt3.
        """

        if len(self.verts) > 2:
            vt1 = self.verts[0].co
            vt2 = self.verts[1].co
            vt3 = self.verts[2].co
            self.no = aljabr.planeNorm(vt1, vt2, vt3)
        else:
            self.no = [0.0, 0.0, 1.0]

    def updateColors(self):
        """
        This method updates the color attributes for each vertex on this face.
        """

        for (i, v) in enumerate(self.verts):
            v.setColor(self.color[i])

    def __str__(self):

        return 'face %i: verts: %s' % (self.idx, [v.idx for v in self.verts])


class FaceGroup:

    """
    A FaceGroup (a group of faces with a unique name).

    Each Face object can be part of one FaceGroup. Each face object has an
    attribute, *group*, storing the FaceGroup it is a member of.

    The FaceGroup object contains a list of the faces in the group and must be
    kept in sync with the FaceGroup references stored by the individual faces.
    
    .. py:attribute:: name
    
        The name. str
        
    .. py:attribute:: parent
    
        The parent. :py:class:`module3d.Object3D`
        
    .. py:attribute:: faces
    
        A read-only iterator of the faces. [:py:class:`module3d.Face`, ..]

    :param name: The name of the group.
    :type name: str
    """

    def __init__(self, name):

        self.name = name
        self.__faces = []
        self.parent = None
        self.__elementIndex = 0
        self.__elementCount = 0
        self.__colorID = [0, 0, 0]

    def __str__(self):
        """
        This method returns a string containing the name of the FaceGroup. This
        method is called when the object is passed to the 'print' function.

        **Parameters:** This method has no parameters.

        """

        return 'facegroup %s' % self.name
        
    def clear(self):
        """
        Removes all faces from the group.
        """
        del self.__faces[:]
        
    @property
    def faces(self):
        return iter(self.__faces)

    def createFace(self, verts, uvs=None):
        """
        Creates a new module3d.Face based on the given vertices and optionally uv coordinates.
        
        :param verts: The vertices.
        :type verts: [:py:class:`module3d.Vert`, ..]
        :param uvs: The uv coordinates.
        :type uvs: [(u,v), ..]
        """
        if len(verts) != self.parent.vertsPerPrimitive:
            raise RuntimeError('The amount of vertices does not match the amount of vertices per primitive of the object')
        
        f = Face(*verts)
        f.group = self
        f.idx = len(self.parent.faces)
        self.__faces.append(f)
        self.parent.faces.append(f)

        if uvs:
            if len(verts) != len(uvs):
                raise RuntimeError('The amount of uv coordinates does not match the amount of vertices')
            f.uv = [self.parent.addUv(uv) for uv in uvs]
            
        for v in verts:
            v.sharedFaces.append(f)

        return f

    def setColor(self, color):
        """
        Sets the color for all the faces in this group.
        
        :param color: The color in rgba.
        :type color: [byte, byte, byte, byte]
        """
        for f in self.__faces:
            f.setColor(color)

class Object3D(object):

    """
    A 3D object, made up of faces and vertices (i.e. containing Face objects and Vert objects).
    The humanoid object manipulated by the MakeHuman application is an instance of this
    class, as are all the GUI controls. Multiple 3D objects can be added to the 3D scene.

    This object has a position and orientation of its own, and the positions and
    orientations of faces and vertices that make up this object are defined relative to
    it.
    
    .. py:attribute:: name
    
        The name. str
        
    .. py:attribute:: object3d
    
        The object in the OpenGL engine. mh.Object3D
    
    .. py:attribute:: x
    
        The x coordinate of the position of this object in the coordinate space of the scene. float
        
    .. py:attribute:: y
    
        The x coordinate of the position of this object in the coordinate space of the scene. float
        
    .. py:attribute:: z
    
        The x coordinate of the position of this object in the coordinate space of the scene. float

    .. py:attribute:: rx
    
        The x rotation component of the orientation of this object within the coordinate space of the scene. float
        
    .. py:attribute:: ry
    
        The y rotation component of the orientation of this object within the coordinate space of the scene. float
        
    .. py:attribute:: rz
    
        The z rotation component of the orientation of this object within the coordinate space of the scene. float
        

    .. py:attribute:: sx
    
        The x scale component of the size of this object within the coordinate space of the scene. float
        
    .. py:attribute:: sy
    
        The y scale component of the size of this object within the coordinate space of the scene. float
        
    .. py:attribute:: sz
    
        The z scale component of the size of this object within the coordinate space of the scene. float
        
    .. py:attribute:: verts
    
        The list of vertices that go to make up this object. [:py:class:`module3d.Vert`, ..]
        
    .. py:attribute:: faces
    
        The list of faces that go to make up this object. [:py:class:`module3d.Face`, ..]
        
    .. py:attribute:: faceGroups
    
        A read-only iterator to the FaceGroups that go to make up this object. [:py:class:`module3d.FaceGroup`, ..]
        
    .. py:attribute:: faceGroupCount
    
        A read-only property indicating the amount of FaceGroups since len does not work on an iterator. int
        
    .. py:attribute:: cameraMode
        
        A flag to indicate which of the two available perspective camera projections, fixed or movable, is to be used to draw this object. int
        
    .. py:attribute:: visibility
    
        A flag to indicate whether or not this object is visible. Boolean
        
    .. py:attribute:: pickable
    
        A flag to indicate whether this object is pickable by mouse or not. Boolean
        
    .. py:attribute:: texture
    
        The path of a file on disk containing the object texture. str
        
    .. py:attribute:: shader
    
        The shader. int
        
    .. py:attribute:: shaderParameters.
    
        The shader parameters. dict
        
    .. py:attribute:: shadeless
    
        A flag to indicate whether this object is unaffected by variations in lighting (certain GUI elements aren't). Boolean
        
    .. py:attribute:: solid
    
        A flag to indicate whether this object is solid or wireframe. Boolean
        
    .. py:attribute:: transparentPrimitives
    
        The amount of transparent primitives in this object. int
        
    .. py:attribute:: vertsPerPrimitive
    
        The amount of vertices per primitive. int
        
    .. py:attribute:: uvValues
    
        A list of uv values referenced to by the faces. [(float, float), ]
        
    .. py:attribute:: uvMap
    
        A map of uv values to speed up searching. dict

    """

    def __init__(self, objName, vertsPerPrimitive=4):

        self.name = objName
        self.object3d = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.rx = 0
        self.ry = 0
        self.rz = 0
        self.sx = 1
        self.sy = 1
        self.sz = 1
        self.verts = []
        self.faces = []
        self.__faceGroups = []
        self.cameraMode = 1
        self.visibility = 1
        self.pickable = 1
        self.texture = None
        self.shader = 0
        self.shaderParameters = {}
        self.shadeless = 0
        self.solid = 1
        self.transparentPrimitives = 0
        self.vertsPerPrimitive = vertsPerPrimitive
        self.__indexBuffer = []
        self.__vertexBufferSize = None
        self.uvValues = None
        self.uvMap = {}
        
        self.__object = None
        
    def getObject(self):
        if self.__object:
            return self.__object()
        else:
            return None
        
    def setObject(self, value):
        self.__object = weakref.ref(value)
    
    object = property(getObject, setObject)
    
    @property
    def faceGroups(self):
        return iter(self.__faceGroups)
        
    @property
    def faceGroupCount(self):
        return len(self.__faceGroups)
        
    def clear(self):
        """
        Clears both local and remote data to repurpose this object
        """
    
        # Clear remote data
        self.detach()

        # Clear local data data
        if self.__indexBuffer:
            del self.__indexBuffer[:]
        if self.uvValues:
            del self.uvValues[:]
        self.uvMap.clear()
        # Remove verts
        for v in self.verts:
            del v.object
            del v.sharedFaces[:]
        del self.verts[:]
        # Remove faces
        for f in self.faces:
            del f.verts
            del f.group
        del self.faces[:]
        # Remove face groups
        for fg in self.__faceGroups:
            del fg.parent
            fg.clear()
        del self.__faceGroups[:]
        
    def attach(self):
        """
        Attachess the object by creating the remote data.
        """
        if self.object3d:
            return
        if not self.__vertexBufferSize:
            return

        selectionColorMap.assignSelectionID(self)

        #print "sending: ", self.name, len(self.verts)

        coIdx = 0
        fidx = 0
        uvIdx = 0
        colIdx = 0

        # create an object with __vertexBufferSize vertices and len(__indexBuffer) / 3 triangles

        self.object3d = mh.Object3D(self.__vertexBufferSize, self.__indexBuffer)
        mh.world.append(self.object3d)

        for g in self.faceGroups:
            if 'joint' in g.name or 'helper' in g.name:
                continue
            groupVerts = set()
            for f in g.faces:
                faceColor = f.color
                if faceColor == None:
                    faceColor = [[255, 255, 255, 255], [255, 255, 255, 255], [255, 255, 255, 255], [255, 255, 255, 255]]
                fUV = f.uv
                if fUV == None:
                    fUV = [-1, -1, -1, -1]

                i = 0
                for v in f.verts:
                    if (v.idx, fUV[i]) not in groupVerts:

                        # self.object3d.setAllCoord(coIdx, colIdx, v.co, v.no, g._FaceGroup__colorID, faceColor[i])

                        self.object3d.setVertCoord(coIdx, v.co)
                        self.object3d.setNormCoord(coIdx, v.no)
                        self.object3d.setColorIDComponent(coIdx, g._FaceGroup__colorID)
                        self.object3d.setColorComponent(colIdx, faceColor[i])
                        groupVerts.add((v.idx, fUV[i]))

                        coIdx += 1
                        colIdx += 1

                        if self.uvValues:
                            self.object3d.setUVCoord(uvIdx, self.uvValues[fUV[i]])
                            uvIdx += 1

                    i += 1

        if self.texture:
            self.setTexture(self.texture)

        self.object3d.shader = self.shader

        for (name, value) in self.shaderParameters.iteritems():
            self.object3d.shaderParameters[name] = value

        self.object3d.translation = (self.x, self.y, self.z)
        self.object3d.rotation = (self.rx, self.ry, self.rz)
        self.object3d.scale = (self.sx, self.sy, self.sz)
        self.object3d.visibility = self.visibility
        self.object3d.shadeless = self.shadeless
        self.object3d.pickable = self.pickable
        self.object3d.solid = self.solid
        self.object3d.transparentPrimitives = self.transparentPrimitives
        self.object3d.vertsPerPrimitive = self.vertsPerPrimitive
        self.object3d.cameraMode = self.cameraMode

        # TODO add all obj attributes
        
    def detach(self):
        """
        Detaches the object, clearing all remote data
        """
        
        if self.object3d:
            mh.world.remove(self.object3d)
            del self.object3d
            self.object3d = None

    def updateIndexBuffer(self):
        """
        Build the lists of vertex indices and UV-indices for this face group.
        In the Python data structures a single vertex can be shared between
        multiple faces in the same face group. However, if a single vertex
        has multiple UV-settings, then we generate additional vertices so
        that we have a place to record the separate UV-indices.
        Where the UV-map needs a sharp transition (e.g. where the eyelids
        meet the eyeball) we therefore create duplicate vertices.
        """
        del self.__indexBuffer[:]
        fullArrayIndex = 0
        for g in self.__faceGroups:
          if 'joint' in g.name or 'helper' in g.name:
            continue
          g._FaceGroup__elementIndex = fullArrayIndex  # first index in opengl array
          groupVerts = {}
          for f in g.faces:
              for (i, v) in enumerate(f.verts):
                  if f.uv:
                      t = f.uv[i]
                  else:
                      t = -1
                  if (v.idx, t) not in groupVerts:
                      v._Vert__indicesInFullVertArray.append(fullArrayIndex)
                      groupVerts[(v.idx, t)] = fullArrayIndex
                      self.__indexBuffer.append(fullArrayIndex)
                      fullArrayIndex += 1
                  else:
                      self.__indexBuffer.append(groupVerts[(v.idx, t)])
          g._FaceGroup__elementCount = g._FaceGroup__elementIndex - fullArrayIndex

        self.__vertexBufferSize = fullArrayIndex

    def createFaceGroup(self, name):
        """
        Creates a new module3d.FaceGroup with the given name.

        :param name: The name for the face group.
        :type name: [float, float, float]
        :return: The new face group.
        :rtype: :py:class:`module3d.FaceGroup`
        """
        fg = FaceGroup(name)
        fg.parent = self
        self.__faceGroups.append(fg)
        return fg

    def createVertex(self, co):
        """
        Creates a new module3d.Vert with the given coordinates.

        :param co: The coordinates for the vertex.
        :type co: [float, float, float]
        :return: The new vertex.
        :rtype: :py:class:`module3d.Vert`
        """
        v = Vert(co, len(self.verts), self)
        self.verts.append(v)
        return v
        
    def addUv(self, uv):
        """
        Adds the uv coordinate to the uv map.

        :param uv: The uv coordinates to add.
        :type uv: (float, float)
        """
        key = tuple(uv)
        try:
            return self.uvMap[key]
        except:
            index = len(self.uvValues)
            self.uvMap[key] = index
            self.uvValues.append(uv)
            return index
            
    def setColor(self, color):
        """
        Sets the color for the entire object.

        :param color: The color in rgba.
        :type color: [byte, byte, byte, byte]
        """
        for g in self.__faceGroups:
            g.setColor(color)

    def setLoc(self, locx, locy, locz):
        """
        This method is used to set the location of the object in the 3D coordinate space of the scene.

        :param locx: The x coordinate of the object.
        :type locx: float
        :param locy: The y coordinate of the object.
        :type locy: float
        :param locz: The z coordinate of the object.
        :type locz: float
        """

        self.x = locx
        self.y = locy
        self.z = locz
        try:
            self.object3d.translation = (self.x, self.y, self.z)
        except AttributeError, text:
            pass

    def setRot(self, rx, ry, rz):
        """
        This method sets the orientation of the object in the 3D coordinate space of the scene.

        :param rx: Rotation around the x-axis.
        :type rx: float
        :param ry: Rotation around the y-axis.
        :type ry: float
        :param rz: Rotation around the z-axis.
        :type rz: float
        """

        self.rx = rx
        self.ry = ry
        self.rz = rz
        try:
            self.object3d.rotation = (self.rx, self.ry, self.rz)
        except AttributeError, text:
            pass

    def setScale(self, sx, sy, sz):
        """
        This method sets the scale of the object in the 3D coordinate space of
        the scene, relative to the initially defined size of the object.

        :param sx: Scale along the x-axis.
        :type sx: float
        :param sy: Scale along the x-axis.
        :type sy: float
        :param sz: Scale along the x-axis.
        :type sz: float
        """

        self.sx = sx
        self.sy = sy
        self.sz = sz
        try:
            self.object3d.scale = (self.sx, self.sy, self.sz)
        except AttributeError, text:
            pass

    def setVisibility(self, visible):
        """
        This method sets the visibility of the object.

        :param visible: Whether or not the object is visible.
        :type visible: Boolean
        """

        self.visibility = visible
        try:
            self.object3d.visibility = int(visible)
        except AttributeError, text:
            pass

    def setPickable(self, pickable):
        """
        This method sets the pickable flag of the object.

        :param pickable: Whether or not the object is pickable.
        :type pickable: Boolean
        """

        self.pickable = pickable
        try:
            self.object3d.pickable = pickable
        except AttributeError, text:
            pass

    def setTexture(self, path, cache=None):
        """
        This method is used to specify the path of a file on disk containing the object texture.

        :param path: The path of a texture file.
        :type path: str
        :param cache: The texture cache to use.
        :type cache: dict
        """
        
        self.texture = path
        
        if not path:
            self.clearTexture()
        
        texture = getTexture(path, cache)
        
        if texture:
            try:
                self.object3d.texture = texture.textureId
            except AttributeError, text:
                pass

    def clearTexture(self):
        """
        This method is used to clear an object's texture.
        """

        self.texture = None
        try:
            self.object3d.texture = 0
        except AttributeError, text:
            pass

    def hasTexture(self):
        return self.object3d.texture != 0

    def setShader(self, shader):
        """
        This method is used to specify the shader.
        
        :param shadeless: The shader.
        :type shadeless: int
        """

        self.shader = shader
        try:
            self.object3d.shader = shader
        except AttributeError, text:
            pass

    def setShaderParameter(self, name, value):
        self.shaderParameters[name] = value
        try:
            self.object3d.shaderParameters[name] = value
        except AttributeError, text:
            pass

    def setShadeless(self, shadeless):
        """
        This method is used to specify whether or not the object is affected by lights.
        This is used for certain GUI controls to give them a more 2D type
        appearance (predominantly the top bar of GUI controls).

        :param shadeless: Whether or not the object is unaffected by lights.
        :type shadeless: Boolean
        """

        self.shadeless = shadeless
        try:
            self.object3d.shadeless = self.shadeless
        except AttributeError, text:
            pass
            
    def setSolid(self, solid):
        """
        This method is used to specify whether or not the object is drawn solid or wireframe.

        :param solid: Whether or not the object is drawn solid or wireframe.
        :type solid: Boolean
        """
        
        self.solid = solid
        try:
            self.object3d.solid = self.solid
        except AttributeError, text:
            pass
            
    def setTransparentPrimitives(self, transparentPrimitives):
        """
        This method is used to specify the amount of transparent faces.

        :param transparentPrimitives: The amount of transparent faces.
        :type transparentPrimitives: int
        """
        
        self.transparentPrimitives = transparentPrimitives
        try:
            self.object3d.transparentPrimitives = self.transparentPrimitives
        except AttributeError, text:
            pass
            
    def setVertsPerPrimitive(self, vertsPerPrimitive):
        """
        This method is used to specify the amount of vertices per primitive. Points, lines, triangles or quads.

        :param vertsPerPrimitive: The amount of vertices per primitive.
        :type vertsPerPrimitive: int
        """
        self.vertsPerPrimitive = vertsPerPrimitive
        try:
            self.object3d.vertsPerPrimitive = self.vertsPerPrimitive
        except AttributeError, text:
            pass

    def getFaceGroup(self, name):
        """
        This method searches the list of FaceGroups held for this object, and
        returns the FaceGroup with the specified name. If no FaceGroup is found
        for that name, this method returns None.

        :param name: The name of the FaceGroup to retrieve.
        :type name: str
        :return: The FaceGroup if found, None otherwise.
        :rtype: :py:class:`module3d.FaceGroup`
        """

        for fg in self.__faceGroups:
            if fg.name == name:
                return fg
        return None

    def getVerticesAndFacesForGroups(self, groupNames):
        vertices = []
        faces = []

        for name in groupNames:
            group = self.getFaceGroup(name)
            faces.extend(group.faces)
            for f in group.faces:
                vertices.extend(f.verts)
        vertices = list(set(vertices))
        return (vertices, faces)

    def updateGroups(self, groupnames, recalcNormals=True, update=True):
        if recalcNormals or update:
            (vertices, faces) = self.getVerticesAndFacesForGroups(groupnames)
            if recalcNormals:
                self.calcNormals(1, 1, vertices, faces)
            if update:
                self.update(vertices, recalcNormals)

    def setCameraProjection(self, cameraMode):
        """
        This method sets the camera mode used to visualize this object (fixed or movable).
        The 3D engine has two camera modes (both perspective modes).
        The first is moved by the mouse, while the second is fixed.
        The first is generally used to model 3D objects (a human, clothes,
        etc.), while the second is used for 3D GUI controls.

        :param cameraMode: The camera mode. 0 = fixed camera; 1 = movable camera.
        :type cameraMode: int
        """

        self.cameraMode = cameraMode
        try:
            self.object3d.cameraMode = self.cameraMode
        except AttributeError, text:
            pass

    def update(self, verticesToUpdate=None, updateNormals=True):
        """
        This method is used to call the update methods on each of a list of vertices or all vertices that form part of this object.

        :param verticesToUpdate: The list of vertices to update.
        :type verticesToUpdate: [:py:class:`module3d.Vert`, ..]
        :param updateNormals: Whether to update the normals as well.
        :type updateNormals: [:py:class:`module3d.Vert`, ..]
        """

        if verticesToUpdate == None:
            verticesToUpdate = self.verts
        
        for v in verticesToUpdate:
            v.update(updateNor=updateNormals)

    def calcNormals(self, recalcVertexNormals=1, recalcFaceNormals=1, verticesToUpdate=None, facesToUpdate=None):
        """
        Updates the given vertex and/or face normals.
        
        :param recalcVertexNormals: A flag to indicate whether or not the vertex normals should be recalculated.
        :type recalcVertexNormals: Boolean
        :param recalcFaceNormals: A flag to indicate whether or not the face normals should be recalculated.
        :type recalcFaceNormals: Boolean
        :param verticesToUpdate: The list of vertices to be updated, if None all vertices are updated.
        :type verticesToUpdate: list of :py:class:`module3d.Vert`
        :param facesToUpdate: The list of faces to be updated, if None all faces are updated.
        :type facesToUpdate: list of :py:class:`module3d.Face`
        """

        if recalcFaceNormals:
            if facesToUpdate == None:
                facesToUpdate = self.faces
            for f in facesToUpdate:
                f.calcNormal()

        if recalcVertexNormals:
            if verticesToUpdate == None:
                verticesToUpdate = self.verts
            for v in verticesToUpdate:
                v.calcNorm()
                
    def calcBBox(self):
        """
        Calculates the axis aligned bounding box of this object in the object's coordinate system. 
        """
        if self.verts:
            bbox =  [self.verts[0].co[:],self.verts[0].co[:]]
            for v in self.verts:
                if v.co[0] < bbox[0][0]: #minX
                    bbox[0][0] = v.co[0]
                if v.co[0] > bbox[1][0]: #maxX
                    bbox[1][0] = v.co[0]
                if v.co[1] < bbox[0][1]: #minY
                    bbox[0][1] = v.co[1]
                if v.co[1] > bbox[1][1]: #maxY
                    bbox[1][1] = v.co[1]
                if v.co[2] < bbox[0][2]: #minZ
                    bbox[0][2] = v.co[2]
                if v.co[2] > bbox[1][2]: #maxX
                    bbox[1][2] = v.co[2]
        else:
            bbox = [[0,0,0], [0,0,0]]
        return bbox

    def __str__(self):

        return 'object3D named: %s, nverts: %s, nfaces: %s, at |%s,%s,%s|' % (self.name, len(self.verts), len(self.faces), self.x, self.y, self.z)


class SelectionColorMap:

    """
    The objects support the use of a technique called *Selection Using Unique
    Color IDs*, that internally uses color-coding of components within the
    scene to support the selection of objects by the user using the mouse.

    This technique generates a sequence of colors (color IDs), assigning a
    unique color to each uniquely selectable object or component in the scene.
    These colors are not displayed, but are used by MakeHuman to generates an
    unseen image of the various selectable elements. This image uses the same
    camera settings currently being used for the actual, on-screen image.
    When the mouse is clicked, the position of the mouse is used with the
    unseen image to retrieve a color. MakeHuman uses this color as an ID to
    identify which object or component the user clicked with the mouse.

    This technique uses glReadPixels() to read the single pixel at the
    current mouse location, using the unseen, color-coded image.

    For further information on this technique, see:

      - http://www.opengl.org/resources/faq/technical/selection.htm and
      - http://wiki.gamedev.net/index.php/OpenGL_Selection_Using_Unique_Color_IDs

    **Note.** Because the 3D engine uses glDrawElements in a highly opimized
    way and each vertex can have only one color ID, there there is a known
    problem with selecting individual faces with very small FaceGroups using
    this technique. However, this is not a major problem for MakeHuman, which
    doesn't use such low polygon groupings.
    
    - **self.colorIDToFaceGroup**: *Dictionary of colors IDs* A dictionary of the color IDs used for
      selection (see MakeHuman Selectors, above).
    - **self.colorID**: *float list* A progressive color ID.
    
    The attributes *self.colorID* and *self.colorIDToFaceGroup*
    support a technique called *Selection Using Unique Color IDs* to make each
    FaceGroup independently clickable.

    The attribute *self.colorID* stores a progressive color that is incremented for each successive
    FaceGroup added to the scene.
    The *self.colorIDToFaceGroup* attribute contains a list that serves as a directory to map
    each color back to the corresponding FaceGroup by using its color ID.
    """

    def __init__(self):
    
        self.colorIDToFaceGroup = {}
        self.colorID = 0

    def assignSelectionID(self, obj):
        """
        This method generates a new, unique color ID for each FaceGroup,
        within a particular Object3D object, that forms a part of this scene3D
        object. This color ID can subsequently be used in a non-displayed
        image map to determine the FaceGroup that a mouse click was made in.

        This method loops through the FaceGroups, assigning the next color
        in the sequence to each subsequent FaceGroup. The color value is
        written into a 'dictionary' to serve as a color ID that can be
        translated back into the corresponding FaceGroup name when a mouse
        click is detected.
        This is part of a technique called *Selection Using Unique Color IDs*
        to make each FaceGroup independently clickable.

        :param obj: The object3D object for which color dictionary entries need to be generated.
        :type obj: module3d.Object 3D
        """

        # print "DEBUG COLOR AND GROUPS, obj", obj.name
        # print "---------------------------"

        for g in obj.faceGroups:
            self.colorID += 1

            # 555 to 24-bit rgb

            idR = (self.colorID % 32) * 8
            idG = ((self.colorID >> 5) % 32) * 8
            idB = ((self.colorID >> 10) % 32) * 8

            g._FaceGroup__colorID = (idR, idG, idB)
            
            self.colorIDToFaceGroup[self.colorID] = g

            # print "SELECTION DEBUG INFO: facegroup %s of obj %s has the colorID = %s,%s,%s or %s"%(g.name,obj.name,idR,idG,idB, self.colorID)

    def getSelectedFaceGroup(self):
        """
        This method uses a non-displayed image containing color-coded faces
        to return the index of the FaceGroup selected by the user with the mouse.
        This is part of a technique called *Selection Using Unique Color IDs* to make each
        FaceGroup independently clickable.

        :return: The selected face group.
        :rtype: :py:class:`module3d.FaceGroup`
        """

        picked = mh.getColorPicked()

        IDkey = picked[0] / 8 | picked[1] / 8 << 5 | picked[2] / 8 << 10  # 555

        # print "DEBUG COLOR PICKED: %s,%s,%s %s"%(picked[0], picked[1], picked[2], IDkey)

        try:
            groupSelected = self.colorIDToFaceGroup[IDkey]
        except:

            # print groupSelected.name
            #this print should only come on while debugging color picking
            #print 'Color %s (%s) not found' % (IDkey, picked)
            groupSelected = None
        return groupSelected

    def getSelectedFaceGroupAndObject(self):
        """
        This method determines whether a FaceGroup or a non-selectable zone has been
        clicked with the mouse. It returns a tuple, showing the FaceGroup and the parent
        Object3D object, or None.
        If no object is picked, this method will simply print \"no clickable zone.\"

        :return: The selected face group and object.
        :rtype: (:py:class:`module3d.FaceGroup`, :py:class:`module3d.Object3d`)
        """

        facegroupPicked = self.getSelectedFaceGroup()
        if facegroupPicked:
            objPicked = facegroupPicked.parent
            return (facegroupPicked, objPicked)
        else:
            #this print should only be made while debugging picking
            #print 'not a clickable zone'
            return None
            
def getFacesFromVerts(vertIndices, verts):

    return set([f for i in vertIndices for f in verts[i].sharedFaces])
    
selectionColorMap = SelectionColorMap()
