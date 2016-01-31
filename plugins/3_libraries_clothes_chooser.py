"""
B{Project Name:}      MakeHuman

B{Product Home Page:} U{http://www.makehuman.org/}

B{Code Home Page:}    U{http://code.google.com/p/makehuman/}

B{Authors:}           Marc Flerackers

B{Copyright(c):}      MakeHuman Team 2001-2011

B{Licensing:}         GPL3 (see also U{http://sites.google.com/site/makehumandocs/licensing})

B{Coding Standards:}  See U{http://sites.google.com/site/makehumandocs/developers-guide}

Abstract
========

TO DO

"""

import gui3d, mh, os
import download
import files3d
import mh2proxy
import export_config


KnownTags = [
    "shoes",
    "dress",
    "tshirt",
    "stockings",
    "trousers",
    "shirt",
    "underwearbottom",
    "underweartop",
]

class ClothesTaskView(gui3d.TaskView):
    
    def __init__(self, category):
        
        self.systemClothes = os.path.join('data', 'clothes')
        self.userClothes = os.path.join(mh.getPath(''), 'data', 'clothes')

        self.taggedClothes = {}
        self.clothesList = []
        
        gui3d.TaskView.__init__(self, category, 'Clothes')
        if not os.path.exists(self.userClothes):
            os.makedirs(self.userClothes)
        self.filechooser = self.addView(gui3d.FileChooser([self.systemClothes, self.userClothes], 'mhclo', 'png', 'data/clothes/notfound.png'))
        self.update = self.filechooser.sortBox.addView(gui3d.Button('Check for updates'))
        self.mediaSync = None

        @self.filechooser.event
        def onFileSelected(filename):
            
            self.setClothes(gui3d.app.selectedHuman, filename)

            gui3d.app.switchCategory('Modelling')
            
        @self.update.event
        def onClicked(event):
            self.syncMedia()
        
    def setClothes(self, human, mhclo):
    
        if os.path.basename(mhclo) == "clear.mhclo":
            for name,clo in human.clothesObjs.items():
                gui3d.app.removeObject(clo)
                del human.clothesObjs[name]
            self.clothesList = []
            return

        proxy = mh2proxy.readProxyFile(human.meshData, mhclo, False)
        
        if not proxy:
            return

        uuid = proxy.getUuid()
        
        if proxy.clothings:
            folder = os.path.dirname(mhclo)
            for piece in proxy.clothings:
                piecefile = os.path.join(folder, piece, piece+".mhclo")
                self.setClothes(human, piecefile)
            return
            
        #folder = os.path.dirname(mhclo)
        (folder, name) = proxy.obj_file
        obj = os.path.join(folder, name)

        try:
            clo = human.clothesObjs[uuid]
        except:
            clo = None
        if clo:
            gui3d.app.removeObject(clo)
            del human.clothesObjs[uuid]
            self.clothesList.remove(uuid)
            print "Removed clothing 1", proxy.name, uuid
            return

        mesh = files3d.loadMesh(obj)
        if proxy.texture:
            (dir, name) = proxy.texture
            tif = os.path.join(folder, name)
            mesh.setTexture(tif)
        else:
            pass
        
        clo = gui3d.app.addObject(gui3d.Object(human.getPosition(), mesh))
        clo.setRotation(human.getRotation())
        clo.mesh.setCameraProjection(0)
        clo.mesh.setSolid(human.mesh.solid)
        clo.mesh.setTransparentPrimitives(len(clo.mesh.faces))
        clo.mesh.originalClothesVerts = [v.co[:] for v in clo.mesh.verts]
        human.clothesObjs[uuid] = clo        
        human.clothesProxies[uuid] = proxy
        self.clothesList.append(uuid)
        
        for tag in proxy.tags:
            tag = tag.lower()
            if tag in KnownTags:
                try:
                    oldUuids = self.taggedClothes[tag]
                except KeyError:
                    oldUuids = []
                newUuids = []
                for oldUuid in oldUuids:
                    if oldUuid == uuid:
                        pass
                    elif True:
                        try:
                            oldClo = human.clothesObjs[oldUuid]
                        except KeyError:
                            continue
                        print "OVERRIDE: do not remove clothing 2", oldUuid
                        #gui3d.app.removeObject(oldClo)
                        #del human.clothesObjs[oldUuid]
                        #self.clothesList.remove(oldUuid)
                    else:
                        print "Kept clothing", oldUuid
                        newUuids.append(oldUuid)
                newUuids.append(uuid)
                self.taggedClothes[tag] = newUuids

        self.adaptClothesToHuman(human)
        clo.setSubdivided(human.isSubdivided())
        
        #self.clothesButton.setTexture(obj.replace('.obj', '.png'))
    
    def adaptClothesToHuman(self, human):

        for (uuid,clo) in human.clothesObjs.items():            
            if clo:
                mesh = clo.getSeedMesh()
                human.clothesProxies[uuid].update(mesh, human.meshData)
                mesh.update()
                if clo.isSubdivided():
                    clo.getSubdivisionMesh()

    def onShow(self, event):
        # When the task gets shown, set the focus to the file chooser
        gui3d.app.selectedHuman.hide()
        gui3d.TaskView.onShow(self, event)
        self.filechooser.setFocus()
        
        #if not os.path.isdir(self.userClothes) or not len([filename for filename in os.listdir(self.userClothes) if filename.lower().endswith('mhclo')]):    
        #    gui3d.app.prompt('No user clothes found', 'You don\'t seem to have any user clothes, download them from the makehuman media repository?\nNote: this can take some time depending on your connection speed.', 'Yes', 'No', self.syncMedia)

    def onHide(self, event):
        gui3d.app.selectedHuman.show()
        gui3d.TaskView.onHide(self, event)
        
    def onResized(self, event):
        self.filechooser.onResized(event)
        
    def onHumanChanging(self, event):
        
        human = event.human
        if event.change == 'reset':
            print 'deleting clothes'
            for (uuid,clo) in human.clothesObjs.items():
                if clo:
                    gui3d.app.removeObject(clo)
                del human.clothesObjs[uuid]
                del human.clothesProxies[uuid]
            self.clothesList = []
            # self.clothesButton.setTexture('data/clothes/clear.png')

    def onHumanChanged(self, event):
        
        human = event.human
        self.adaptClothesToHuman(human)

    def loadHandler(self, human, values):

        mhclo = export_config.getExistingProxyFile(values, "clothes")
        if not mhclo:
            print values[1], "does not exist. Skipping."
        else:            
            self.setClothes(human, mhclo)
        
    def saveHandler(self, human, file):
        
        for name in self.clothesList:
            clo = human.clothesObjs[name]
            if clo:
                proxy = human.clothesProxies[name]
                file.write('clothes %s %s\n' % (os.path.basename(proxy.file), proxy.getUuid()))
                
    def syncMedia(self):
        
        if self.mediaSync:
            return
        if not os.path.isdir(self.userClothes):
            os.makedirs(self.userClothes)
        self.mediaSync = download.MediaSync(gui3d.app, self.userClothes, 'http://download.tuxfamily.org/makehuman/clothes/', self.syncMediaFinished)
        self.mediaSync.start()
        
    def syncMediaFinished(self):
        
        self.mediaSync = None

# This method is called when the plugin is loaded into makehuman
# The app reference is passed so that a plugin can attach a new category, task, or other GUI elements


def load(app):
    category = app.getCategory('Library')
    taskview = category.addView(ClothesTaskView(category))

    app.addLoadHandler('clothes', taskview.loadHandler)
    app.addSaveHandler(taskview.saveHandler)

# This method is called when the plugin is unloaded from makehuman
# At the moment this is not used, but in the future it will remove the added GUI elements


def unload(app):
    pass

