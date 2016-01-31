# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Project Name:        MakeHuman
# Product Home Page:   http://www.makehuman.org/
# Code Home Page:      http://code.google.com/p/makehuman/
# Authors:             Thomas Larsson
# Script copyright (C) MakeHuman Team 2001-2011
# Coding Standards:    See http://sites.google.com/site/makehumandocs/developers-guide
#
# Abstract
# Utility for making clothes to MH characters.
#

import bpy
import os
import random
import uuid
from bpy.props import *
from mathutils import Vector
from . import base_uv
from . import error

#
#   Global variables
#

theThreshold = -0.2
theListLength = 3
Epsilon = 1e-4

BaseMeshVersion = "alpha_7"

LastClothing = "Tights"
ClothingEnums = [
    ("Body", "Body", "Body"),
    ("Skirt", "Skirt", "Skirt"),
    ("Tights", "Tights", "Tights")
]

if BaseMeshVersion == "alpha_7":
    LastVertices = {
        "Body" : 15340,
        "Skirt" : 16096,
        "Tights" : 18528,
    }
    NBodyVerts = LastVertices["Body"]
    NBodyFaces = 14812

#
#   isHuman(ob):
#   isClothing(ob):
#   getHuman(context):
#   getClothing(context):
#   getObjectPair(context):
#

def isSelfClothed(context):
    if context.scene.MCUseInternal:
        return (context.scene.MCSelfClothed != LastClothing)
    else:
        return False

        
def isHuman(ob):
    try:
        return ob["MhxMesh"]
    except:
        return False                

        
def isClothing(ob):
    return ((ob.type == 'MESH') and (not isHuman(ob)))

    
def getHuman(context):
    for ob in context.scene.objects:
        if ob.select and isHuman(ob):
            return ob
    raise error.MhcloError("No human selected")

        
def getClothing(context):        
    for ob in context.scene.objects:
        if ob.select and isClothing(ob):
            return ob
    raise error.MhcloError("No clothing selected")
    
    
def getObjectPair(context):
    human = None
    clothing = None
    scn = context.scene
    for ob in scn.objects:
        if ob.select:
            if isHuman(ob):
                if human:
                    raise error.MhcloError("Two humans selected: %s and %s" % (human.name, ob.name))
                else:
                    human = ob
            elif ob.type == 'MESH':
                if clothing:
                    raise error.MhcloError("Two pieces of clothing selected: %s and %s" % (clothing.name, ob.name))
                else:
                    clothing = ob
    if not human:
        raise error.MhcloError("No human selected")
    if isSelfClothed(context):
        if clothing:
            raise error.MhcloError("Clothing %s selected but human %s is self-clothed" % (clothing.name, human.name))
        checkObjectOK(human, context)
        nverts = len(human.data.vertices)
        nOldVerts = LastVertices[scn.MCSelfClothed]
        clothing = copyObject(human, nOldVerts, nverts, context, "Clothing")
        base = copyObject(human, 0, nOldVerts, context, "Base")
        return (base, clothing)
    elif not clothing:
        raise error.MhcloError("No clothing selected")
    return (human, clothing)  

    
def copyObject(human, n0, n1, context, name):
    scn = context.scene
    for ob in scn.objects:
        ob.select = False
    human.select = True
    scn.objects.active = human
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.duplicate(linked=False)
    ob = context.object
    ob.name = name
    ob.data.name = name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    print(context.object, context.object.data)
    for n in range(n0,n1):
        ob.data.vertices[n].select = False
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

#
#   snapSelectedVerts(context):
#

def snapSelectedVerts(context):
    ob = context.object
    bpy.ops.object.mode_set(mode='OBJECT')
    selected = []
    for v in ob.data.vertices:
        if v.select:
            selected.append(v)
    bpy.ops.object.mode_set(mode='EDIT')
    for v in selected:
        v.select = True
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(
            snap=True, 
            snap_target='CLOSEST', 
            snap_point=(0, 0, 0), 
            snap_align=False, 
            snap_normal=(0, 0, 0))
    return

#
#    printMverts(stuff, mverts):
#

def printMverts(stuff, mverts):
    for n in range(theListLength):
        (v,dist) = mverts[n]
        if v:
            print(stuff, v.index, dist)

#
#    selectVerts(verts, ob):
#

def selectVerts(verts, ob):
    for v in ob.data.vertices:
        v.select = False
    for v in verts:
        v.select = True
    return    

#
#   goodName(name):    
#   getFileName(pob, context, ext):            
#

def goodName(name):    
    newName = name.replace('-','_').replace(' ','_')
    return newName.lower()
    
def getFileName(pob, context, ext):            
    name = goodName(pob.name)
    outpath = '%s/%s' % (context.scene.MCDirectory, name)
    outpath = os.path.realpath(os.path.expanduser(outpath))
    if not os.path.exists(outpath):
        print("Creating directory %s" % outpath)
        os.mkdir(outpath)
    outfile = os.path.join(outpath, "%s.%s" % (name, ext))
    return (outpath, outfile)
    
#
#
#

ShapeKeys = [
    'Breathe',
    ]

#
#    findClothes(context, bob, pob, log):
#

def findClothes(context, bob, pob, log):
    base = bob.data
    proxy = pob.data
    scn = context.scene
    
    bestVerts = []
    for pv in proxy.vertices:
        try:
            pindex = pv.groups[0].group
        except:
            pindex = -1
        if pindex < 0:
            selectVerts([pv], pob)
            raise error.MhcloError("Clothes %s vert %d not member of any group" % (pob.name, pv.index))

        gname = pob.vertex_groups[pindex].name
        bindex = None
        for bvg in bob.vertex_groups:
            if bvg.name == gname:
                bindex = bvg.index
        if bindex == None:
            raise error.MhcloError("Did not find vertex group %s in base mesh" % gname)            

        mverts = []
        for n in range(theListLength):
            mverts.append((None, 1e6))

        exact = False
        for bv in base.vertices:
            if exact:
                break
            for grp in bv.groups:
                if grp.group == bindex:
                    vec = pv.co - bv.co
                    n = 0
                    for (mv,mdist) in mverts:
                        if vec.length < Epsilon:
                            mverts[0] = (bv, -1)
                            exact = True
                            break
                        if vec.length < mdist:
                            for k in range(n+1, theListLength):
                                j = theListLength-k+n
                                mverts[j] = mverts[j-1]
                            mverts[n] = (bv, vec.length)
                            #print(bv.index)
                            #printMverts(bv.index, mverts)
                            break
                        n += 1

        (mv, mindist) = mverts[0]
        if mv:
            if pv.index % 10 == 0:
                print(pv.index, mv.index, mindist, gname, pindex, bindex)
            if log:
                log.write("%d %d %.5f %s %d %d\n" % (pv.index, mv.index, mindist, gname, pindex, bindex))
            #printMverts("  ", mverts)
        else:
            msg = (
            "Failed to find vert %d in group %s.\n" % (pv.index, gname) +
            "Proxy index %d, Base index %d\n" % (pindex, bindex) +
            "Vertex coordinates (%.4f %.4f %.4f)\n" % (pv.co[0], pv.co[1], pv.co[2])
            )
            selectVerts([pv], pob)
            raise error.MhcloError(msg)
        if mindist > 5:
            msg = (
            "Vertex %d is %f dm away from closest body vertex in group %s.\n" % (pv.index, mindist, gname) +
            "Max allowed value is 5dm. Check base and proxy scales.\n" +
            "Vertex coordinates (%.4f %.4f %.4f)\n" % (pv.co[0], pv.co[1], pv.co[2])
            )
            selectVerts([pv], pob)
            raise error.MhcloError(msg)

        if gname[0:3] != "Mid":
            bindex = -1
        bestVerts.append((pv, bindex, exact, mverts, []))

    print("Setting up face table")
    vfaces = {}
    for v in base.vertices:
        vfaces[v.index] = []            
    baseFaces = getFaces(base)
    for f in baseFaces:
        v0 = f.vertices[0]
        v1 = f.vertices[1]
        v2 = f.vertices[2]
        if len(f.vertices) == 4:
            v3 = f.vertices[3]
            t0 = [v0,v1,v2]
            t1 = [v1,v2,v3]
            t2 = [v2,v3,v0]
            t3 = [v3,v0,v1]
            vfaces[v0].extend( [t0,t2,t3] )
            vfaces[v1].extend( [t0,t1,t3] )
            vfaces[v2].extend( [t0,t1,t2] )
            vfaces[v3].extend( [t1,t2,t3] )
        else:
            t = [v0,v1,v2]
            vfaces[v0].append(t)
            vfaces[v1].append(t)
            vfaces[v2].append(t)
    
    print("Finding weights")
    for (pv, bindex, exact, mverts, fcs) in bestVerts:
        if exact:
            continue
        for (bv,mdist) in mverts:
            if bv:
                for f in vfaces[bv.index]:
                    v0 = base.vertices[f[0]]
                    v1 = base.vertices[f[1]]
                    v2 = base.vertices[f[2]]
                    if (bindex >= 0) and (pv.co[0] < 0.01) and (pv.co[0] > -0.01):
                        wts = midWeights(pv, bindex, v0, v1, v2, bob, pob)    
                    else:
                        wts = cornerWeights(pv, v0, v1, v2, bob, pob)
                    fcs.append((f, wts))

    print("Finding best weights")
    alwaysOutside = False
    minOffset = 0.0
    useProjection = False
    
    bestFaces = []
    badVerts = []
    for (pv, bindex, exact, mverts, fcs) in bestVerts:
        #print(pv.index)
        pv.select = False
        if exact:
            bestFaces.append((pv, True, mverts, 0, 0))
            continue
        minmax = -1e6
        for (fverts, wts) in fcs:
            w = minWeight(wts)
            if w > minmax:
                minmax = w
                bWts = wts
                bVerts = fverts
        if minmax < theThreshold:
            badVerts.append(pv.index)
            pv.select = True
            """
            if scn['MCForbidFailures']:
                selectVerts([pv], pob)
                print("Tried", mverts)
                msg = (
                "Did not find optimal triangle for %s vert %d.\n" % (pob.name, pv.index) +
                "Avoid the message by unchecking Forbid failures.")
                raise error.MhcloError(msg)
            """
            (mv, mdist) = mverts[0]
            bVerts = [mv.index,0,1]
            bWts = (1,0,0)

        v0 = base.vertices[bVerts[0]]
        v1 = base.vertices[bVerts[1]]
        v2 = base.vertices[bVerts[2]]
    
        est = bWts[0]*v0.co + bWts[1]*v1.co + bWts[2]*v2.co
        norm = bWts[0]*v0.normal + bWts[1]*v1.normal + bWts[2]*v2.normal
        diff = pv.co - est
        if useProjection:
            proj = diff.dot(norm)
            if alwaysOutside and proj < minOffset:
                proj = minOffset
            bestFaces.append((pv, False, bVerts, bWts, proj))    
        else:
            bestFaces.append((pv, False, bVerts, bWts, diff))    

    if badVerts:
        print("Optimal triangles not found for the following verts")
        n = 0
        nmax = len(badVerts)
        string = ""
        for vn in badVerts:
            string += "%6d " % vn
            n += 1
            if n%8 == 0:
                print(string)
                string = ""
        print(string)                
        print("Done")
    return bestFaces

#
#    minWeight(wts)
#

def minWeight(wts):
    best = 1e6
    for w in wts:
        if w < best:
            best = w
    return best

#
#    cornerWeights(pv, v0, v1, v2, bob, pob):
#
#    px = w0*x0 + w1*x1 + w2*x2
#    py = w0*y0 + w1*y1 + w2*y2
#    pz = w0*z0 + w1*z1 + w2*z2
#
#    w2 = 1-w0-w1
#
#    w0*(x0-x2) + w1*(x1-x2) = px-x2
#    w0*(y0-y2) + w1*(y1-y2) = py-y2
#
#    a00*w0 + a01*w1 = b0
#    a10*w0 + a11*w1 = b1
#
#    det = a00*a11 - a01*a10
#
#    det*w0 = a11*b0 - a01*b1
#    det*w1 = -a10*b0 + a00*b1
#

def cornerWeights(pv, v0, v1, v2, bob, pob):
    r0 = v0.co
    r1 = v1.co
    r2 = v2.co
    u01 = r1-r0
    u02 = r2-r0
    n = u01.cross(u02)
    n.normalize()

    u = pv.co-r0
    r = r0 + u - n*u.dot(n)

    """
    a00 = r0[0]-r2[0]
    a01 = r1[0]-r2[0]
    a10 = r0[1]-r2[1]
    a11 = r1[1]-r2[1]
    b0 = r[0]-r2[0]
    b1 = r[1]-r2[1]
    """    
    
    e0 = u01
    e0.normalize()
    e1 = n.cross(e0)
    e1.normalize()
    
    u20 = r0-r2
    u21 = r1-r2
    ur2 = r-r2
    
    a00 = u20.dot(e0)
    a01 = u21.dot(e0)
    a10 = u20.dot(e1)
    a11 = u21.dot(e1)
    b0 = ur2.dot(e0)
    b1 = ur2.dot(e1)
    
    det = a00*a11 - a01*a10
    if abs(det) < 1e-20:
        print("Clothes vert %d mapped to degenerate triangle (det = %g) with corners" % (pv.index, det))
        print("r0 ( %.6f  %.6f  %.6f )" % (r0[0], r0[1], r0[2]))
        print("r1 ( %.6f  %.6f  %.6f )" % (r1[0], r1[1], r1[2]))
        print("r2 ( %.6f  %.6f  %.6f )" % (r2[0], r2[1], r2[2]))
        print("A [ %.6f %.6f ]\n  [ %.6f %.6f ]" % (a00,a01,a10,a11))
        selectVerts([pv], pob)
        selectVerts([v0, v1, v2], bob)
        raise error.MhcloError("Singular matrix in cornerWeights")

    w0 = (a11*b0 - a01*b1)/det
    w1 = (-a10*b0 + a00*b1)/det
    
    return (w0, w1, 1-w0-w1)

#
#   midWeights(pv, bindex, v0, v1, v2, bob, pob):
#

def midWeights(pv, bindex, v0, v1, v2, bob, pob):
    #print("Mid", pv.index, bindex)
    pv.select = True
    if isInGroup(v0, bindex):
        v0.select = True
        if isInGroup(v1, bindex):
            v1.select = True    
            return midWeight(pv, v0.co, v1.co)
        elif isInGroup(v2, bindex):
            (w1, w0, w2) = midWeight(pv, v0.co, v2.co)
            v2.select = True
            return (w0, w1, w2)
    elif isInGroup(v1, bindex) and isInGroup(v2, bindex):            
        (w1, w2, w0) = midWeight(pv, v1.co, v2.co)
        v1.select = True
        v2.select = True
        return (w0, w1, w2)
    #print("  Failed mid")
    return cornerWeights(pv, v0, v1, v2, bob, pob)
    
def isInGroup(v, bindex):
    for g in v.groups:
        if g.group == bindex:
            return True
    return False            
    
def midWeight(pv, r0, r1):
    u01 = r1-r0    
    d01 = u01.length
    u = pv.co-r0
    s = u.dot(u01)
    w = s/(d01*d01)
    return (1-w, w, 0)

#
#    printClothes(context, bob, pob, data):
#
        
def printClothesHeader(fp, scn):
    fp.write(
"# author %s\n" % scn.MCAuthor +
"# license %s\n" % scn.MCLicense +
"# homepage %s\n" % scn.MCHomePage +
"# uuid %s\n" % uuid.uuid4() +
"# basemesh %s\n" % BaseMeshVersion)
    for n in range(1,6):
        tag = eval("scn.MCTag%d" % n)
        if tag:
            fp.write("# tag %s\n" % tag)
    fp.write("\n")            


def printClothes(context, bob, pob, data):
    scn = context.scene
    if isSelfClothed(context):
        firstVert = LastVertices[scn.MCSelfClothed]
        folder = scn.MCMakeHumanDirectory
        outfile = os.path.join(folder, "data/3dobjs/base.mhclo")
    else:
        firstVert = 0
        (outpath, outfile) = getFileName(pob, context, "mhclo")
    print("Creating clothes file %s" % outfile)
    fp= open(outfile, "w")
    printClothesHeader(fp, scn)
    fp.write("# name %s\n" % pob.name.replace(" ","_"))
    fp.write("# obj_file %s.obj\n" % goodName(pob.name))
    printScale(fp, bob, scn, 'x_scale', 0, 'MCX1', 'MCX2')
    printScale(fp, bob, scn, 'z_scale', 1, 'MCY1', 'MCY2')
    printScale(fp, bob, scn, 'y_scale', 2, 'MCZ1', 'MCZ2')

    if not isSelfClothed(context):
        printStuff(fp, pob, context)

    printFaceNumbers(fp, pob)
    fp.write("# verts %d\n" % (firstVert))
    for (pv, exact, verts, wts, diff) in data:
        if exact:
            (bv, dist) = verts[0]
            fp.write("%5d\n" % bv.index)
        else:
            fp.write("%5d %5d %5d %.5f %.5f %.5f %.5f %.5f %.5f\n" % (
                verts[0], verts[1], verts[2], wts[0], wts[1], wts[2], diff[0], diff[2], -diff[1]))
    fp.write('\n')
    printMhcloUvLayers(fp, pob, scn, True)
    fp.close()
    print("%s done" % outfile)    
    return
    

def printFaceNumbers(fp, ob):
    if len(ob.data.materials) <= 1:
        return
    fp.write("# faceNumbers\n")
    meFaces = getFaces(ob.data)
    mi = -1
    us = -1
    n = 0
    for f in meFaces:
        if (f.material_index == mi) and (f.use_smooth == us):
            n += 1
        else:
            if n > 1:
                fp.write("    ftn %d %d %d ;\n" % (n, mi, us))
            elif n > 0:
                fp.write("    ft %d %d ;\n" % (mi, us))
            mi = f.material_index
            us = f.use_smooth
            n = 1
    if n > 1:
        fp.write("    ftn %d %d %d ;\n" % (n, mi, us))
    elif n > 0:
        fp.write("    ft %d %d ;\n" % (mi, us))
    return

    
def printMhcloUvLayers(fp, pob, scn, hasObj):
    me = pob.data
    if me.uv_textures:      
        for layer,uvtex in enumerate(me.uv_textures):
            if hasObj and (layer == scn.MCTextureLayer):
                continue
            if scn.MCAllUVLayers or not hasObj:
                printLayer = layer
            else:
                printLayer = 1
                if layer != scn.MCMaskLayer:
                    continue
            (vertEdges, vertFaces, edgeFaces, faceEdges, faceNeighbors, uvFaceVertsList, texVertsList) = setupTexVerts(pob)
            texVerts = texVertsList[layer]
            uvFaceVerts = uvFaceVertsList[layer]
            nTexVerts = len(texVerts)
            fp.write("# texVerts %d\n" % printLayer)
            for vtn in range(nTexVerts):
                vt = texVerts[vtn]
                fp.write("%.4f %.4f\n" % (vt[0], vt[1]))
            fp.write("# texFaces %d\n" % printLayer)
            meFaces = getFaces(me)
            for f in meFaces:
                uvVerts = uvFaceVerts[f.index]
                for n,v in enumerate(f.vertices):
                    (vt, uv) = uvVerts[n]
                    fp.write("%d " % vt)
                    #fp.write("(%.3f %.3f) " % (uv[0], uv[1]))
                fp.write("\n")
    return

    
def reexportMhclo(context):
    pob = getClothing(context)
    scn = context.scene
    scn.objects.active = pob    
    bpy.ops.object.mode_set(mode='OBJECT')
    (outpath, outfile) = getFileName(pob, context, "mhclo")
        
    lines = []
    print("Reading clothes file %s" % outfile)
    fp = open(outfile, "r")
    for line in fp:
        lines.append(line)
    fp.close()        
            
    print("Creating new clothes file %s" % outfile)
    fp = open(outfile, "w")
    doingStuff = False
    for line in lines:
        words = line.split()
        if len(words) == 0:
            fp.write(line)                
        elif (words[0] == "#"):
            if words[1] in ["texVerts", "texFaces"]:
                break
            elif words[1] == "z_depth":
                printStuff(fp, pob, context)
                doingStuff = True
            elif words[1] == "use_projection":
                doingStuff = False
            elif doingStuff:
                pass
            else:            
                fp.write(line)                
        elif not doingStuff:                
            fp.write(line)                
    printMhcloUvLayers(fp, pob, scn, True)
    fp.close()
    print("%s written" % outfile)    
    return
    
      
#
#   printStuff(fp, pob, context): 
#   From z_depth to use_projection
#

def printStuff(fp, pob, context):
    scn = context.scene
    fp.write("# z_depth %d\n" % scn.MCZDepth)
    
    for mod in pob.modifiers:
        if mod.type == 'SHRINKWRAP':
            fp.write("# shrinkwrap %.3f\n" % (mod.offset))
        elif mod.type == 'SUBSURF':
            fp.write("# subsurf %d %d\n" % (mod.levels, mod.render_levels))
        elif mod.type == 'SOLIDIFY':
            fp.write("# solidify %.3f %.3f\n" % (mod.thickness, mod.offset))
            
    for skey in ShapeKeys:            
        if eval("scn.MC" + skey):
            fp.write("# shapekey %s\n" % skey)            
            
    me = pob.data            
    if scn.MCAllUVLayers:
        if me.uv_textures:
            for layer,uvtex in enumerate(me.uv_textures):
                fp.write("# uvtex_layer %d %s\n" % (layer, uvtex.name.replace(" ","_")))
            fp.write("# objfile_layer %d\n" % scn.MCTextureLayer)
        writeTextures(fp, goodName(pob.name), scn)
    else:        
        if me.uv_textures:
            uvtex0 = me.uv_textures[scn.MCTextureLayer]
            fp.write("# uvtex_layer 0 %s\n" % uvtex0.name.replace(" ","_"))
            uvtex1 = me.uv_textures[scn.MCMaskLayer]
            if scn.MCUseMask and uvtex1 != uvtex0:
                fp.write("# uvtex_layer 1 %s\n" % uvtex1.name.replace(" ","_"))
            fp.write("# objfile_layer 0\n")
        writeTextures(fp, goodName(pob.name), scn)
           
    if scn.MCHairMaterial:
        fp.write(
"# material %s\n" % pob.name +
"  texture data/hairstyles/%s_texture.tif %d\n" % (pob.name, scn.MCTextureLayer) +
"  diffuse_intensity 0.8\n" +
"  specular_intensity 0.0\n" +
"  specular_hardness 1\n" +
"  use_shadows 1\n" +
"  use_transparent_shadows 1\n" +
"  use_raytrace 1\n" +
"  use_transparency 1\n" +
"  alpha 0.0\n" +
"  specular_alpha 0.0\n" +
"  use_map_color_diffuse 1\n" +
"  use_map_alpha 1\n" +
"  use_alpha 1\n" +
"  diffuse_color_factor 1.0\n" +
"  alpha_factor 1.0\n")

    me = pob.data

    useMats = scn.MCMaterials
    useBlender = scn.MCBlenderMaterials
    alphaDone = False
    if me.materials and (useMats or useBlender) and me.materials[0]:
        mat = me.materials[0]
        fp.write("# material %s\n" % mat.name)
        if useMats:
            writeColor(fp, 'diffuse_color', 'diffuse_intensity', mat.diffuse_color, mat.diffuse_intensity)
            #fp.write('diffuse_shader %s\n' % mat.diffuse_shader)
            writeColor(fp, 'specular_color', 'specular_intensity', mat.specular_color, mat.specular_intensity)
            #fp.write('specular_shader %s\n' % mat.specular_shader)
            if scn.MCUseTrans:
                alpha = 0
            else:
                alpha = mat.alpha            
            fp.write("alpha %s\n" % alpha)
            alphaDone = True
        if useBlender:
            (outpath, outfile) = getFileName(pob, context, "mhx")
            mhxfile = exportBlenderMaterial(me, outpath)
            fp.write("# material_file %s\n" % mhxfile)
    elif not scn.MCHairMaterial:
        fp.write("# material %s\n" % pob.name.replace(" ","_"))
        if scn.MCUseTrans:
            fp.write("  alpha 0\n")
            
    fp.write("# use_projection 0\n")            
    return  
    
def writeTextures(fp, name, scn):        
    fp.write("# texture %s_texture.png %d\n" % (name, scn.MCTextureLayer))
    if scn.MCUseMask:
        fp.write("# mask %s_mask.png %d\n" % (name, scn.MCMaskLayer))
    if scn.MCUseBump:
        fp.write("# bump %s_bump.png %d %.3f\n" % (name, scn.MCTextureLayer, scn.MCBumpStrength))
    if scn.MCUseNormal:
        fp.write("# normal %s_normal.png %d %.3f\n" % (name, scn.MCTextureLayer, scn.MCNormalStrength))
    if scn.MCUseDisp:
        fp.write("# displacement %s_disp.png %d %.3f\n" % (name, scn.MCTextureLayer, scn.MCDispStrength))
    if scn.MCUseTrans:
        fp.write("# transparency %s_trans.png %d\n" % (name, scn.MCTextureLayer))
    return
    
#
#   deleteStrayVerts(context, ob):
#

def deleteStrayVerts(context, ob):
    scn = context.scene
    scn.objects.active = ob
    bpy.ops.object.mode_set(mode='OBJECT')
    verts = ob.data.vertices
    onFaces = {}
    for v in verts:
        onFaces[v.index] = False
    faces = getFaces(ob.data)
    for f in faces:
        for vn in f.vertices:
            onFaces[vn] = True
    for v in verts:
        if not onFaces[v.index]:
            raise NameError("Mesh %s has stray vert %d" % (ob.name, v.index))
        return
    
#
#   exportObjFile(context):
#

def exportObjFile(context):
    ob = getClothing(context)
    deleteStrayVerts(context, ob)
    (objpath, objfile) = getFileName(ob, context, "obj")
    print("Open", objfile)
    fp = open(objfile, "w")
    fp.write("# Exported from make_clothes.py\n")
    
    scn = context.scene
    me = ob.data
    for v in me.vertices:
        fp.write("v %.4f %.4f %.4f\n" % (v.co[0], v.co[2], -v.co[1]))
        
    for v in me.vertices:
        fp.write("vn %.4f %.4f %.4f\n" % (v.normal[0], v.normal[2], -v.normal[1]))
        
    if me.uv_textures:
        (vertEdges, vertFaces, edgeFaces, faceEdges, faceNeighbors, uvFaceVertsList, texVertsList) = setupTexVerts(ob)
        layer = scn.MCTextureLayer
        writeObjTextureData(fp, me, texVertsList[layer], uvFaceVertsList[layer])
    else:
        meFaces = getFaces(me)
        for f in meFaces:
            fp.write("f ")
            for v in f.vertices:
                fp.write("%d " % (v+1))
            fp.write("\n")

    fp.close()
    print(objfile, "closed")
    return
        
def writeObjTextureData(fp, me, texVerts, uvFaceVerts):    
    nTexVerts = len(texVerts)
    for vtn in range(nTexVerts):
        vt = texVerts[vtn]
        fp.write("vt %.4f %.4f\n" % (vt[0], vt[1]))
    meFaces = getFaces(me)
    for f in meFaces:
        uvVerts = uvFaceVerts[f.index]
        fp.write("f ")
        for n,v in enumerate(f.vertices):
            (vt, uv) = uvVerts[n]
            fp.write("%d/%d " % (v+1, vt+1))
        fp.write("\n")
    return        

def writeColor(fp, string1, string2, color, intensity):
    fp.write(
        "%s %.4f %.4f %.4f\n" % (string1, color[0], color[1], color[2]) +
        "%s %.4g\n" % (string2, intensity))

def printScale(fp, bob, scn, name, index, prop1, prop2):
    if not scn.MCIsMHMesh:
        return
    verts = bob.data.vertices
    n1 = eval("scn.%s" % prop1)
    n2 = eval("scn.%s" % prop2)
    if n1 >=0 and n2 >= 0:
        x1 = verts[n1].co[index]     
        x2 = verts[n2].co[index]
        fp.write("# %s %d %d %.4f\n" % (name, n1, n2, abs(x1-x2)))
    return

#
#   setupTexVerts(ob):
#

def setupTexVerts(ob):
    me = ob.data
    vertEdges = {}
    vertFaces = {}
    for v in me.vertices:
        vertEdges[v.index] = []
        vertFaces[v.index] = []
    for e in me.edges:
        for vn in e.vertices:
            vertEdges[vn].append(e)
    meFaces = getFaces(me)
    for f in meFaces:
        for vn in f.vertices:
            vertFaces[vn].append(f)
    
    edgeFaces = {}
    for e in me.edges:
        edgeFaces[e.index] = []
    faceEdges = {}
    for f in meFaces:
        faceEdges[f.index] = []
    for f in meFaces:
        for vn in f.vertices:
            for e in vertEdges[vn]:
                v0 = e.vertices[0]
                v1 = e.vertices[1]
                if (v0 in f.vertices) and (v1 in f.vertices):
                    if f not in edgeFaces[e.index]:
                        edgeFaces[e.index].append(f)
                    if e not in faceEdges[f.index]:
                        faceEdges[f.index].append(e)
            
    faceNeighbors = {}
    for f in meFaces:
        faceNeighbors[f.index] = []
    for f in meFaces:
        for e in faceEdges[f.index]:
            for f1 in edgeFaces[e.index]:
                if f1 != f:
                    faceNeighbors[f.index].append((e,f1))

    uvFaceVertsList = []
    texVertsList = []
    for index,uvtex in enumerate(me.uv_textures):
        uvFaceVerts = {}
        uvFaceVertsList.append(uvFaceVerts)
        for f in meFaces:
            uvFaceVerts[f.index] = []
        vtn = 0
        texVerts = {}    
        texVertsList.append(texVerts)
        if BMeshAware:
            uvloop = me.uv_layers[index]
            n = 0
            for f in me.polygons:
                for vn in f.vertices:
                    uvv = uvloop.data[n]
                    n += 1
                    vtn = findTexVert(uvv.uv, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob)
        else:
            for f in me.faces:
                uvf = uvtex.data[f.index]
                vtn = findTexVert(uvf.uv1, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob)
                vtn = findTexVert(uvf.uv2, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob)
                vtn = findTexVert(uvf.uv3, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob)
                if len(f.vertices) > 3:
                    vtn = findTexVert(uvf.uv4, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob)
    return (vertEdges, vertFaces, edgeFaces, faceEdges, faceNeighbors, uvFaceVertsList, texVertsList)     

def findTexVert(uv, vtn, f, faceNeighbors, uvFaceVerts, texVerts, ob):
    for (e,f1) in faceNeighbors[f.index]:
        for (vtn1,uv1) in uvFaceVerts[f1.index]:
            vec = uv - uv1
            if vec.length < 1e-8:
                uvFaceVerts[f.index].append((vtn1,uv))                
                return vtn
    uvFaceVerts[f.index].append((vtn,uv))
    texVerts[vtn] = uv
    return vtn+1

#
#   exportBaseUvsPy(context):
#

def exportBaseUvsPy(context):
    ob = context.object
    bpy.ops.object.mode_set(mode='OBJECT')
    scn = context.scene
    (vertEdges, vertFaces, edgeFaces, faceEdges, faceNeighbors, uvFaceVertsList, texVertsList) = setupTexVerts(ob)
    maskLayer = scn.MCMaskLayer
    texVerts = texVertsList[maskLayer]
    uvFaceVerts = uvFaceVertsList[maskLayer]    
    nTexVerts = len(texVerts)

    folder = scn.MCMakeHumanDirectory
    fname = os.path.join(folder, "utils/makeclothes/base_uv.py")
    print("Creating", fname)
    fp = open(fname, "w")
    fp.write("firstVert = %d\n" % NBodyVerts)
    fp.write("firstFace = %d\n" % NBodyFaces)
    fp.write("texFaces = [\n")
    meFaces = getFaces(ob.data)
    for f in meFaces:
        uvVerts = uvFaceVerts[f.index]
        fp.write("  ( ")
        for n,v in enumerate(f.vertices):
            (vt, uv) = uvVerts[n]
            fp.write("(%.4f, %.4f), " % (uv[0], uv[1]))
        fp.write("),\n")
    fp.write("]\n")
    fp.close()
    return
        

#
#   storeData(pob, bob, data):
#   restoreData(context):    
#

def storeData(pob, bob, data):
    fname = settingsFile("stored")
    fp = open(fname, "w")
    fp.write("%s\n" % pob.name)
    fp.write("%s\n" % bob.name)
    for (pv, exact, verts, wts, diff) in data:
        #print(pv,exact)
        fp.write("%d %d\n" % (pv.index, exact))
        #print(verts)
        fp.write("%s\n" % verts)
        if not exact:
            #print(wts)
            fp.write("(%s,%s,%s)\n" % wts)
            #print(diff)
            fp.write("(%s,%s,%s)\n" % (diff[0],diff[1],diff[2]))
    fp.close()
    return
    
    
def restoreData(context): 
    (bob, pob) = getObjectPair(context)
    fname = settingsFile("stored")
    fp = open(fname, "rU")
    status = 0
    data = []
    for line in fp:
        #print(line)
        words = line.split()
        if status == 0:
            pname = line.rstrip()
            if pname != pob.name:
                raise error.MhcloError(
                "Restore error: stored data for %s does not match selected object %s\n" % (pname, pob.name) +
                "Make clothes for %s first\n" % pob.name)
            status = 10
        elif status == 10:
            bname = line.rstrip()
            if bname != bob.name:
                raise error.MhcloError(
                "Restore error: stored human %s does not match selected human %s\n" % (bname, bob.name) +
                "Make clothes for %s first\n" % pob.name)
            status = 1
        elif status == 1:
            pv = pob.data.vertices[int(words[0])]
            exact = int(words[1])
            status = 2
        elif status == 2:
            verts = eval(line)
            if exact:
                data.append((pv, exact, verts, 0, 0))
                status = 1
            else:
                status = 3
        elif status == 3:
            wts = eval(line)
            status = 4
        elif status == 4:
            diff = Vector( eval(line) )
            data.append((pv, exact, verts, wts, diff))
            status = 1
    bob = context.scene.objects[bname]
    return (bob, data)

#
#   unwrapObject(ob, context):
#

def unwrapObject(ob, context):
    scn = context.scene
    old = scn.objects.active
    scn.objects.active = ob
    
    n = len(ob.data.uv_textures)-1
    if n < scn.MCMaskLayer:
        while n < scn.MCMaskLayer:
            ob.data.uv_textures.new()
            n += 1
        ob.data.uv_textures[n].name = "Mask"
    ob.data.uv_textures.active_index = scn.MCMaskLayer        
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    scn.objects.active = old
    return

#
#   projectUVs(bob, pob, context):
#

def printItems(struct):
    for (key,value) in struct.items():
        print(key, value)
    

def projectUVs(bob, pob, context):
    print("Projecting %s => %s" % (bob.name, pob.name))
    (bob1, data) = restoreData(context)
    scn = context.scene

    (bVertEdges, bVertFaces, bEdgeFaces, bFaceEdges, bFaceNeighbors, bUvFaceVertsList, bTexVertsList) = setupTexVerts(bob)
    bUvFaceVerts = bUvFaceVertsList[0]
    bTexVerts = bTexVertsList[0]
    bNTexVerts = len(bTexVerts)
    table = {}
    bFaces = getFaces(bob.data)
    bTexFaces = getTexFaces(bob.data, 0)
    if scn.MCIsMHMesh:
        modifyTexFaces(bFaces, bTexFaces)
    for (pv, exact, verts, wts, diff) in data:
        if exact:
            (v0, x) = verts[0]            
            vn0 = v0.index
            for f0 in bVertFaces[vn0]:
                uvf = bTexFaces[f0.index].uvs
                uv0 = getUvLoc(vn0, f0, uvf)
                table[pv.index] = (1, uv0, 1)
                break
        else:
            vn0 = verts[0]
            vn1 = verts[1]
            vn2 = verts[2]
            if (vn1 == 0) and (vn2 == 1) and (abs(wts[0]-1) < Epsilon):
                uvVerts = []
                for f0 in bVertFaces[vn0]:
                    uvf = bTexFaces[f0.index].uvs
                    uv0 = getUvLoc(vn0, f0, uvf)
                    uvVerts.append(uv0)
                table[pv.index] = (2, uvVerts, wts)
                continue
            for f0 in bVertFaces[vn0]:
                for f1 in bVertFaces[vn1]:
                    if (f1 == f0):
                        for f2 in bVertFaces[vn2]:
                            if (f2 == f0):
                                uvf = bTexFaces[f0.index].uvs
                                uv0 = getUvLoc(vn0, f0, uvf)
                                uv1 = getUvLoc(vn1, f0, uvf)
                                uv2 = getUvLoc(vn2, f0, uvf)
                                table[pv.index] = (0, [uv0,uv1,uv2], wts)
        
    (pVertEdges, pVertFaces, pEdgeFaces, pFaceEdges, pFaceNeighbors, pUvFaceVertsList, pTexVertsList) = setupTexVerts(pob)
    maskLayer = context.scene.MCMaskLayer
    pUvFaceVerts = pUvFaceVertsList[maskLayer]
    pTexVerts = pTexVertsList[maskLayer]
    pNTexVerts = len(pTexVerts)
    (pSeamEdgeFaces, pSeamVertEdges, pBoundaryVertEdges, pVertTexVerts) = getSeamData(pob.data, pUvFaceVerts, pEdgeFaces)
    pTexVertUv = {}
    for vtn in range(pNTexVerts):
        pTexVertUv[vtn] = None
        
    pTexFaces = getTexFaces(pob.data, maskLayer)
    pverts = pob.data.vertices
    bverts = bob.data.vertices
    bedges = bob.data.edges
    remains = {}
    zero = (0,0)
    uvIndex = 0
    pMeFaces = getFaces(pob.data)
    for pf in pMeFaces:
        fn = pf.index
        rmd = {}
        rmd[0] = None
        rmd[1] = None
        rmd[2] = None
        rmd[3] = None
        remains[fn] = rmd
        
        uvf = pTexFaces[fn]
        for n,pvn in enumerate(pf.vertices):
            uv = getSingleUvLoc(pvn, table)
            uv = trySetUv(pvn, fn, uvf, rmd, n, uv, pVertTexVerts, pTexVertUv, pSeamVertEdges)
            if uv: 
                uvf.set(n, uv)

    (bVertList, bPairList, bEdgeList) = getSeams(bob, bTexFaces, context.scene)  
    for (en,fcs) in pSeamEdgeFaces.items():
        pe = pob.data.edges[en]
        for m in range(2):
            pv = pverts[pe.vertices[m]]
            be = findClosestEdge(pv, bEdgeList, bverts, bedges)
            for pf in fcs:
                fn = pf.index
                for (n, rmd) in remains[fn].items():
                    if rmd:
                        (uvf, pvn, vt, uv0) = rmd
                        if pv.index == pvn:
                            if pTexVertUv[vt]:
                                uv = pTexVertUv[vt]
                            else:
                                uv = getSeamVertFaceUv(pv, pe, pf, pVertTexVerts, pTexVertUv, be, bEdgeFaces, bTexFaces, pverts, bverts)
                                pTexVertUv[vt] = uv
                            uvf.set(n, uv)
                            remains[fn][n] = None
    
    for pf in pMeFaces:
        rmd = remains[pf.index]
        for n in range(4):
            if rmd[n]:
                (uvf, pvn, vt, uv) = rmd[n]
                pverts[pvn].select = True
                if pTexVertUv[vt]:
                    uv = pTexVertUv[vt]
                else:
                    pTexVertUv[vt] = uv
                uvf.set(n, uv)
    return                


def modifyTexFaces(meFaces, texFaces):
    nFaces = len(meFaces)
    nModFaces = len(base_uv.texFaces)
    if nFaces < NBodyFaces + nModFaces:
        nModFaces = nFaces - NBodyFaces
    for n in range(nModFaces):
        tf = base_uv.texFaces[n]
        texFaces[n+NBodyFaces].uvs = [Vector(tf[0]), Vector(tf[1]), Vector(tf[2]), Vector(tf[3])]
     

def trySetUv(pvn, fn, uvf, rmd, n, uv, vertTexVerts, texVertUv, seamVertEdges):        
    (vt, uv_old) = vertTexVerts[pvn][fn]
    if texVertUv[vt]:
        return texVertUv[vt]
    elif not seamVertEdges[pvn]:
        texVertUv[vt] = uv
        return uv
    else:
        rmd[n] = (uvf, pvn, vt, uv)
        return None


def findClosestEdge(pv, edgeList, verts, edges):
    mindist = 1e6
    for e in edgeList:
        vec0 = pv.co - verts[e.vertices[0]].co
        vec1 = pv.co - verts[e.vertices[1]].co
        dist = vec0.length + vec1.length
        if dist < mindist:
            mindist = dist
            best = e
    return best
        

def getSeamVertFaceUv(pv, pe, pf, pVertTexVerts, pTexVertUv, be, bEdgeFaces, bTexFaces, pverts, bverts):
    dist = {}
    for bf in bEdgeFaces[be.index]:
        dist[bf.index] = 0
    for pvn in pf.vertices:
        (vt, uv_old) = pVertTexVerts[pvn][pf.index]
        puv = pTexVertUv[vt]
        if puv:
            for bf in bEdgeFaces[be.index]:
                for n,bvn in enumerate(bf.vertices):
                    buvf = bTexFaces[bf.index]
                    #buv = getUvVert(buvf, n)
                    buv = buvf.get(n)
                    duv = buv - puv
                    dist[bf.index] += duv.length

    mindist = 1e6
    for bf in bEdgeFaces[be.index]:
        if dist[bf.index] < mindist:
            mindist = dist[bf.index]
            best = bf
            
    bv0 = bverts[be.vertices[0]]
    bv1 = bverts[be.vertices[1]]
    m0 = getFaceIndex(bv0.index, best)
    m1 = getFaceIndex(bv1.index, best)
    buvf = bTexFaces[best.index]
    #buv0 = getUvVert(buvf, m0)
    #buv1 = getUvVert(buvf, m1)
    buv0 = buvf.get(m0)
    buv1 = buvf.get(m1)
    vec0 = pv.co - bv0.co
    vec1 = pv.co - bv1.co
    vec = bv0.co - bv1.co
    dist0 = abs(vec.dot(vec0))
    dist1 = abs(vec.dot(vec1))
    eps = dist1/(dist0+dist1)    
    uv = eps*buv0 + (1-eps)*buv1
    return uv
    
    best.select = True
    pf.select = True
    bv0.select = True
    bv1.select = True
    pv.select = True
    print(uv)
    print("  ", buv0)
    print("  ", buv1)
    foo
    
    return uv

    
def getFaceIndex(vn, f):
    n = 0
    for vn1 in f.vertices:
        if vn1 == vn:
            #print(v.index, n, list(f.vertices))            
            return n
        n += 1
    raise error.MhcloError("Vert %d not in face %d %s" % (vn, f.index, list(f.vertices)))


def getSeamData(me, uvFaceVerts, edgeFaces):    
    seamEdgeFaces = {}
    seamVertEdges = {}
    boundaryEdges = {}
    vertTexVerts = {}
    verts = me.vertices

    for v in me.vertices:
        vn = v.index
        seamVertEdges[vn] = []
        vertTexVerts[vn] = {}
        v.select = False

    meFaces = getFaces(me)
    for f in meFaces:
        fn = f.index
        for vn in f.vertices:
            n = getFaceIndex(vn, f)
            uvf = uvFaceVerts[fn]
            vertTexVerts[vn][fn]= uvf[n]

    for e in me.edges:
        en = e.index
        fcs = edgeFaces[en]
        if len(fcs) < 2:
            boundaryEdges[en] = True
            e.select = False
        else:
            vn0 = e.vertices[0]
            vn1 = e.vertices[1]
            if isSeam(vn0, vn1, fcs[0], fcs[1], vertTexVerts):
                #e.select = True
                seamEdgeFaces[en] = fcs
                seamVertEdges[vn0].append(e)
                seamVertEdges[vn1].append(e)
            else:
                e.select = False
    return (seamEdgeFaces, seamVertEdges, boundaryEdges, vertTexVerts)            


def isSeam(vn0, vn1, f0, f1, vertTexVerts):
    (vt00, uv00) = vertTexVerts[vn0][f0.index]
    (vt01, uv01) = vertTexVerts[vn1][f0.index]
    (vt10, uv10) = vertTexVerts[vn0][f1.index]
    (vt11, uv11) = vertTexVerts[vn1][f1.index]
    d00 = uv00-uv10
    d11 = uv01-uv11
    d01 = uv00-uv11
    d10 = uv01-uv10
    #test1 = ((vt00 == vt10) and (vt01 == vt11))
    #test2 = ((vt00 == vt11) and (vt01 == vt10))
    test1 = ((d00.length < Epsilon) and (d11.length < Epsilon))
    test2 = ((d01.length < Epsilon) and (d10.length < Epsilon))
    if (test1 or test2):
        return False
    else:
        return True
        print("%d %s" % (vt00, uv00))
        print("%d %s" % (vt01, uv01))
        print("%d %s" % (vt10, uv10))
        print("%d %s" % (vt11, uv11))


def createFaceTable(verts, faces):
    table = {}
    for v in verts:
        table[v.index] = []
    for f in faces:
        for v in f.vertices:
            table[v].append(f)
    return table            


def getSingleUvLoc(vn, table):
    (exact, buvs, wts) = table[vn]
    if exact == 1:
        return buvs
    elif exact == 2:
        return buvs[0]
    else:
        try:
            return buvs[0]*wts[0] + buvs[1]*wts[1] + buvs[2]*wts[2]
        except:
            for n in range(3):
                print(buvs[n], wts[n])
            halt
        

def getUvLoc(vn, f, uvface):
    for n,vk in enumerate(f.vertices):
        if vk == vn:
            return uvface[n]
    raise error.MhcloError("Vertex %d not in face %d??" % (vn,f))

#
#   recoverSeams(context):
#

def recoverSeams(context):
    ob = getHuman(context)
    scn = context.scene
    getFaces(ob.data)
    texFaces = getTexFaces(ob.data, 0)
    (vertList, pairList, edgeList) = getSeams(ob, texFaces, scn)
    vcoList = coordList(vertList, ob.data.vertices)
    sme = bpy.data.meshes.new("Seams")
    sme.from_pydata(vcoList, pairList, [])
    sme.update(calc_edges=True)
    sob = bpy.data.objects.new("Seams", sme)
    sob.show_x_ray = True
    scn.objects.link(sob)            
    print("Seams recovered for object %s\n" % ob.name)
    return    


def setSeams(context):
    scn = context.scene
    clothing = None
    seams = None
    for ob in scn.objects:
        if ob.select and not isHuman(ob):
            faces = getFaces(ob.data)
            if faces:
                clothing = ob
            else:
                seams = ob
    if not (clothing and seams):
        raise error.MhcloError("A clothing and a seam object must be selected")
    checkObjectOK(clothing, context)
    checkObjectOK(seams, context)

    for e in clothing.data.edges:
        e.use_seam = False
        
    for se in seams.data.edges:
        dist = 1e6
        sv0 = seams.data.vertices[se.vertices[0]]
        sv1 = seams.data.vertices[se.vertices[1]]
        best = None
        for e in clothing.data.edges:
            v0 = clothing.data.vertices[e.vertices[0]]
            v1 = clothing.data.vertices[e.vertices[1]]
            d00 = v0.co - sv0.co
            d01 = v0.co - sv1.co
            d10 = v1.co - sv0.co
            d11 = v1.co - sv1.co
            d0 = d00.length + d11.length
            d1 = d01.length + d10.length
            if d1 < d0:
                d0 = d1
            if d0 < dist:
                dist = d0
                best = e
        best.use_seam = True
        best.select = True
        if se.index % 100 == 0:
            print(se.index)
    print("Seams set for object %s\n" % clothing.name)
    return        
    
            
def coordList(vertList, verts):
    coords = []
    for vn in vertList:
        coords.append(verts[vn].co)
    return coords        

    
def getSeams(ob, texFaces, scn):
    verts = ob.data.vertices
    meFaces = getFaces(ob.data)
    faceTable = createFaceTable(verts, meFaces)
    onEdges = {}
    for v in verts:
        onEdges[v.index] = False
    for v in ob.data.vertices:
        if isOnEdge(v, faceTable, texFaces):
            onEdges[v.index] = True

    vertList = []
    edgeList = []
    pairList = []
    n = 0
    for e in ob.data.edges:
        v0 = e.vertices[0]
        v1 = e.vertices[1]
        e.use_seam = (onEdges[v0] and onEdges[v1])
        if e.use_seam:
            vertList += [v0, v1]
            pairList.append((n,n+1))            
            n += 2
            edgeList.append(e)
    return (vertList, pairList, edgeList)            

        
def isOnEdge(v, faceTable, texFaces):  
    if v.index >= NBodyVerts:
        return False
    uvloc = None
    for f in faceTable[v.index]:
        uvface = texFaces[f.index].uvs
        #print("F", v.index, f.index, uvface)
        for n,vn in enumerate(f.vertices):
            if vn == v.index:
                uvnloc = uvface[n]
                if uvloc:
                    dist = uvnloc - uvloc
                    if dist.length > 0.01:
                        return True
                else:
                    uvloc = uvnloc
    return False                            

#
#    makeClothes(context, doFindClothes):
#

def makeClothes(context, doFindClothes):
    (bob, pob) = getObjectPair(context)
    scn = context.scene
    checkObjectOK(bob, context)
    checkAndVertexDiamonds(scn, bob)
    checkObjectOK(pob, context)
    checkSingleVGroups(pob)
    if scn.MCLogging:
        logfile = '%s/clothes.log' % scn.MCDirectory
        log = open(logfile, "w")
    else:
        log = None
    if doFindClothes:
        data = findClothes(context, bob, pob, log)
        storeData(pob, bob, data)
    else:
        (bob, data) = restoreData(context)
    printClothes(context, bob, pob, data)
    if log:
        log.close()
    if isSelfClothed(context):
        scn.objects.unlink(bob)
        scn.objects.unlink(pob)
    return
    
#
#   checkObjectOK(ob, context):
#

def checkObjectOK(ob, context):
    old = context.object
    context.scene.objects.active = ob
    word = None
    error = False
    if ob.location.length > Epsilon:
        word = "object translation"
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    eu = ob.rotation_euler
    if abs(eu.x) + abs(eu.y) + abs(eu.z) > Epsilon:
        word = "object rotation"
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    vec = ob.scale - Vector((1,1,1))
    if vec.length > Epsilon:
        word = "object scaling"
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if ob.constraints:
        word = "constraints"
        error = True
    for mod in ob.modifiers:
        if (mod.type in ['CHILD_OF', 'ARMATURE']) and mod.show_viewport:
            word = "an enabled %s modifier" % mod.type
            mod.show_viewport = False
    if ob.parent:
        word = "parent"
        ob.parent = None
    if word:
        msg = "Object %s can not be used for clothes creation because it has %s.\n" % (ob.name, word)
        if error:
            msg +=  "Apply or delete before continuing.\n"
            print(msg)
            raise error.MhcloError(msg)
        else:
            print(msg)
            print("Fixed automatically")
    context.scene.objects.active = old
    return    

#
#   checkSingleVGroups(pob):
#

def checkSingleVGroups(pob):
    for v in pob.data.vertices:
        n = 0
        for g in v.groups:
            #print("Key", g.group, g.weight)
            n += 1
        if n != 1:
            v.select = True
            raise error.MhcloError("Vertex %d in %s belongs to %d groups. Must be exactly one" % (v.index, pob.name, n))
    return            
        
#
#   offsetCloth(context):
#

def offsetCloth(context):
    (bob, pob) = getObjectPair(context)
    bverts = bob.data.vertices
    pverts = pob.data.vertices    
    print("Offset %s to %s" % (bob.name, pob.name))

    inpath = '%s/%s.mhclo' % (context.scene.MCDirectory, goodName(bob.name))
    infile = os.path.realpath(os.path.expanduser(inpath))
    outpath = '%s/%s.mhclo' % (context.scene.MCDirectory, goodName(pob.name))
    outfile = os.path.realpath(os.path.expanduser(outpath))
    print("Modifying clothes file %s => %s" % (infile, outfile))
    infp = open(infile, "r")
    outfp = open(outfile, "w")

    status = 0
    alwaysOutside = context.scene['MCOutside']
    minOffset = context.scene['MCMinOffset']

    for line in infp:
        words = line.split()
        if len(words) < 1:
            outfp.write(line)
        elif words[0] == "#":    
            if len(words) < 2:
                status = 0
                outfp.write(line)
            elif words[1] == "verts":
                status = 1
                outfp.write(line)
            elif words[1] == "obj_data":
                if context.scene.MCVertexGroups:
                    infp.close()
                    writeFaces(pob, outfp) 
                    writeVertexGroups(pob, outfp)
                    outfp.close()
                    print("Clothes file modified %s => %s" % (infile, outfile))
                    return
                outfp.write(line)
                status = 0
            elif words[1] == "name":
                outfp.write("# name %s\n" % pob.name.replace(" ","_"))
            else:
                outfp.write(line)
            vn = 0
        elif status == 1:
            # 4715  5698  5726 0.00000 1.00000 -0.00000 0.00921
            verts = [int(words[0]), int(words[1]), int(words[2])]
            wts = [float(words[3]), float(words[4]), float(words[5])]
            bv = bverts[vn]
            pv = pverts[vn]
            diff = pv.co - bv.co
            proj = diff.dot(bv.normal)
            print(diff, proj)
            if alwaysOutside and proj < minOffset:
                proj = minOffset
            outfp.write("%5d %5d %5d %.5f %.5f %.5f %.5f\n" % (
                verts[0], verts[1], verts[2], wts[0], wts[1], wts[2], proj))
            # print(vn, bv.co, pv.co)
            vn += 1
        else:
            outfp.write(line)

    infp.close()
    outfp.close()
    print("Clothes file modified %s => %s" % (infile, outfile))
    return

def writeFaces(pob, fp):
    fp.write("# faces\n")
    meFaces = getFaces(pob.data)
    for f in meFaces:
        for v in f.vertices:
            fp.write(" %d" % (v+1))
        fp.write("\n")
    return

def writeVertexGroups(pob, fp):
    for vg in pob.vertex_groups:
        fp.write("# weights %s\n" % vg.name)
        for v in pob.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 1e-4:
                    fp.write(" %d %.4g \n" % (v.index, g.weight))
    return

###################################################################################    
#
#   Export of clothes material
#
###################################################################################    

def exportBlenderMaterial(me, path):
    mats = []
    texs = []
    for mat in me.materials:
        if mat:
            mats.append(mat)
            for mtex in mat.texture_slots:
                if mtex:
                    tex = mtex.texture
                    if tex and (tex not in texs):
                        texs.append(tex)
    
    matname = goodName(mats[0].name)
    mhxfile = "%s_material.mhx" % matname
    mhxpath = os.path.join(path, mhxfile)
    print("Open %s" % mhxpath)
    fp = open(mhxpath, "w")
    for tex in texs:
        exportTexture(tex, matname, fp)
    for mat in mats:
        exportMaterial(mat, fp)
    fp.close()
    return "%s" % mhxfile

#
#    exportMaterial(mat, fp):
#    exportMTex(index, mtex, use, fp):
#    exportTexture(tex, fp):
#    exportImage(img, fp)
#

def exportMaterial(mat, fp):
    fp.write("Material %s \n" % mat.name)
    for (n,mtex) in enumerate(mat.texture_slots):
        if mtex:
            exportMTex(n, mtex, mat.use_textures[n], fp)
    prio = ['diffuse_color', 'diffuse_shader', 'diffuse_intensity', 
        'specular_color', 'specular_shader', 'specular_intensity']
    writePrio(mat, prio, "  ", fp)
    exportRamp(mat.diffuse_ramp, 'diffuse_ramp', fp)
    exportRamp(mat.specular_ramp, 'specular_ramp', fp)
    exclude = []
    exportDefault("Halo", mat.halo, [], [], exclude, [], '  ', fp)
    exclude = []
    exportDefault("RaytraceTransparency", mat.raytrace_transparency, [], [], exclude, [], '  ', fp)
    exclude = []
    exportDefault("SSS", mat.subsurface_scattering, [], [], exclude, [], '  ', fp)
    exclude = ['use_surface_diffuse']
    exportDefault("Strand", mat.strand, [], [], exclude, [], '  ', fp)
    writeDir(mat, prio+['texture_slots', 'volume', 'node_tree',
        'diffuse_ramp', 'specular_ramp', 'use_diffuse_ramp', 'use_specular_ramp', 
        'halo', 'raytrace_transparency', 'subsurface_scattering', 'strand',
        'is_updated', 'is_updated_data'], "  ", fp)
    fp.write("end Material\n\n")
    return

MapToTypes = {
    'use_map_alpha' : 'ALPHA',
    'use_map_ambient' : 'AMBIENT',
    'use_map_color_diffuse' : 'COLOR',
    'use_map_color_emission' : 'COLOR_EMISSION',
    'use_map_color_reflection' : 'COLOR_REFLECTION',
    'use_map_color_spec' : 'COLOR_SPEC',
    'use_map_color_transmission' : 'COLOR_TRANSMISSION',
    'use_map_density' : 'DENSITY',
    'use_map_diffuse' : 'DIFFUSE',
    'use_map_displacement' : 'DISPLACEMENT',
    'use_map_emission' : 'EMISSION',
    'use_map_emit' : 'EMIT', 
    'use_map_hardness' : 'HARDNESS',
    'use_map_mirror' : 'MIRROR',
    'use_map_normal' : 'NORMAL',
    'use_map_raymir' : 'RAYMIR',
    'use_map_reflect' : 'REFLECTION',
    'use_map_scatter' : 'SCATTERING',
    'use_map_specular' : 'SPECULAR_COLOR', 
    'use_map_translucency' : 'TRANSLUCENCY',
    'use_map_warp' : 'WARP',
}

def exportMTex(index, mtex, use, fp):
    tex = mtex.texture
    texname = tex.name.replace(' ','_')
    mapto = None
    prio = []
    for ext in MapToTypes.keys():
        if eval("mtex.%s" % ext):
            if mapto == None:
                mapto = MapToTypes[ext]
            prio.append(ext)    
    fp.write("  MTex %d %s %s %s\n" % (index, texname, mtex.texture_coords, mapto))
    writePrio(mtex, ['texture']+prio, "    ", fp)
    writeDir(mtex, list(MapToTypes.keys()) + [
        'texture', 'type', 'texture_coords', 'offset', 'is_updated', 'is_updated_data'], "    ", fp)
    fp.write("  end MTex\n\n")
    return

def exportTexture(tex, matname, fp):
    if not tex:
        return
    if tex.type == 'IMAGE' and tex.image:
        exportImage(tex.image, matname, fp)
        fp.write("Texture %s %s\n" % (tex.name, tex.type))
        fp.write("  Image %s ;\n" % tex.image.name)
    else:
        fp.write("Texture %s %s\n" % (tex.name, tex.type))

    exportRamp(tex.color_ramp, "color_ramp", fp)
    writeDir(tex, [
        'color_ramp', 'node_tree', 'image_user', 'use_nodes', 'use_textures', 'type', 
        'users_material', 'is_updated', 'is_updated_data'], "  ", fp)
    fp.write("end Texture\n\n")

def exportImage(img, matname, fp):
    imgName = img.name
    if imgName == 'Render_Result':
        return
    fp.write(
"Image %s\n" % imgName +
"  Filename %s ;\n" % os.path.basename(img.filepath) +
"    use_premultiply %s ;\n" %  img.use_premultiply +
"end Image\n\n")
    return

def exportRamp(ramp, name, fp):
    if ramp == None:
        return
    print(ramp)
    fp.write("  Ramp %s\n" % name)

    for elt in ramp.elements:
        col = elt.color
        fp.write("    Element (%.3f,%.3f,%.3f,%.3f) %.3f ;\n" % (col[0], col[1], col[2], col[3], elt.position))
    writeDir(ramp, ['elements'], "    ", fp)
    fp.write("  end Ramp\n")


#
#    writePrio(data, prio, pad, fp):
#    writeDir(data, exclude, pad, fp):
#

def writePrio(data, prio, pad, fp):
    for ext in prio:
        writeExt(ext, "data", [], pad, 0, fp, globals(), locals())

def writeDir(data, exclude, pad, fp):
    for ext in dir(data):
        writeExt(ext, "data", exclude, pad, 0, fp, globals(), locals())

def writeQuoted(arg, fp):
    typ = type(arg)
    if typ == int or typ == float or typ == bool:
        fp.write("%s" % arg)
    elif typ == str:
        fp.write("'%s'"% stringQuote(arg))
    elif len(arg) > 1:
        c = '['
        for elt in arg:
            fp.write(c)
            writeQuoted(elt, fp)
            c = ','
        fp.write("]")
    else:
        raise error.MhcloError("Unknown property %s %s" % (arg, typ))
        fp.write('%s' % arg)

def stringQuote(string):
    s = ""
    for c in string:
        if c == '\\':
            s += "\\\\"
        elif c == '\"':
            s += "\\\""
        elif c == '\'':
            s += "\\\'"
        else:
            s += c
    return s
        
            
#
#    writeExt(ext, name, exclude, pad, depth, fp, globals, locals):        
#

def writeExt(ext, name, exclude, pad, depth, fp, globals, locals):        
    expr = name+"."+ext
    try:
        arg = eval(expr, globals, locals)
        success = True
    except:
        success = False
        arg = None
    if success:
        writeValue(ext, arg, exclude, pad, depth, fp)
    return

#
#    writeValue(ext, arg, exclude, pad, depth, fp):
#

excludeList = [
    'bl_rna', 'fake_user', 'id_data', 'rna_type', 'name', 'tag', 'users', 'type'
]

def writeValue(ext, arg, exclude, pad, depth, fp):
    if (len(str(arg)) == 0 or
        arg == None or
        arg == [] or
        ext[0] == '_' or
        ext in excludeList or
        ext in exclude):
        return
        
    if ext == 'end':
        print("RENAME end", arg)
        ext = '\\ end'

    typ = type(arg)
    if typ == int:
        fp.write("%s%s %d ;\n" % (pad, ext, arg))
    elif typ == float:
        fp.write("%s%s %.3f ;\n" % (pad, ext, arg))
    elif typ == bool:
        fp.write("%s%s %s ;\n" % (pad, ext, arg))
    elif typ == str:
        fp.write("%s%s '%s' ;\n" % (pad, ext, stringQuote(arg.replace(' ','_'))))
    elif typ == list:
        fp.write("%s%s List\n" % (pad, ext))
        n = 0
        for elt in arg:
            writeValue("[%d]" % n, elt, [], pad+"  ", depth+1, fp)
            n += 1
        fp.write("%send List\n" % pad)
    elif typ == Vector:
        c = '('
        fp.write("%s%s " % (pad, ext))
        for elt in arg:
            fp.write("%s%.3f" % (c,elt))
            c = ','
        fp.write(") ;\n")
    else:
        try:
            r = arg[0]
            g = arg[1]
            b = arg[2]
        except:
            return
        if (type(r) == float) and (type(g) == float) and (type(b) == float):
            fp.write("%s%s (%.4f,%.4f,%.4f) ;\n" % (pad, ext, r, g, b))
            print(ext, arg)
    return 

#
#    exportDefault(typ, data, header, prio, exclude, arrays, pad, fp):
#

def exportDefault(typ, data, header, prio, exclude, arrays, pad, fp):
    if not data:
        return
    try:
        if not data.enabled:
            return
    except:
        pass
    try:
        name = data.name
    except:
        name = ''

    fp.write("%s%s %s" % (pad, typ, name))
    for val in header:
        fp.write(" %s" % val)
    fp.write("\n")
    writePrio(data, prio, pad+"  ", fp)

    for (arrname, arr) in arrays:
        #fp.write(%s%s\n" % (pad, arrname))
        for elt in arr:
            exportDefault(arrname, elt, [], [], [], [], pad+'  ', fp)

    writeDir(data, prio+exclude+arrays, pad+"  ", fp)
    fp.write("%send %s\n" % (pad,typ))
    return

###################################################################################    
#
#   Boundary parts
#
###################################################################################    

BodyPartVerts = {
    "Head" : ((4302, 8697), (8208, 8220), (8223, 6827)), 
    "Torso" : ((3464, 10305), (6930, 7245), (14022, 14040)),
    "Arm" : ((14058, 14158), (4550, 4555), (4543, 4544)), 
    "Hand" : ((14058, 15248), (3214, 3264), (4629, 5836)),
    "Leg" : ((3936, 3972), (3840, 3957), (14165, 14175)), 
    "Foot" : ((4909, 4943), (5728, 12226), (4684, 5732)), 
    }

def setBoundaryVerts(scn): 
    (x, y, z) = BodyPartVerts[scn.MCBodyPart]
    setAxisVerts(scn, 'MCX1', 'MCX2', x)
    setAxisVerts(scn, 'MCY1', 'MCY2', y)
    setAxisVerts(scn, 'MCZ1', 'MCZ2', z)
    
def setAxisVerts(scn, prop1, prop2, x):
    (x1, x2) = x
    exec("scn.%s = x1" % prop1)
    exec("scn.%s = x2" % prop2)
    
def selectBoundary(ob, scn):
    verts = ob.data.vertices
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in verts:
        v.select = False
    for xyz in ['X','Y','Z']:
        for n in [1,2]:
            n = eval("scn.MC%s%d" % (xyz, n))
            print(n)
            verts[n].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    return    
    
def setBoundary(context):       
    scn = context.scene
    setBoundaryVerts(scn)
    if scn.MCExamineBoundary:
        ob = getHuman(context)
        selectBoundary(ob, scn)
    return            

###################################################################################    
#
#   Z depth
#
###################################################################################    

#
#   getZDepthItems():
#   setZDepth(scn):    
#

ZDepth = {
    "Body" : 0,
    "Underwear and lingerie" : 20,
    "Socks and stockings" : 30,
    "Shirt and trousers" : 40,
    "Sweater" : 50,
    "Indoor jacket" : 60,
    "Shoes and boots" : 70,
    "Coat" : 80,
    "Backpack" : 100,
    }
    
def setZDepthItems():
    global ZDepthItems
    zlist = sorted(list(ZDepth.items()), key=lambda z: z[1])
    ZDepthItems = []
    for (name, val) in zlist:
        ZDepthItems.append((name,name,name))
    return            

def setZDepth(scn):    
    scn.MCZDepth = ZDepth[scn.MCZDepthName]
    return
    
 
###################################################################################    
#
#   Utilities
#
###################################################################################    
#
#    printVertNums(context):
#
 
def printVertNums(context):
    ob = context.object
    print("Verts in ", ob)
    for v in ob.data.vertices:
        if v.select:
            print(v.index)
    print("End verts")

#
#   deleteHelpers(context):
#

def deleteHelpers(context):
    ob = context.object
    scn = context.scene
    #if not isHuman(ob):
    #    return
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    nmax = LastVertices[scn.MCKeepVertsUntil]
    for v in ob.data.vertices:
        if v.index >= nmax:
            v.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')    
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Vertices deleted")
    return                
            
#
#    removeVertexGroups(context, removeType):
#

def removeVertexGroups(context, removeType):
    ob = context.object
    bpy.ops.object.mode_set(mode='OBJECT')
    if removeType == 'All':
        bpy.ops.object.vertex_group_remove(all=True)
        print("All vertex groups removed")
    else:
        for v in ob.data.vertices:
            if v.select:
                for vgrp in ob.vertex_groups:
                    vgrp.remove([v.index])
        print("Selected verts removed from all vertex groups")
    return

#
#   autoVertexGroups(context):
#

def autoVertexGroups(context):
    ob = context.object
    scn = context.scene
    ishuman = isHuman(ob)
    mid = ob.vertex_groups.new("Mid")
    left = ob.vertex_groups.new("Left")
    right = ob.vertex_groups.new("Right")
    if isSelfClothed(context):
        nOldVerts = LastVertices[scn.MCSelfClothed]
    else:
        nOldVerts = LastVertices[LastClothing]
    if ishuman:
        verts = getHumanVerts(ob.data, scn)
    else:
        verts = ob.data.vertices
    for v in verts.values():
        vn = v.index
        if v.co[0] > 0.01:
            left.add([vn], 1.0, 'REPLACE')
        elif v.co[0] < -0.01:
            right.add([vn], 1.0, 'REPLACE')
        else:
            mid.add([vn], 1.0, 'REPLACE')
            if ishuman and (vn < nOldVerts):
                left.add([vn], 1.0, 'REPLACE')
                right.add([vn], 1.0, 'REPLACE')
    print("Vertex groups auto assigned to %s" % scn.MCAutoGroupType.lower())
    return

def getHumanVerts(me, scn):
    verts = {}
    if scn.MCAutoGroupType == 'Selected':
        for v in me.vertices:
            if v.select:
                verts[v.index] = v
    elif scn.MCAutoGroupType == 'Helpers':
        addHelperVerts(me, verts)
    elif scn.MCAutoGroupType == 'Body':
        addBodyVerts(me, verts)
    elif scn.MCAutoGroupType == 'All':
        addHelperVerts(me, verts)
        addBodyVerts(me, verts)
    return verts        
        
def addHelperVerts(me, verts):
    for v in me.vertices:
        if v.index >= NBodyVerts:
            verts[v.index] = v
    return
    
def addBodyVerts(me, verts):
    meFaces = getFaces(me)
    for f in meFaces:
        if len(f.vertices) < 4:
            continue
        for vn in f.vertices:
            if vn < NBodyVerts:
                verts[vn] = me.vertices[vn]
    return                

#
#   checkAndVertexDiamonds(scn, ob):
#

def checkAndVertexDiamonds(scn, ob):
    print("Unvertex diamonds in %s" % ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    me = ob.data
    nverts = len(me.vertices)
    if scn.MCIsMHMesh and (nverts not in LastVertices.values()):
        raise error.MhcloError(
            "Base object %s has %d vertices. The number of verts in an MH human must be one of %s" % 
            (ob, nverts, LastVertices.values()))
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.vertex_group_remove_from(all=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    return            

#
#   readDefaultSettings(context):
#   saveDefaultSettings(context):
#

def settingsFile(name):
    outdir = os.path.expanduser("~/makehuman/settings/")        
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    return os.path.join(outdir, "make_clothes.%s" % name)
    
def readDefaultSettings(context):
    fname = settingsFile("settings")
    try:
        fp = open(fname, "rU")
    except:
        print("Did not find %s. Using default settings" % fname)
        return
    
    scn = context.scene
    for line in fp:
        words = line.split()
        if len(words) < 3:
            continue
        prop = words[0]
        type = words[1]        
        if type == "int":
            scn[prop] = int(words[2])
        elif type == "float":
            scn[prop] = float(words[2])
        elif type == "str":
            string = words[2]
            for word in words[3:]:
                string += " " + word
            scn[prop] = string
    fp.close()
    return
    
def saveDefaultSettings(context):
    fname = settingsFile("settings")
    fp = open(fname, "w")
    scn = context.scene
    for (prop, value) in scn.items():
        if prop[0:2] == "MC":
            if type(value) == int:
                fp.write("%s int %s\n" % (prop, value))
            elif type(value) == float:
                fp.write("%s float %.4f\n" % (prop, value))
            elif type(value) == str:
                fp.write("%s str %s\n" % (prop, value))
    fp.close()
    return
    
#
#   BMesh
#

    
def getFaces(me):
    global BMeshAware
    try:
        BMeshAware = True
        return me.polygons
    except:
        BMeshAware = False
        return me.faces


class CTextureFace:
    def __init__(self, f, data, n):
        self.uvs = []
        self.data = data
        self.index = n
        
    def set(self, n, uv):
        global BMeshAware
        if BMeshAware:
            self.data[self.index+n].uv = uv
        else:
            if n==0:
                self.data.uv1 = uv
            elif n==1:
                self.data.uv2 = uv
            elif n==2:
                self.data.uv3 = uv
            elif n==3:
                self.data.uv4 = uv
        
    def get(self, n):
        global BMeshAware
        if BMeshAware:
            return self.data[self.index+n].uv
        else:
            if n==0:
                return self.data.uv1
            elif n==1:
                return self.data.uv2
            elif n==2:
                return self.data.uv3
            elif n==3:
                return self.data.uv4
        
        
def getTexFaces(me, ln):
    global BMeshAware
    texFaces = {}
    if BMeshAware:
        uvlayer = me.uv_layers[ln]
        n = 0
        for f in me.polygons:
            tf = CTextureFace(f, uvlayer.data, n)
            for vn in f.vertices:
                tf.uvs.append(uvlayer.data[n].uv)
                n += 1
            texFaces[f.index]= tf
    else:
        uvtex = me.uv_textures[ln]
        for f in me.faces:
            uvface = uvtex.data[f.index]
            tf = CTextureFace(f, uvface, 0)
            tf.uvs = [uvface.uv1, uvface.uv2, uvface.uv3]
            if len(f.vertices) == 4:
                tf.uvs.append(uvface.uv4)
            texFaces[f.index] = tf
    return texFaces            
      
#
#   initInterface():
#

def initInterface():
    for skey in ShapeKeys:
        expr = (
    'bpy.types.Scene.MC%s = BoolProperty(\n' % skey +
    '   name="%s", \n' % skey +
    '   description="Shapekey %s affects clothes",\n' % skey +
    '   default=False)')
        exec(expr)

    bpy.types.Scene.MCDirectory = StringProperty(
        name="Directory", 
        description="Directory", 
        maxlen=1024,
        default="~")
    
    bpy.types.Scene.MCMaterials = BoolProperty(
        name="Materials", 
        description="Use materials",
        default=False)

    bpy.types.Scene.MCUseBump = BoolProperty(
        name="Bump", 
        description="Use bump map",
        default=False)

    bpy.types.Scene.MCUseNormal = BoolProperty(
        name="Normal", 
        description="Use normal map",
        default=False)

    bpy.types.Scene.MCUseDisp = BoolProperty(
        name="Displace", 
        description="Use displacement map",
        default=False)

    bpy.types.Scene.MCUseTrans = BoolProperty(
        name="Transparency", 
        description="Use transparency map",
        default=False)

    bpy.types.Scene.MCUseMask = BoolProperty(
        name="Mask", 
        description="Use mask map",
        default=True)

    bpy.types.Scene.MCUseTexture = BoolProperty(
        name="Texture", 
        description="Use texture",
        default=True)

    bpy.types.Scene.MCMaskLayer = IntProperty(
        name="Mask UV layer", 
        description="UV layer for mask, starting with 0",
        default=0)

    bpy.types.Scene.MCTextureLayer = IntProperty(
        name="Texture UV layer", 
        description="UV layer for textures, starting with 0",
        default=0)

    bpy.types.Scene.MCBumpStrength = FloatProperty(
        name="Bump strength", 
        description="Bump strength",
        default=1.0,
        min=0.0, max=1.0)

    bpy.types.Scene.MCNormalStrength = FloatProperty(
        name="Normal strength", 
        description="Normal strength",
        default=1.0,
        min=0.0, max=1.0)

    bpy.types.Scene.MCDispStrength = FloatProperty(
        name="Disp strength", 
        description="Displacement strength",
        default=0.2,
        min=0.0, max=1.0)

    bpy.types.Scene.MCAllUVLayers = BoolProperty(
        name="All UV layers", 
        description="Include all UV layers in export",
        default=False)

    bpy.types.Scene.MCBlenderMaterials = BoolProperty(
        name="Blender materials", 
        description="Save materials as mhx file",
        default=False)

    bpy.types.Scene.MCHairMaterial = BoolProperty(
        name="Hair material", 
        description="Fill in hair material",
        default=False)

    bpy.types.Scene.MCVertexGroups = BoolProperty(
        name="Save vertex groups", 
        description="Save vertex groups but not texverts",
        default=True)

    """
    bpy.types.Scene.MCThreshold = FloatProperty(
        name="Threshold", 
        description="Minimal allowed value of normal-vector dot product",
        min=-1.0, max=0.0,
        default=theThreshold)

    bpy.types.Scene.MCListLength = IntProperty(
        name="List length", 
        description="Max number of verts considered",
        default=theListLength)

    bpy.types.Scene.MCForbidFailures = BoolProperty(
        name="Forbid failures", 
        description="Raise error if not found optimal triangle")
    scn['MCForbidFailures'] = True
    """
    
    bpy.types.Scene.MCUseInternal = BoolProperty(
        name="Use Internal", 
        description="Access internal settings",
        default=False)

    bpy.types.Scene.MCLogging = BoolProperty(
        name="Log", 
        description="Write a log file for debugging",
        default=False)

    bpy.types.Scene.MCIsMHMesh = BoolProperty(
        name="MakeHuman mesh", 
        description="The human is the MakeHuman base mesh",
        default=True)

    bpy.types.Scene.MCMakeHumanDirectory = StringProperty(
        name="MakeHuman Directory", 
        maxlen=1024,
        default="/home/svn/makehuman")

    bpy.types.Scene.MCSelfClothed = EnumProperty(
        items = ClothingEnums,
        name="Self clothed", 
        description="Clothes included in body mesh",
        default=LastClothing)

    bpy.types.Scene.MCKeepVertsUntil = EnumProperty(
        items = ClothingEnums,
        name="Keep verts untils", 
        description="Last clothing to keep vertices for",
        default=LastClothing)

    bpy.types.Scene.MCX1 = IntProperty(
        name="X1", 
        description="First X vert for clothes rescaling",
        default=4302)

    bpy.types.Scene.MCX2 = IntProperty(
        name="X2", 
        description="Second X vert for clothes rescaling",
        default=8697)

    bpy.types.Scene.MCY1 = IntProperty(
        name="Y1", 
        description="First Y vert for clothes rescaling",
        default=8208)

    bpy.types.Scene.MCY2 = IntProperty(
        name="Y2", 
        description="Second Y vert for clothes rescaling",
        default=8220)

    bpy.types.Scene.MCZ1 = IntProperty(
        name="Z1", 
        description="First Z vert for clothes rescaling",
        default=8289)

    bpy.types.Scene.MCZ2 = IntProperty(
        name="Z2", 
        description="Second Z vert for clothes rescaling",
        default=6827)
    
    bpy.types.Scene.MCExamineBoundary = BoolProperty(
        name="Examine", 
        description="Examine boundary when set",
        default=False)

    bpy.types.Scene.MCBodyPart = EnumProperty(
        items = [('Head', 'Head', 'Head'),
                 ('Torso', 'Torso', 'Torso'),
                 ('Arm', 'Arm', 'Arm'),
                 ('Hand', 'Hand', 'Hand'),
                 ('Leg', 'Leg', 'Leg'),
                 ('Foot', 'Foot', 'Foot')],
        default='Head')                 
    #setBoundaryVerts(scn)

    setZDepthItems()
    bpy.types.Scene.MCZDepthName = EnumProperty(
        items = ZDepthItems,
        default='Sweater')

    bpy.types.Scene.MCZDepth = IntProperty(
        name="Z depth", 
        description="Location in the Z buffer",
        default=ZDepth['Sweater'])
    
    bpy.types.Scene.MCAutoGroupType = EnumProperty(
        items = [('Helpers','Helpers','Helpers'),
                 ('Body','Body','Body'),
                 ('Selected','Selected','Selected'),
                 ('All','All','All')],
    default='Helpers')
                 
    bpy.types.Scene.MCRemoveGroupType = EnumProperty(
        items = [('Selected','Selected','Selected'),
                 ('All','All','All')],
        default='All')
    
    bpy.types.Scene.MCAuthor = StringProperty(
        name="Author", 
        default="Unknown",
        maxlen=32)
    
    bpy.types.Scene.MCLicense = StringProperty(
        name="License", 
        default="GPL3 (see also http://sites.google.com/site/makehumandocs/licensing)",
        maxlen=256)
    
    bpy.types.Scene.MCHomePage = StringProperty(
        name="HomePage", 
        default="http://www.makehuman.org/",
        maxlen=256)

    bpy.types.Scene.MCTag1 = StringProperty(
        name="Tag1", 
        default="",
        maxlen=32)
    
    bpy.types.Scene.MCTag2 = StringProperty(
        name="Tag2", 
        default="",
        maxlen=32)
    
    bpy.types.Scene.MCTag3 = StringProperty(
        name="Tag3", 
        default="",
        maxlen=32)
    
    bpy.types.Scene.MCTag4 = StringProperty(
        name="Tag4", 
        default="",
        maxlen=32)
    
    bpy.types.Scene.MCTag5 = StringProperty(
        name="Tag5", 
        default="",
        maxlen=32)
    

    return
    