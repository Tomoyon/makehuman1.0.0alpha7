#!/usr/bin/python
# -*- coding: utf-8 -*-

""" 
MakeHuman 3D Transformation functions. 

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    http://code.google.com/p/makehuman/

**Authors:**           Marc Flerackers

**Copyright(c):**      MakeHuman Team 2001-2011

**Licensing:**         GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)

**Coding Standards:**  See http://sites.google.com/site/makehumandocs/developers-guide

Abstract
--------

This module contains algorithms used to perform high-level 3D 
transformations on the 3D mesh that is used to represent the human 
figure in the MakeHuman application.
 
These currently include: 

  - morphing for anatomical variations 
  - pose deformations
  - mesh coherency tests (for use during the development cycle)
  - visualisation functions (for use during the development cycle)
  
This will also be where any future mesh transformation 
algorithms will be coded. For example: 

  - collision deformations
  - etc..

"""

__docformat__ = 'restructuredtext'

import time
import aljabr
import textures3d
import files3d
import os

NMHVerts = 18528

targetBuffer = {}
theHuman = None

class Target:

    """
    This class is used to store morph targets.
    """

    def __init__(self, obj, name):
        """
        This method initializes an instance of the Target class.
            
        Parameters
        ----------
        
        obj:
            *3d object*. The base object (to which a target can be applied).
            This object is read to determine the number of vertices to
            use when initializing this data structure.
        
        name:
            *string*. The name of this target.
        
        
        """
        
        self.name = name
        self.data = [0, 0, 0] * len(obj.verts)
        self.faces = []
        self.verts = []
        self.morphFactor = -1
        fileDescriptor = None

        while fileDescriptor == None:
            try:
                fileDescriptor = open(name)
            except:
                if "caucasian" in name:
                    if not "female_young" in name:
                        print 'Unable to open %s'%(name)
                        if "female_child" in name:
                            name = name.replace("female_child", "female_young")
                        elif "female_old" in name:
                            name = name.replace("female_old", "female_young")
                        elif "male_child" in name:
                            name = name.replace("male_child", "female_young")
                        elif "male_young" in name:
                            name = name.replace("male_young", "female_young")
                        elif "male_old" in name:
                            name = name.replace("male_old", "female_young")
                        else:
                            print 'Unable to open %s'%(name)
                            return
                        print 'Trying %s instead'%(name)
                    else:
                        print 'Unable to open %s'%(name)
                        return
                else:
                    if "asian" in name:
                        print 'Unable to open %s'%(name)
                        name = name.replace("asian", "caucasian")
                        print 'Trying %s instead'%(name)
                    elif "african" in name:
                        print 'Unable to open %s'%(name)
                        name = name.replace("african", "caucasian")
                        print 'Trying %s instead'%(name)
                    else:
                        print 'Unable to open %s'%(name)
                        return

        facesToRecalculate = set()  # Indices of faces affected by the target, to put in buffer
        verticesToRecalculate = []  # Indices of vertices affected by the targets, to put in buffer

        for line in fileDescriptor:
            translationData = line.split()
            if len(translationData) == 4:
                vertIndex = int(translationData[0])
                if vertIndex >= NMHVerts:
                    continue
                verticesToRecalculate.append(vertIndex)
                translationVector = (float(translationData[1]), float(translationData[2]), float(translationData[3]))
                self.data[vertIndex] = translationVector

                vertToModify = obj.verts[vertIndex]
                for face in vertToModify.sharedFaces:
                    facesToRecalculate.add(face.idx)

        self.faces = tuple(facesToRecalculate)
        self.verts = tuple(verticesToRecalculate)

        fileDescriptor.close()
        
    def apply(self, obj, morphFactor, update=True, calcNormals=True, faceGroupToUpdateName=None, scale=(1.0,1.0,1.0)):
        global theHuman
        
        self.morphFactor = morphFactor                

        if self.verts:
            
            if morphFactor or calcNormals or update:
            
                if faceGroupToUpdateName:

                    # if a facegroup is provided, apply it ONLY to the verts used
                    # by the specified facegroup.
                
                    faceGroupToUpdate = obj.getFaceGroup(faceGroupToUpdateName)
                    verticesToUpdate = set()
                    facesToRecalculate = list(faceGroupToUpdate.faces)
                    for f in facesToRecalculate:
                        for v in f.verts:
                            verticesToUpdate.add(v)
                            
                else:

                    # if a vertgroup is not provided, all verts affected by
                    # the targets will be modified

                    facesToRecalculate = [obj.faces[i] for i in self.faces]
                    verticesToUpdate = [obj.verts[i] for i in self.verts]

            if morphFactor:
                
                # Adding the translation vector

                for v in verticesToUpdate:
                    targetVect = self.data[v.idx]
                    dv0 = targetVect[0] * morphFactor * scale[0]
                    dv1 = targetVect[1] * morphFactor * scale[1]
                    dv2 = targetVect[2] * morphFactor * scale[2]
                    v.co[0] += dv0
                    v.co[1] += dv1
                    v.co[2] += dv2                    
                    if not hasattr(self, "isWarp"):
                        sv = theHuman.shadowVerts[v.idx]
                        sv[0] += dv0
                        sv[1] += dv1
                        sv[2] += dv2     

            if calcNormals:
                obj.calcNormals(1, 1, verticesToUpdate, facesToRecalculate)
            if update:
                obj.update(verticesToUpdate)

            return True
            
        return False


def getTarget(obj, targetPath):
    """
    This function retrieves a set of translation vectors from a morphing 
    target file and stores them in a buffer. It is usually only called if 
    the translation vectors from this file have not yet been buffered during 
    the current session. 
    
    The translation target files contain lists of vertex indices and corresponding 
    3D translation vectors. The buffer is structured as a list of lists 
    (a dictionary of dictionaries) indexed using the morph target file name, so:
    \"targetBuffer[targetPath] = targetData\" and targetData is a list of vectors 
    keyed on their vertex indices. 
    
    For example, a translation direction vector
    of [0,5.67,2.34] for vertex 345 would be stored using 
    \"targetData[345] = [0,5.67,2.34]\".
    If this is taken from target file \"foo.target\", then this targetData could be
    assigned to the buffer with 'targetBuffer[\"c:/MH/foo.target\"] = targetData'. 
    
    Parameters
    ----------

    obj:
        *3d object*. The target object to which the translations are to be applied.
        This object is read by this function to define a list of the vertices 
        affected by this morph target file.

    targetPath:
        *string*. The file system path to the file containing the morphing targets. 
        The precise format of this string will be operating system dependant.
    """

    global targetBuffer

    try:
        target = targetBuffer[targetPath]
    except KeyError:
        target = None
        
    if target:
        if hasattr(target, "isWarp"):
            target.reinit()
        return target

    target = Target(obj, targetPath)
    targetBuffer[targetPath] = target
    
    return target

def loadTranslationTarget(obj, targetPath, morphFactor, faceGroupToUpdateName=None, update=1, calcNorm=1, scale=[1.0,1.0,1.0]):
    """
    This function retrieves a set of translation vectors and applies those 
    translations to the specified vertices of the mesh object. This set of 
    translations corresponds to a particular morph target file.  
    If the file has already been loaded into memory then the translation 
    vectors are read from the target data buffer, otherwise a function is 
    first called to load the target data from disk into a buffer for 
    future use.
    
    The translation target files contain lists of vertex indices and corresponding 
    3D translation vectors. The translation vector for each vertex is multiplied 
    by a common factor (morphFactor) before being applied to the specified vertex.
    
    Parameters
    ----------

    obj:
        *3d object*. The target object to which the translations are to be applied.
        This object is read and updated by this function.

    targetPath:
        *string*. The file system path to the file containing the morphing targets. 
        The precise format of this string will be operating system dependant.

    morphFactor:
        *float*. A factor between 0 and 1 controlling the proportion of the translations 
        to be applied. If 0 then the object remains unmodified. If 1 the 'full' translations
        are applied. This parameter would normally be in the range 0-1 but can be greater 
        than 1 or less than 0 when used to produce extreme deformations (deformations 
        that extend beyond those modelled by the original artist).

    faceGroupToUpdateName:
        *string*. Optional: The name of a single facegroup to be affected by the target.
        If specified, then only transformations to faces contained by the specified 
        facegroup are applied. If not specified, all transformations contained within the
        morph target file are applied. This permits a single morph target file to contain
        transformations that affect multiple facegroups, but to only be selectively applied 
        to individual facegroups.

    update:
        *int flag*. A flag to indicate whether the update method on the object should be called.

    calcNorm:
        *int flag*. A flag to indicate whether the normals are to be recalculated (1/true) 
        or not (0/false).   

    """

    if not (morphFactor or update):
        return

    target = getTarget(obj, targetPath)

    target.apply(obj, morphFactor, update, calcNorm, faceGroupToUpdateName, scale)


def calcTargetNormal(obj, targetPath):
    """
    Sometime it's needed to recal the normals of last applied
    target. Previously we use a workaroundl loading a target with a very
    small morphFactor and calcNorm=1. But to have the code more readable
    and avoid confusion, it's better to have a separate function.
    
    Parameters
    ----------

    obj:
        *3d object*. The target object to which the translations are to be applied.
        This object is read and updated by this function.

    targetPath:
        *string*. The file system path to the file containing the morphing targets. 
        The precise format of this string will be operating system dependant.    

    """

    target = getTarget(obj, targetPath)

    # if the target is already buffered, just get it using
    # the path as key

    if target:
        facesToRecalculate = [obj.faces[i] for i in target.faces]
        verticesToUpdate = [obj.verts[i] for i in target.verts]
        obj.calcNormals(1, 1, verticesToUpdate, facesToRecalculate)
        obj.update(verticesToUpdate)

        # print "Applied %s with value of %f in %f sec"%(targetPath, morphFactor,(time.time() - t1))

        return True
    else:
        return False


def loadRotationTarget(obj, targetPath, morphFactor):  
    """
    This function loads a rotation target file and applies the rotations to 
    specific vertices on the mesh object by rotating them around a common axis 
    (which is specified in a separate 'info' file using two of 
    the vertices on the mesh object). 
    
    Each line in the rotation target file contains a pair of numbers. The first
    is an index to a particular vertex in the array of vertices in the mesh object. 
    The second is a rotation angle.
    
    This function requires an 'info' file with a name that corresponds to the name of
    the rotation target file. This file contains a pair of 
    indices that point to two of the vertices in the mesh object. The coordinates of
    those two vertices are used as the axis around which the vertices listed in the 
    rotation target file will be rotated. 
    
    The rotation angles for each of the points listed in the rotation target file are
    multiplied by a factor (morphFactor) before being applied to the vertex coordinates.

    Parameters
    ----------

    obj:
        *3d object*. The target object to which the rotations are to be applied.

    targetPath:
        *string*. The file system path to the file containing the rotation targets.
        **Note.** This path is also used to find an accompanying path with the '.info'
        extension appended to targetPath. This 'info' file must be present and must 
        contain the element numbers of a pair 
        of vertices around which the rotation is to be performed.

    morphFactor:
        *float*. A factor between 0 and 1 controlling the proportion of the specified 
        rotations to apply. If 0 then the object remains unmodified. If 1 the full rotations
        are applied. This parameter would normally be in the range 0-1 but can be greater 
        than 1 or less than 0 when used to produce extreme deformations (deformations 
        that extend beyond those modelled by the original artist).

    calcNorm:
        *int flag*. A flag to indicate whether the normals are to be recalculated (1/true) 
        or not (0/false).    

    """

    a = time.time()  

    try:
        f = open(targetPath)
        fileDescriptor = f.readlines()
        f.close()
    except:
        print "Error opening target file: %s"%(targetPath)
        return 0


    #Get info of axis from the first line of file
    rotAxeInfo = fileDescriptor[0].split()

    #Calculate the rotation axis vector
    axisP1  = obj.verts[int(rotAxeInfo[0])]
    axisP2  = obj.verts[int(rotAxeInfo[1])]
    axis = rotAxeInfo[2]
    #rotAxis = [axisP2.co[0]-axisP1.co[0],axisP2.co[1]-axisP1.co[1],axisP2.co[2]-axisP1.co[2]]
    #rotAxis = vunit(rotAxis)
    #axis = axisID(rotAxis)

    indicesToUpdate = []

    v1= [axisP1.co[0],axisP1.co[1],axisP1.co[2]]
    v2= [axisP2.co[0],axisP2.co[1],axisP2.co[2]]
    actualRotCenter = aljabr.centroid([v1,v2])

    for stringData in fileDescriptor[1:]:
        listData = stringData.split()
        theta = float(listData[0])
        theta = theta*morphFactor
        #Rmtx = makeRotMatrix(-theta, rotAxis)
        if axis == "X":
            Rmtx = aljabr.makeRotEulerMtx3D(theta,0,0)
        elif axis == "Y":
            Rmtx = aljabr.makeRotEulerMtx3D(0,theta,0)
        elif axis == "Z":
            Rmtx = aljabr.makeRotEulerMtx3D(0,0,theta)

        for pIndex in listData[1:]:
            pointIndex = int(pIndex)
            indicesToUpdate.append(pointIndex)
            pointRotated = aljabr.rotatePoint(actualRotCenter, obj.verts[pointIndex].co, Rmtx)

            obj.verts[pointIndex].co = list(pointRotated)
    
    verticesToUpdate = [obj.verts[i] for i in set(indicesToUpdate)]
    obj.update(verticesToUpdate)
    print "ROTATION TIME", time.time()-a

    return 1

def saveTranslationTarget(obj, targetPath, groupToSave=None, epsilon=0.001):
    """
    This function analyses an object to determine the differences between the current 
    set of vertices and the vertices contained in the *originalVerts* list, writing the
    differences out to disk as a morphing target file.

    Parameters
    ----------

    obj:
        *3d object*. The object from which the current set of vertices is to be determined.

    originalVerts:
        *list of list*. The positions of vertices in the base reference mesh. This is a list of 
        3 coordinates of the form: [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3],...[xn,yn,zn]]

    targetPath:
        *string*. The file system path to the output file into which the morphing targets
        will be written.

    groupToSave:
        *faceGroup*. It's possible to save only the changes made to a specific part of the 
        mesh object by indicating the face group to save.

    epsilon:
        *float*. The distance that a vertex has to have been moved for it to be 
        considered 'moved'
        by this function. The difference between the original vertex position and
        the current vertex position is compared to this value. If that difference is greater
        than the value of epsilon, the vertex is considered to have been modified and will be 
        saved in the output file as a morph target.   

    """

    modifiedFacesIndices = {}
    modifiedVertsIndices = []
    originalVerts = files3d.loadVertsCoo(obj.path)

    if not groupToSave:
        vertsToSave = xrange(len(obj.verts))
    else:
        pass  # TODO verts from group

    objVerts = obj.verts

    nVertsExported = 0
    if objVerts:
        for index in vertsToSave:
            originalVertex = originalVerts[index]
            targetVertex = objVerts[index]
            sharedFaces = obj.verts[index].sharedFaces

            delta = aljabr.vsub(targetVertex.co, originalVertex)
            dist = aljabr.vdist(originalVertex, targetVertex.co)

            if dist > epsilon:
                nVertsExported += 1
                dataToExport = [index, delta[0], delta[1], delta[2]]
                modifiedVertsIndices.append(dataToExport)

                # for f in sharedFaces:
                #    modifiedFacesIndices[f.idx] = f.idx

    try:
        fileDescriptor = open(targetPath, 'w')
    except:
        print 'Unable to open %s'%(targetPath)
        return None

    # for fidx in modifiedFacesIndices.values():
        # fileDescriptor.write("%i " % (fidx))
    # fileDescriptor.write("\n")

    for data in modifiedVertsIndices:
        fileDescriptor.write('%d %f %f %f\n' % (data[0], data[1], data[2], data[3]))

    fileDescriptor.close()
    if nVertsExported == 0:
        print 'Warning%t|Zero verts exported in file ' + targetPath


def checkMeshTopology(obj, verbose=None):
    """
    
    This function is used (during the development cycle rather than in the 
    runtime application) to perform a series of checks to validate 
    the coherence of the current mesh topology. 
    These checks use a set of functions provided by 
    the halfedge plugin module.

    .. image:: ../images/mesh_check.png

    Three main checks are performed:

      - The \"isolated verts\" check identifies vertices that are not 
        used by any edges.
      - The \"boundary edge\" check identifies edges that are connected
        to only one face.
      - The \"wrong normal\" check identifies adjoining half-edges (which
        should point in opposite directions) that are pointing in the
        same direction. 
        
    If any errors are detected they are displayed in the output stream and 
    the vertices and edges
    found to be defective are coloured on the image on the screen. 
    
    The 'wrong normal' check is written to accommodate an h-edge \"bug\":
    if a face has a wrong normal (i.e. wrong verts
    order) the edge loop is infinite, because the
    condition:
    
    ::

        while loopHedge != startHEdge:

    is never true. We therefore assume that a vertex can't share
    more than 25 edges, so, if the number of iterations is over
    25, the normals are wrong.

    Boundary verts are blue, while verts of an edge
    between two faces with opposite normals, are red.

    Parameters
    ----------
    
    verbose:
        *integer flat*. If 1, all discrepancies discovered will be 
        displayed to the output stream.
    
    """

    isolate_verts = []
    edges_boundary = []
    wrong_normals_edges = []

    import halfedges

    if not hasattr(obj, 'he_hedgeCalculated'):
        halfedges.calcHedgeData(obj)

    for v in obj.verts:
        he = v.he_hedge
        twin = he.twin
        if not he:
            isolate_verts.append(obj.verts.index(v))
            continue
        if not twin:
            edges_boundary.append(he)
            v.color = [0, 0, 255, 255]  # Blue = boundary
            continue

        startHEdge = he
        loopHedge = twin.next
        i = 0
        while loopHedge != startHEdge:
            i += 1
            if not loopHedge.twin:
                edges_boundary.append(loopHedge)
                v.color = [0, 0, 255, 255]  # Blue = boundary
                break
            try:
                loopHedge = loopHedge.twin.next
            except:
                break
            if i > 25:
                wrong_normals_edges.append(loopHedge.next)
                v.color = [255, 0, 0, 255]  # Red =Wrong normals
                break
    for v in obj.verts:
        v.update(0, 0, 1)
    print 'Check Mesh result:'
    print 'Mesh %s has %s isolated verts ' % (obj.name, len(isolate_verts))
    if verbose:
        for iv in isolate_verts:
            print iv
    print 'Mesh %s has %s boundary edges ' % (obj.name, len(edges_boundary))
    if verbose:
        for eb in edges_boundary:
            print eb
    print 'Mesh %s has %s edges shared between faces with opposite normals ' % (obj.name, len(wrong_normals_edges))
    if verbose:
        for wne in wrong_normals_edges:
            print wne


def analyzeTarget(obj, targetPath):
    """
    This function is used (more during the development cycle than in the 
    runtime application) to analyze the difference between the vertex positions of 
    a mesh object and those recorded in a file on disk. 
    The result is a representation of each vertex displacement as a color. 
    This provides a graphical representation of the deformations
    with respect to the original positions as defined by the mesh object.
    
    Plugin developers may find this function useful for visualizing and checking
    integration plugins. 

    Parameters
    ----------
    
    obj:
        *3D object*. The object possessing the 'original' vertex positions.

    targetPath:
        *string*. The file system path to the file containing the target vertex positions.
    """

    try:
        fileDescriptor = open(targetPath)
    except:
        print 'Unable to open %s'%(targetPath)
        return 0

    targetData = fileDescriptor.readlines()
    distMax = 0.00001

    # Step 1: calculate max length

    for vData in targetData:
        vectorData = vData.split()
        targetsVector = [float(vectorData[1]), float(vectorData[2]), float(vectorData[3])]
        dist = aljabr.vlen(targetsVector)
        if dist > distMax:
            distMax = dist

    # Step 2: calculate color

    for vData in targetData:
        vectorData = vData.split()
        mainPointIndex = int(vectorData[0])
        targetsVector = [float(vectorData[1]), float(vectorData[2]), float(vectorData[3])]
        dist = aljabr.vlen(targetsVector)
        v = obj.verts[mainPointIndex]
        if dist == 0:
            v.color = [255, 255, 255, 255]
        else:
            R = int((dist / distMax) * 255)
            G = 255 - int(R / 10)
            B = 255 - int(R / 10)
            v.color = [R, G, B, 255]
            v.update(0, 0, 1)

    fileDescriptor.close()


def colorizeVerts(obj, color, targetPath=None, faceGroupName=None):
    """       
    """

    if targetPath:
        try:
            fileDescriptor = open(targetPath)
        except:
            print 'Unable to open %s'%(targetPath)
            return 0

        for vData in fileDescriptor:
            vectorData = vData.split()
            mainPointIndex = int(vectorData[0])
            v = obj.verts[mainPointIndex]
            v.color = color
            v.update(0, 0, 1)

        fileDescriptor.close()
    elif faceGroupName:
        found = False
        for faceGroup in obj.faceGroups:
            if faceGroup.name == faceGroupName:
                found = True
                for f in faceGroup.faces:
                    f.color = [color, color, color]
                    f.updateColors()
        if not found:
            print 'Warning, face group %s not found in %s possible values are' % (faceGroupName, obj.name)
            for faceGroup in obj.faceGroups:
                print faceGroup.name
    else:
        for v in obj.verts:
            v.color = color
            v.update(0, 0, 1)


def loadVertsColors(obj, colorsPath, update=1, mode='new'):
    """
    This function is used to load a set of vertex colors from a file and 
    apply them to an object. This is used for both the humanoid object and 
    for the colors of GUI controls although they may be merged with colors from 
    a tga file for display of the humanoid model depending upon the visualisation 
    mode being used.
    
    Parameters
    ----------
    
    obj:
        *3D object*. The object to which the colors from the file are to be applied.

    colorsPath:
        *string*. The file system path to the file containing the vertex colors.

    update:
        *int flag*. If update = 1, each vertex in the object is updated based
        on the values read from the file.
        
    mode:
        *string*. A mode setting of \"new\" to completely replace the current color 
        or \"linearmix\" to produce a linear mix of the existing color and the color 
        from the file.  
       
    """

    try:
        fileDescriptor = open(colorsPath)
    except:

        # print "WARNING: Unable to open color file %s"%(colorsPath)

        return 0
    colorData = fileDescriptor.readlines()
    fileDescriptor.close()

    # if mode == new, the existing colors will be totally
    # replaced by the colors loaded. So we re-init it using
    # range function that make a list of n integers, where n is
    # the number of vertices

    # TODO THE CODE  COMMENTED BELOW IS WRONG: must be updated with new color structure
    # if mode == "new":
    #    obj.colors = xrange(len(obj.verts))

    if len(colorData) != len(obj.faces):
        print 'Warning: Color data does not match number of vertices ( %i vs %i)' % (len(colorData), len(obj.faces))
        return 0

    for (i, f) in enumerate(obj.faces):
        faceColor = colorData[i]
        vColors = [int(x) for x in faceColor.split()]
        f.color = [[vColors[0], vColors[1], vColors[2], vColors[3]],
            [vColors[4], vColors[5], vColors[6], vColors[7]],
            [vColors[8], vColors[9], vColors[10], vColors[11]],
            [vColors[12], vColors[13], vColors[14], vColors[15]]]

        # I assign single verts color too, but without really use them in realtime rendering
        # infact, in realtime rendering we use face.color and not vert.color, but
        # vert.color maybe useful in some algos, in example when exporting to renderman.

        f.verts[0].color = [vColors[0], vColors[1], vColors[2], vColors[3]]
        f.verts[1].color = [vColors[4], vColors[5], vColors[6], vColors[7]]
        f.verts[2].color = [vColors[8], vColors[9], vColors[10], vColors[11]]
        f.verts[3].color = [vColors[12], vColors[13], vColors[14], vColors[15]]

        # print f.verts[0].idx, f.verts[0].color

        if update:
            f.updateColors()

    #print 'Time to apply colors ', time.time() - t1


def saveVertsColorsFromBitmap(obj, imagePath):
    """
    This function is used (during the development cycle rather than in the 
    runtime application) to save a set of vertex 'colors' reading uv
    projection on a tga image.
    
    Parameters
    ----------
    
    obj:
        *3D object*. The object to which the colors apply.

    imagePath:
        *string*. The file system path to the file containing the vertex 'colors'.

           
    """

    t1 = time.time()
    tgaData = textures3d.readTGA(imagePath)
    if tgaData:
        BGRlist = tgaData[0]
        xres = tgaData[1]
        yres = tgaData[2]
        numOfPixel = tgaData[3]
        byteUsedForPixel = tgaData[4]

        objectColor = []
        for f in obj.faces:
            faceColors = []
            for uv in f.uv:
                u = uv[0]
                v = uv[1]

                pixelIdx = textures3d.UVCooToBitmapIndex(xres, yres, u, v)
                if byteUsedForPixel == 3:
                    pixelIdx *= 3
                    B = BGRlist[pixelIdx]
                    G = BGRlist[pixelIdx + 1]
                    R = BGRlist[pixelIdx + 2]
                    A = 255

                if byteUsedForPixel == 4:
                    pixelIdx *= 4
                    B = BGRlist[pixelIdx]
                    G = BGRlist[pixelIdx + 1]
                    R = BGRlist[pixelIdx + 2]
                    A = BGRlist[pixelIdx + 3]

                color = (R, G, B, A)
                faceColors.append(color)
            objectColor.append(faceColors)
    else:

        print 'WARNING: %s not converted in verts color' % imagePath
        return

    try:
        fileDescriptor = open(imagePath + '.colors', 'w')
    except:
        print 'error to save obj file'
        return 0

    # Write, for each line, a sequence of 3 verts color of the triangle:
    # r1,g1,b1,a1,r2,g2,b2,a2,r3,g3,b3,a3,

    for fc in objectColor:
        colorVert0 = fc[0]
        colorVert1 = fc[1]
        colorVert2 = fc[2]
        fileDescriptor.write('%i %i %i %i %i %i %i %i %i %i %i %i\n' % (colorVert0[0], colorVert0[1], colorVert0[2], colorVert0[3], colorVert1[0], colorVert1[1],
                             colorVert1[2], colorVert1[3], colorVert2[0], colorVert2[1], colorVert2[2], colorVert2[3]))
    fileDescriptor.close()

    print 'Time to save colors ', time.time() - t1


def resetObj(obj, update=None, calcNorm=None):
    """
    This function resets the positions of the vertices of an object to their original base positions.
    
    Parameters
    ----------
    
    obj:
        *3D object*. The object whose vertices are to be reset.

    update:
        *int*. An indicator to control whether to call the vectors update method.

    calcNorm:
        *int*. An indicator to control whether or not the normals should be recalculated

    """

    originalVerts = files3d.loadVertsCoo(obj.path)
    for (i, v) in enumerate(obj.verts):
        v.co[0] = originalVerts[i][0]
        v.co[1] = originalVerts[i][1]
        v.co[2] = originalVerts[i][2]
        if update:
            v.update()
    if calcNorm:
        obj.calcNormals()

#scaleList is a list of tuple like this:  [(set(1,2,3,4),[1.0,1.0,2.0]),....]. First entry of tuple is a set of indices, second entry is a triple list of scale.
def scaleTarget(obj, index, morphFactor, scaleList):
   targetVect = obj.verts[index]
   scale = [1.0,1.0,1.0]
   for tpl in scaleList:
      if (index in tpl[0]):
         scale = tpl[1]
         break
   return [targetVect[0]*scale[0]*morphFactor ,targetVect[1]*scale[1]*morphFactor, targetVect[2]*scale[2]*morphFactor]

def loadTranslationTarget2(obj, targetPath, morphFactor, scaleList, update=1, calcNorm=1):

    #change this thing
    #dictionary of targets we will do this manually no need to pushtarget
    global targetBuffer
    if not targetBuffer.has_key(targetPath):
        pushTargetInBuffer(obj, targetPath)

    # if the target is already buffered, just get it using
    # the path as key
   
    if os.path.isfile(targetPath): 
        target = targetBuffer[targetPath]   

        # if a facegroup is provided, apply it ONLY to the verts used
        # by the specified facegroup.
        facesToRecalculate = [obj.faces[i] for i in target.faces]
        verticesToUpdate = [obj.verts[i] for i in target.verts]

        # Adding the translation vector
        for v in verticesToUpdate:
            targetVect = scaleTarget(target.data, v.idx) #jcapco changed
            v.co[0] += targetVect[0] * morphFactor
            v.co[1] += targetVect[1] * morphFactor
            v.co[2] += targetVect[2] * morphFactor

        if calcNorm == 1:
            obj.calcNormals(1, 1, verticesToUpdate, facesToRecalculate)
        if update:
            obj.update(verticesToUpdate)

        return True

def printBox(file, obj):
   dx = []
   dy = []
   dz = []
   data = open(file)
   for line in data:
      line = line.split()
      i = int(line[0])
      vert = obj.verts[i].co
      if (len(dx) == 0):
        dx = [vert[0], vert[0]]
        dy = [vert[1], vert[1]]
        dz = [vert[2], vert[2]]
      else:
        if dx[0] > vert[0] : dx[0] = vert[0]
        if dx[1] < vert[0] : dx[1] = vert[0]
        if dy[0] > vert[1] : dy[0] = vert[1]
        if dy[1] < vert[1] : dy[1] = vert[1]
        if dz[0] > vert[2] : dz[0] = vert[2]
        if dz[1] < vert[2] : dz[1] = vert[2]
  
   print " dx : ", dx
   print " dy : ", dy
   print " dz : ", dz

def computeScale(oBox, file, obj):
   dx = []
   dy = []
   dz = []
   data = open(file)
   for line in data:
      line = line.split()
      i = int(line[0])
      vert = obj.verts[i].co
      if (len(dx) == 0):
        dx = [vert[0], vert[0]]
        dy = [vert[1], vert[1]]
        dz = [vert[2], vert[2]]
      else:
        if dx[0] > vert[0] : dx[0] = vert[0]
        if dx[1] < vert[0] : dx[1] = vert[0]
        if dy[0] > vert[1] : dy[0] = vert[1]
        if dy[1] < vert[1] : dy[1] = vert[1]
        if dz[0] > vert[2] : dz[0] = vert[2]
        if dz[1] < vert[2] : dz[1] = vert[2]
   scale = [1.0,1.0,1.0]
   if (len(dx)>0):
      scale[0] = (dx[1]-dx[0])/(oBox[0][1] - oBox[0][0])
      scale[1] = (dy[1]-dy[0])/(oBox[1][1] - oBox[1][0])
      scale[2] = (dz[1]-dz[0])/(oBox[2][1] - oBox[2][0])
   return scale
