'''
Created on Feb 16, 2016

@author: Wen-Jye
'''
import Leap
import random
import sys
import time
import numpy
import colorsys
from os import listdir
from os.path import isfile, join
from math import *
from random import randint
from direct.showbase.ShowBase import ShowBase
from panda3d.core import PandaSystem
from panda3d.core import CollisionTraverser,CollisionNode, Vec3
from panda3d.core import CollisionHandlerQueue,CollisionRay
from panda3d.core import LRotationf,NodePath, Vec3, Vec4, BitMask32
from panda3d.core import AmbientLight, DirectionalLight, PerspectiveLens
from panda3d.core import PointLight, Spotlight
from panda3d.core import TextNode
from panda3d.core import Material, Texture, CardMaker, TransparencyAttrib, TexGenAttrib, TextureStage
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from Leap import Vector

LOAD_HAND_FROM = "handPart"

ACCEL = 70         # Acceleration in ft/sec/sec
MAX_SPEED = 20    # Max speed in ft/sec
MAX_SPEED_SQ = MAX_SPEED ** 2  # Squared to make it easier to use lengthSquared
                               # Instead of length
UP = Vec3(0,0,1)   # We need this vector a lot, so its better to just have one
                   # instead of creating a new one every time we need it
ZERO = Vec3(0,0,0)
GRAVITY = Vec3(0,-0.3,0)

STAGE_HEIGHT = 12

trigger_pinch = False
trigger_pinch_threshold = False
pinch_cube = -1
pinch_position = ZERO
pointable_position = Vec3(0,0,0)
pointable_finger = None
pinch_finger = [-1,-1]
lastPinchFrame = 0 


timer = 180
gameInter = False
gameSuccess = False
gameStart = False
returnHome = False
tryAgain = False

question_list = []
answer = []
renderedCube = []
cargoList = []
loadedCube = []
score = 0

cubesPosList = [Vec3(-8,STAGE_HEIGHT+4,3), Vec3(-4,STAGE_HEIGHT+4,3), Vec3(0,STAGE_HEIGHT+4,3), Vec3(4,STAGE_HEIGHT+4,3), Vec3(8,STAGE_HEIGHT+4,3), Vec3(-8,STAGE_HEIGHT+4,-1), Vec3(-4,STAGE_HEIGHT+4,-1), Vec3(0,STAGE_HEIGHT+4,-1), Vec3(4,STAGE_HEIGHT+4,-1), Vec3(8,STAGE_HEIGHT+4,-1)]
trainAccel = [10, 5, 4, 2.9, 2.32, 2, 1.7, 1.5, 1.3, 1.2, 1.1]
cubeList = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
fingerTip = ['fing1_R_collider', 'fing2_R_collider', 'fing3_R_collider','fing4_R_collider', 'fing5_R_collider']
finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
picture_names =[]
class Main(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        global picture_names
        picture_names = [f for f in listdir('images') if isfile(join('images', f))]
        
        self.handScale = 1
        self.handV=ZERO
        self.scale = 20 / self.handScale
        self.ex = Vec3(1,0,0)
        self.ez = Vec3(0,0,-1)
        
        self.leap = Leap.Controller()
        self.title = OnscreenText(text="Wen-Jye's Panda3D Leap Motion",
                              style=1, fg=(1,1,0,1),
                              pos=(0.7,-0.95), scale = .07)
        self.score = OnscreenText(text="",
                                     pos = (-1.3, .75), fg=(1,1,0,1),
                                     align = TextNode.ALeft, scale = .1)
        self.timer = OnscreenText(text="",
                                     pos = (-1.3, .85), fg=(1,1,0,1),
                                     align = TextNode.ALeft, scale = .1)
    
        
        self.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerQueue()
        self.handLoader()
        
        self.tracks = self.loader.loadModel("models/tracks")
        self.tracks.setScale(1,1.5,1)
        self.tracks.setPosHpr(-3, STAGE_HEIGHT, 12, 90, 90, 90)
        
        self.train = self.loader.loadModel("models/train")
        self.train.setScale(1,0.5,0.5)
        self.train.setPosHpr(16, STAGE_HEIGHT+0.3, 12, 90, 180, 90)
        
        
        self.stage = self.loader.loadModel("models/stage")
        self.stage.setScale(0.55,0.50,0.25)
        self.stage.setPosHpr(0, STAGE_HEIGHT-0.5, 2, 90, 180, 90)
        self.mesh = self.stage.find("**/mesh_stage")
        self.floor = self.stage.find("**/floor")
        self.floor.node().setIntoCollideMask(BitMask32.bit(0))
        self.wall_B = self.stage.find("**/wall_B")
        self.wall_B.node().setIntoCollideMask(BitMask32.bit(0))
        self.wall_F = self.stage.find("**/wall_F")
        self.wall_F.node().setIntoCollideMask(BitMask32.bit(0))
        self.wall_R = self.stage.find("**/wall_R")
        self.wall_R.node().setIntoCollideMask(BitMask32.bit(0))
        self.wall_L = self.stage.find("**/wall_L")
        self.wall_L.node().setIntoCollideMask(BitMask32.bit(0))
        
        self.cubeRoots = [[render.attachNewNode("cubeRoot_%i"  % (i+1)), Vec3(randint(-3, 3),randint(0, 7),randint(-3, 3))] for i in range(40)] # @UndefinedVariable
        for i in range(len(self.cubeRoots)):
            self.cubeRoots[i][0].detachNode()
            self.cubeCreator(i) 
        
        self.buttonList = [render.attachNewNode("button_%i"  % (i+1)) for i in range(3)] # @UndefinedVariable
        for i in range(len(self.buttonList)):
            self.buttonCreator(i) 
            self.buttonList[i].detachNode()
        self.setLight()        
        self.errorMsg = OnscreenText(text="", pos = (0,0), fg=(1,1,0,1), align = TextNode.ACenter, scale = .1)
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        self.menuBG = self.loadImageAsPlane("tex/startScreen.jpg" )
        self.menuBG.setScale(12.5,9,8.5)
        self.menuBG.reparentTo(self.render)
        self.menuBG.setPosHpr(0,STAGE_HEIGHT+1.5,-2, 0, -105, 0)
        self.menuBG.setTransparency(TransparencyAttrib.MAlpha)
        self.menuBG.setAlphaScale(1)
        self.taskMgr.add(self.deviceChecker, "deviceChecker")
    def spinCameraTask(self, task):
        self.camera.setPos(0,STAGE_HEIGHT+10,30)
        self.camera.setHpr(0,255,0)
        #self.camera.setPos(0,STAGE_HEIGHT,30)
        #self.camera.setHpr(0,270,0)
        self.camLens.setFov(65)
        return Task.cont
    def loadImageAsPlane(self, filepath, yresolution = 600):
        tex = loader.loadTexture(filepath) # @UndefinedVariable
        tex.setBorderColor(Vec4(0,0,0,0))
        tex.setWrapU(Texture.WMBorderColor)
        tex.setWrapV(Texture.WMBorderColor)
        cm = CardMaker(filepath + ' card')
        cm.setFrame(-tex.getOrigFileXSize(), tex.getOrigFileXSize(), -tex.getOrigFileYSize(), tex.getOrigFileYSize())
        card = NodePath(cm.generate())
        card.setTexture(tex)
        card.setScale(card.getScale()/ yresolution)
        card.flattenLight() # apply scale
        return card
    def handLoader(self):
        self.palm_R = self.loader.loadModel("%s/palm_R" % LOAD_HAND_FROM) # @UndefinedVariable
        self.palm_R_collider = self.palm_R.find("**/palm_R_collider")
        self.palm_R_collider.node().setIntoCollideMask(BitMask32.bit(0))
        self.fing_R = [self.loader.loadModel("%s/fing%i_R" % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.midd_R = [self.loader.loadModel("%s/m%i_R"    % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.base_R = [self.loader.loadModel("%s/b%i_R"    % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.fing_R_collider = [self.fing_R[i].find("**/fing%i_R_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        self.midd_R_collider = [self.midd_R[i].find("**/m%i_R_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        self.base_R_collider = [self.base_R[i].find("**/b%i_R_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        self.palm_L = self.loader.loadModel("%s/palm_L" % LOAD_HAND_FROM) # @UndefinedVariable
        self.palm_R_collider = self.palm_L.find("**/palm_L_collider")
        self.palm_R_collider.node().setIntoCollideMask(BitMask32.bit(0))
        self.fing_L = [self.loader.loadModel("%s/fing%i_L" % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.midd_L = [self.loader.loadModel("%s/m%i_L"    % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.base_L = [self.loader.loadModel("%s/b%i_L"    % (LOAD_HAND_FROM, i+1)) for i in range(5)] # @UndefinedVariable
        self.fing_L_collider = [self.fing_L[i].find("**/fing%i_L_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        self.midd_L_collider = [self.midd_L[i].find("**/m%i_L_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        self.base_L_collider = [self.base_L[i].find("**/b%i_L_collider" % (i+1)) for i in range(5)] # @UndefinedVariable
        
        self.palm_R.setScale(self.handScale, self.handScale, self.handScale*1.5)
        self.palm_L.setScale(self.handScale, self.handScale, self.handScale*1.5)
        for f in self.fing_R: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.midd_R: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.base_R: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.fing_L: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.midd_L: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.base_L: f.setScale(self.handScale, self.handScale*1.5, self.handScale*1.5)
        for f in self.fing_R_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
        for f in self.midd_R_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
        for f in self.base_R_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
        for f in self.fing_L_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
        for f in self.midd_L_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
        for f in self.base_L_collider: f.node().setIntoCollideMask(BitMask32.bit(0))
    def deviceChecker(self, task):
        if self.leap.is_connected: 
            if len(self.leap.frame().hands) is 0:
                self.errorMsg.setText("please place the hand above the device to start")
                return Task.cont
            else:
                base.cTrav = self.cTrav # @UndefinedVariable
                self.errorMsg.setText("")
                self.menuBG.detachNode()
                taskMgr.remove("handUpdater")  # @UndefinedVariable
                self.handLoop = taskMgr.add(self.handUpdater, "handUpdater") # @UndefinedVariable
                self.handLoop.last = 0
                self.homeInitial()
                return Task.done
        else: 
            self.errorMsg.setText("please connect device")
            return Task.cont
    def buttonCreator(self, buttonRoot):
        button = loader.loadModel("models/button") # @UndefinedVariable
        button.setScale(0.3,0.4,0.25)
        button.reparentTo(self.buttonList[buttonRoot]) # @UndefinedVariable
        buttonMesh = button.find("**/mesh_button")
        myTexture = self.loader.loadTexture('tex/start_%i.png' %(buttonRoot+1))
        buttonMesh.setTexture(myTexture,1)
        buttonCollider = button.find("**/collider_button")
        buttonCollider.node().setFromCollideMask(BitMask32.bit(0))
        self.cTrav.addCollider(buttonCollider, self.cHandler)
    def cubeCreator(self, cubeRoot):
        cube = loader.loadModel("models/cube") # @UndefinedVariable
        cube.reparentTo(self.cubeRoots[cubeRoot][0]) # @UndefinedVariable
        cubeMesh = cube.find("**/mesh_cube")
        myTexture = self.loader.loadTexture('cubes/tex_%i.jpg' %(cubeRoot))
        cubeMesh.setTexture(myTexture,1)
        cubeSphere = cube.find("**/collider_cube")
        cubeSphere.node().setFromCollideMask(BitMask32.bit(0))
        self.cTrav.addCollider(cubeSphere, self.cHandler)
    def clamp(self, i, mn=0, mx=1):
        return min(max(i, mn), mx)    
    def setLight(self):
        #self.ambientText = self.makeStatusLabel(0)
        self.ambientLight = self.render.attachNewNode(AmbientLight("ambientLight")) 
        # Set the color of the ambient light
        self.ambientLight.node().setColor((1, 1, 1, 1))
        self.render.setLight(self.ambientLight)
        
        self.directionalLight = self.render.attachNewNode(
            DirectionalLight("directionalLight"))
        self.directionalLight.node().setColor((.35, .35, .35, 1))
        # The direction of a directional light is set as a 3D vector
        self.directionalLight.node().setDirection(Vec3(1, 1, -2))
        # These settings are necessary for shadows to work correctly
        self.directionalLight.setY(6)
        dlens = self.directionalLight.node().getLens()
        dlens.setFilmSize(41, 21)
        dlens.setNearFar(50, 75)
        self.render.setLight(self.directionalLight)
        self.color = self.directionalLight.node().getColor()
        h, s, b = colorsys.rgb_to_hsv(self.color[0], self.color[1], self.color[2])
        brightness = self.clamp(b + 0)
        r, g, b = colorsys.hsv_to_rgb(h, s, brightness)
        self.directionalLight.node().setColor((r, g, b, 1))
        
        self.lightSourceSphere = self.loader.loadModel('models/sphere')
        self.lightSourceSphere.setColor((1, 1, 1, 1))
        self.lightSourceSphere.setPos(0,STAGE_HEIGHT+4,3)
        self.lightSourceSphere.setScale(.25)
        self.lightSource = self.lightSourceSphere.attachNewNode(PointLight("lightSource"))
        self.lightSource.node().setAttenuation(Vec3(1, 0.04, 0.1))
        self.lightSource.node().setColor((1, 1, 1, 1))
        self.lightSource.node().setSpecularColor((1, 1, 1, 1))
        self.render.setLight(self.lightSource)
        
    def homeInitial(self):
        global gameStart
        global returnHome
        global tryAgain
        gameStart = False
        tryAgain = False
        returnHome = False
        
        self.menuBG.reparentTo(self.render)
        myTexture = self.loader.loadTexture('tex/home.jpg')
        self.menuBG.setTexture(myTexture,1)
        
        self.buttonList[0].reparentTo(self.render)
        self.buttonList[0].setPosHpr(-6, STAGE_HEIGHT-1, 0, -90, 0, -105)
        
        taskMgr.remove("homeTask")  # @UndefinedVariable
        self.menu = taskMgr.add(self.homeTask, "homeTask") # @UndefinedVariable
        self.menu.last = 0
    def homeTask(self, task):
        global gameStart
        if pointable_finger is None: return Task.cont
        for i in range(len(self.buttonList)):
            buttonPressed = Vec3(1,1,1)
            for f in range(self.cHandler.getNumEntries()):
                entry = self.cHandler.getEntry(f)
                tipName = entry.getIntoNode().getName()
                name = entry.getFromNode().getName()
                if name == "collider_button" and tipName == fingerTip[pointable_finger.type]: 
                    if self.buttonPress(entry, i): buttonPressed= (Vec3(1.1,1.1,1.1))
            self.buttonList[i].setScale(buttonPressed)
        if gameStart: 
            self.stage.reparentTo(self.render)
            self.buttonList[0].detachNode()
            self.menuBG.detachNode()
            self.gameInitial(len(picture_names), True)
            taskMgr.remove("inGameTask") # @UndefinedVariable
            self.inGameTaskLoop = taskMgr.add(self.inGameTask, "inGameTask") # @UndefinedVariable
            self.inGameTaskLoop.last = 0
            gameStart = False        
            return Task.done
        else: return Task.cont
    def scoreInitial(self):
        global gameStart
        global returnHome
        global tryAgain
        global answer
        global renderedCube
        global score
        global question_list
        question_list.clear()
        gameStart = False
        tryAgain = False
        returnHome = False
        scoreCubes = []
        for i in range(len(renderedCube)): 
            if len(answer)>i: self.cargos[i][0].remove_node()
            self.cubeRoots[renderedCube[i]][0].detachNode()
            self.cubeRoots[renderedCube[i]][1] = Vec3(randint(-3, 3),randint(0, 7),randint(-3, 3)) 
        self.image.removeNode()
        self.cargos.clear()
        answer.clear()
        answer.clear()
        self.train.setPosHpr(16, STAGE_HEIGHT+0.3, 12, 90, 180, 90)
        self.train.detachNode()
        self.stage.detachNode()
        self.tracks.detachNode()
        self.timer.setText("")
        self.score.setText("")
        
        self.menuBG.reparentTo(self.render)
        myTexture = self.loader.loadTexture('tex/score.jpg')
        self.menuBG.setTexture(myTexture,1)
        
        for i in range(len(str(score))):        
            temp = cubeList.index(str(score)[i])
            scoreCubes.append(loader.loadModel("models/cube"))# @UndefinedVariable
            scoreCubes[i].reparentTo(self.render) # @UndefinedVariable
            scoreCubes[i].setPos(3.5+(int(i)*2.4),STAGE_HEIGHT+2.5-(i*0.1),-1)
            scoreCubes[i].setHpr(0,-2,-15)
            cubeMesh = scoreCubes[i].find("**/mesh_cube")
            myTexture = self.loader.loadTexture('cubes/tex_%i.jpg' %(temp))
            cubeMesh.setTexture(myTexture,1)
        
        self.buttonList[1].reparentTo(self.render)
        self.buttonList[1].setPosHpr(-7, STAGE_HEIGHT-5, 0, -90, 0, -105)
        
        self.buttonList[2].reparentTo(self.render)
        self.buttonList[2].setPosHpr(8.5, STAGE_HEIGHT-5, 0, -90, 0, -105)
        
        taskMgr.remove("scoreTask")  # @UndefinedVariable
        self.scoreLoop = taskMgr.add(self.scoreTask, "scoreTask", extraArgs = [scoreCubes], appendTask=True) # @UndefinedVariable
        self.scoreLoop.last = 0   
        score = 0     
    def scoreTask(self, scoreCubes, task):
        global tryAgain
        global returnHome
        for i in range(len(self.buttonList)):
            buttonPressed = Vec3(1,1,1)
            for f in range(self.cHandler.getNumEntries()):
                entry = self.cHandler.getEntry(f)
                tipName = entry.getIntoNode().getName()
                name = entry.getFromNode().getName()
                if name == "collider_button" and tipName == fingerTip[pointable_finger.type]: 
                    if self.buttonPress(entry, i): buttonPressed= (Vec3(1.1,1.1,1.1))
            self.buttonList[i].setScale(buttonPressed)
        if tryAgain: 
            self.stage.reparentTo(self.render)
            for f in scoreCubes: f.removeNode()
            scoreCubes.clear()
            self.buttonList[1].detachNode()
            self.buttonList[2].detachNode()
            self.menuBG.detachNode()
            self.gameInitial(len(picture_names),True)
            taskMgr.remove("inGameTask") # @UndefinedVariable
            self.inGameTaskLoop = taskMgr.add(self.inGameTask, "inGameTask") # @UndefinedVariable
            self.inGameTaskLoop.last = 0
            return task.done
        elif returnHome:
            for f in scoreCubes: f.removeNode()
            scoreCubes.clear()
            self.menuBG.detachNode()
            self.buttonList[1].detachNode()
            self.buttonList[2].detachNode()
            self.homeInitial()
            return task.done            
        else: return task.cont
    def gameInitial(self, question, englishGmae):
        global answer
        global gameStart
        global returnHome
        global tryAgain
        global score
        global question_list
        gameStart = False
        tryAgain = False
        returnHome = False
        tempQuestion= ""
        
        self.score.setText("Score: %i" % (score))
        self.ballAccelV = GRAVITY
        self.tracks.reparentTo(self.render)
        self.trainV = Vec3(0,0,0)
        self.train.reparentTo(self.render)
        self.trainV = Vec3(-5,0,0)
        if(englishGmae):
            question = randint(0, question-1)
            while question in question_list: question = randint(0, question-1)
            tempQuestion = picture_names[question][:picture_names[question].index('.')]
            question_list.append(question)
            self.image = self.loadImageAsPlane("images/%s" % (picture_names[question]))
            self.image.reparentTo(self.render)
            self.image.setScale(self.image.getScale()*1.2)
            self.image.setPosHpr(0,STAGE_HEIGHT+3.5,-11, 90, 270, 90)
            self.image.setTransparency(TransparencyAttrib.MAlpha)
            self.image.setAlphaScale(1)
            self.cargos = [[self.loader.loadModel("models/cargo"), -1] for i in range(len(tempQuestion))] # @UndefinedVariable
            for i in range(len(self.cargos)):
                self.cargos[i][0].reparentTo(self.render)
                self.cargos[i][0].setScale(1,0.3,0.3)
                self.cargos[i][0].setScale(1,0.32,0.32)
                if i == 0:self.cargos[i][0].setPosHpr(self.train.getX()+2.5, STAGE_HEIGHT+0.3, 12, 90, 180, 90)
                else: self.cargos[i][0].setPosHpr(self.cargos[i-1][0].getX()+2, STAGE_HEIGHT+0.3, 12, 90, 180, 90)
    
            taskMgr.remove("trainMovingTask") # @UndefinedVariable
            self.trainEnter = taskMgr.add(self.trainMovingTask, "trainMovingTask", extraArgs = [True], appendTask=True ) # @UndefinedVariable
            self.trainEnter.last = 0
            
            usedPos = random.sample(range(0, 10), 10)
            for i in range(10):
                if i<len(tempQuestion):
                    temp = cubeList.index(tempQuestion[i])
                    answer.append(temp)
                    self.assignCube(temp, i, usedPos)
                else: 
                    temp = randint(10,35)
                    while temp in answer: temp = randint(10,35)
                    self.assignCube(temp, i, usedPos)
    def assignCube(self, temp, i, usedPos):
        global renderedCube   
        renderedCube.append(temp) 
        self.cubeRoots[temp][0].reparentTo(self.render)
        self.cubeRoots[temp][0].setPos(cubesPosList[usedPos[i]])
        self.cubeRoots[temp][0].setHpr(0,0,0)
        taskMgr.remove("physicsTask_%i" % (i)) # @UndefinedVariable
        self.physicsTaskLoop = taskMgr.add(self.physicsTask, "physicsTask_%i" % (i),extraArgs = [temp], appendTask=True) # @UndefinedVariable
        self.physicsTaskLoop.last = 0 
    
    def inGameTask(self, task):
        global gameSuccess
        global score
        global gameInter
        global timer
        secs = timer - int(task.time)
        mins = int(secs/60)
        self.timer.setText('{:02d}:{:02d}'.format(mins, secs%60))
            
        if secs == -1:
            #score= score+22
            gameInter= False
            self.errorMsg.setText("")
            taskMgr.remove("trainMovingTask")  # @UndefinedVariable
            self.scoreInitial()
            return Task.done
        if gameInter: return Task.cont
        fail = True
        gameSuccess = True
        for i in range(len(answer)):
            if self.cargos[i][1] == -1: fail = False
            if answer[i] != self.cargos[i][1]:
                gameSuccess = False
        if gameSuccess: 
            self.errorMsg.setText("Success")
            score = score +1
            self.score.setText("Score: %i" % (score))
            gameInter = True
            taskMgr.remove("trainMovingTask") # @UndefinedVariable
            self.trainLeaving = taskMgr.add(self.trainMovingTask, "trainMovingTask", extraArgs = [False], appendTask=True ) # @UndefinedVariable
            self.trainLeaving.last = 0
            
        elif fail: self.errorMsg.setText("FAIL")
        else: self.errorMsg.setText("")
        return Task.cont
    def buttonPress(self, colEntry, button):
        global gameStart
        global returnHome
        global tryAgain
        if colEntry.getFromNodePath().getPos(self.buttonList[button]).length() == 0:
            norm = colEntry.getSurfaceNormal(render) * -1 # The normal of the hand # @UndefinedVariable
            handCurSpeed = self.handV.length()                # The current hand speed
            hitDir = colEntry.getSurfacePoint(render) - self.buttonList[button].getPos() # @UndefinedVariable
            hitDir.normalize()                            
            hitAngle = self.dotProduct(norm, hitDir)
            if hitAngle > 0 and handCurSpeed>100 and self.handV[2]<-1: 
                if button == 0: gameStart = True
                elif button == 1: returnHome = True
                elif button == 2: tryAgain = True
            return True
        else: return False
    def trainMovingTask(self, arriving, task):
        global answer
        global gameInter
        dt = task.time - task.last
        task.last = task.time
        if dt > .1: return Task.cont 
        if arriving:
            if self.train.getX()<0:  self.trainV += Vec3(1,0,0)* dt * trainAccel[len(answer)]
            self.train.setPos(self.train.getPos() + (self.trainV * dt))
            for f in self.cargos: f[0].setPos(f[0].getPos() + (self.trainV * dt))
            if self.trainV[0]>0:
                self.trainV = Vec3(0,0,0)
                return Task.done
        else: 
            self.trainV += Vec3(-1,0,0)* dt * trainAccel[len(answer)]
            self.train.setPos(self.train.getPos() + (self.trainV * dt))
            for i in range(len(answer)): 
                newPos = self.cargos[i][0].getPos() + (self.trainV * dt)
                self.cargos[i][0].setPos(newPos)
                self.cubeRoots[answer[i]][0].setPos(newPos+Vec3(0,1.4,0))
            if self.cargos[len(answer)-1][0].getX()<-16:
                for i in range(len(renderedCube)): 
                    if len(answer)>i: self.cargos[i][0].remove_node()
                    self.cubeRoots[renderedCube[i]][0].detachNode()
                    self.cubeRoots[renderedCube[i]][1] = Vec3(randint(-3, 3),randint(0, 7),randint(-3, 3)) 
                self.image.removeNode()
                self.cargos.clear()
                answer.clear()
                gameInter = False
                self.train.setPosHpr(16, STAGE_HEIGHT+0.3, 12, 90, 180, 90)
                self.gameInitial(len(picture_names),True)
                return task.done
        return Task.cont            
    def physicsTask(self, cube, task):
        global trigger_pinch
        global trigger_pinch_threshold
        global lastPinchFrame
        global pinch_cube
        if gameInter: return task.done
        isLoaded = False
        dt = task.time - task.last
        task.last = task.time
        if dt > .1: return Task.cont 
        df = 0
        if trigger_pinch and cube == pinch_cube: 
            lastPinchFrame = task.time
            trigger_pinch_threshold = True
        else: df = task.time - lastPinchFrame
        
        if cube == pinch_cube:
            if df < 0.1  and trigger_pinch_threshold is True and trigger_pinch is False: 
                cubeP = self.cubeRoots[pinch_cube][0].getPos()
                for f in self.cargos:
                    cargoP = f[0].getPos()
                    if cubeP[0]>cargoP[0]-1 and cubeP[0]<cargoP[0]+1 and cubeP[1] > cargoP[1] and cubeP[1] < cargoP[1]+4 and cubeP[2]>cargoP[2]-3 and cubeP[2]<cargoP[2]+3:
                        self.cubeRoots[pinch_cube][0].setPos(cargoP+Vec3(0,1.4,0))
                        lastPinchFrame = 0
                        trigger_pinch_threshold = False
                        f[1] = pinch_cube
                        pinch_cube = -1
                
                if trigger_pinch_threshold:
                    currentPos = self.thowingTask(False)
                    if currentPos.length() >0:
                        self.cubeRoots[cube][0].setPos(currentPos)
                    else: 
                        lastPinchFrame = 0
                        trigger_pinch_threshold = False
            
            elif df >= 0.1  and trigger_pinch_threshold is True: 
                lastPinchFrame = 0
                trigger_pinch_threshold = False
                pinch_cube = -1
                self.cubeRoots[cube][1] = self.thowingTask(True)
        for f in self.cargos:
            if f[1] == cube: 
                isLoaded=True
                
        if isLoaded : return Task.cont
        elif cube == pinch_cube and trigger_pinch_threshold: return Task.cont
        
        #if trigger_pinch_threshold is False:
        for i in range(self.cHandler.getNumEntries()):
            entry = self.cHandler.getEntry(i)
            name = entry.getIntoNode().getName()
            if name == "palm_L_collider": self.handCollideHandler(entry, cube)
            elif name == "palm_R_collider": self.handCollideHandler(entry, cube)
            elif name == "floor": self.wallCollideHandler(entry, cube)
            elif name == "wall_B": self.wallCollideHandler(entry, cube)
            elif name == "wall_F": self.wallCollideHandler(entry, cube)
            elif name == "wall_R": self.wallCollideHandler(entry, cube)
            elif name == "wall_L": self.wallCollideHandler(entry, cube)
            elif name == "collider_cube": self.cubeCollideHandler(entry, cube)
            elif trigger_pinch_threshold is False: self.handCollideHandler(entry, cube)
        
        self.cubeRoots[cube][1] += self.ballAccelV * dt * ACCEL
        if self.cubeRoots[cube][1].lengthSquared() > MAX_SPEED_SQ:
            self.cubeRoots[cube][1].normalize()
            self.cubeRoots[cube][1] *= MAX_SPEED
        self.cubeRoots[cube][0].setPos(self.cubeRoots[cube][0].getPos() + (self.cubeRoots[cube][1] * dt))
        return Task.cont
    def thowingTask(self, thowing):
        global pinch_position
        global pinch_finger
        self.frame = self.leap.frame()
        temp = self.frame.hands[pinch_finger[0]].palm_velocity
        releaseHandV = Vec3((temp[0], temp[1], temp[2]))/self.scale
        thumb_tip = self.frame.hands[pinch_finger[0]].fingers[0].bone(3).next_joint
        joint_position = self.frame.hands[pinch_finger[0]].fingers[pinch_finger[1]].bone(3).next_joint
        distance = thumb_tip - joint_position
        release_position = joint_position + Vector(distance[0]/2, distance[1]/2, distance[2]/2)
        release_position = Vec3((release_position[0], release_position[1], release_position[2]))/self.scale
        if thowing is True: 
            thowingV = release_position-pinch_position
            pinch_finger = [-1,-1]
            return releaseHandV
        else: 
            return release_position
    def dotProduct(self, pos1, pos2):
        v1 = (round(pos1[0], 8),round(pos1[1], 8),round(pos1[2], 8))
        v2 = (round(pos2[0], 8),round(pos2[1], 8),round(pos2[2], 8))
        v1_u = v1 / numpy.linalg.norm(v1)
        v2_u = v2 / numpy.linalg.norm(v2)
        return numpy.dot(v1_u, v2_u)
    def cubeCollideHandler(self, colEntry, cube):
        if colEntry.getFromNodePath().getPos(self.cubeRoots[cube][0]).length() == 0:
            ballV=Vec3(0,0,0)
            self.cubeRoots[cube][1] = ballV
            disp = (colEntry.getSurfacePoint(render) - colEntry.getInteriorPoint(render)) # @UndefinedVariable
            newPos = self.cubeRoots[cube][0].getPos() + disp
            self.cubeRoots[cube][0].setPos(newPos)        
    def handCollideHandler(self, colEntry, cube):
        if colEntry.getFromNodePath().getPos(self.cubeRoots[cube][0]).length() == 0:
            norm = colEntry.getSurfaceNormal(render) * -1               # The normal of the hand # @UndefinedVariable
            curSpeed = self.cubeRoots[cube][1].length()                 # The current ball speed
            inVec = self.cubeRoots[cube][1] / curSpeed                  # The direction of ball travel
            velAngle = self.dotProduct(norm, inVec)     
            totalV = Vec3(self.cubeRoots[cube][1][0]+self.handV[0],self.cubeRoots[cube][1][1]+self.handV[1],self.cubeRoots[cube][1][2]+self.handV[2])
            ballV=Vec3(totalV[0]/10,totalV[1]/10,totalV[2]/10)
            if velAngle > 0:
                self.cubeRoots[cube][1] = ballV
                disp = (colEntry.getSurfacePoint(render) - colEntry.getInteriorPoint(render)) # @UndefinedVariable
                newPos = self.cubeRoots[cube][0].getPos() + disp
                self.cubeRoots[cube][0].setPos(newPos)        
    def wallCollideHandler(self, colEntry, cube):
        if colEntry.getFromNodePath().getPos(self.cubeRoots[cube][0]).length() == 0:
            ballV=Vec3(-self.cubeRoots[cube][1][0],self.cubeRoots[cube][1][1],self.cubeRoots[cube][1][2])
            if colEntry.getIntoNode().getName() == "wall_F" or colEntry.getIntoNode().getName() == "wall_B":
                ballV=Vec3(self.cubeRoots[cube][1][0],self.cubeRoots[cube][1][1],-self.cubeRoots[cube][1][2])
            elif colEntry.getIntoNode().getName() == "floor": 
                ballV=Vec3(self.cubeRoots[cube][1][0]/2,-self.cubeRoots[cube][1][1]/2,self.cubeRoots[cube][1][2]/2)
                if ballV[2]<0.01: ballV[2] =0
            self.cubeRoots[cube][1] = ballV
            disp = (colEntry.getSurfacePoint(render)- colEntry.getInteriorPoint(render)) # @UndefinedVariable
            newPos = self.cubeRoots[cube][0].getPos() + disp
            self.cubeRoots[cube][0].setPos(newPos)
    def handUpdater(self, task):
        self.frame = self.leap.frame()
        global trigger_pinch
        pointables = self.frame.pointables
        trigger_pinch = False
        rightHand=None
        if len(self.frame.hands)>0:  
            front_pointable = pointables.frontmost
            for hand in self.frame.hands:
                if(hand.is_left and rightHand==None):
                    self.plotHand(self.palm_L, self.fing_L, self.midd_L, self.base_L, self.frame.hands[0], 0, front_pointable)
                    rightHand=False
                elif(hand.is_right and rightHand==None):
                    self.plotHand(self.palm_R, self.fing_R, self.midd_R, self.base_R, self.frame.hands[0], 0, front_pointable)
                    rightHand=True
                if(len(self.frame.hands)>1):
                    if(rightHand):
                        self.plotHand(self.palm_L, self.fing_L, self.midd_L, self.base_L, self.frame.hands[1], 0, front_pointable)
                    else:
                        self.plotHand(self.palm_R, self.fing_R, self.midd_R, self.base_R, self.frame.hands[1], 0, front_pointable)
                else:
                    if(rightHand):
                        self.plotHand(self.palm_L, self.fing_L, self.midd_L, self.base_L, None, None, front_pointable)
                    else:
                        self.plotHand(self.palm_R, self.fing_R, self.midd_R, self.base_R, None, None, front_pointable)
        else:
            self.plotHand(self.palm_L, self.fing_L, self.midd_L, self.base_L, None, None, None)
            self.plotHand(self.palm_R, self.fing_R, self.midd_R, self.base_R, None, None, None)
            rightHand=None
        return Task.cont
    def plotHand(self, palm, fingerTips, fingerMiddles, fingerbases, leapHand, pinchHand, front_pointable):
        global pinch_finger
        global pointable_position
        global pointable_finger
        usedFingers = 0
        palmValid = False
        if(leapHand and leapHand.is_valid):
            palmValid = True
            palm_position, palm_quat = self.calcTrafo(leapHand.palm_position, -leapHand.palm_normal, self.ez, self.scale)
            palm.setPos(palm_position)
            #print(palm_position[2])
            palm.setQuat(palm_quat)
            thumb_tip = leapHand.fingers[0].bone(3).next_joint
            self.handV=Vec3(leapHand.palm_velocity[0], leapHand.palm_velocity[1], leapHand.palm_velocity[2])
            for i in range(len(leapHand.fingers)):
                lf = leapHand.fingers[i]                
                if lf.is_valid:
                    if i>0 and len(answer) >0: self.updatePinch(leapHand, thumb_tip, lf)
                    if trigger_pinch is True: 
                        pinch_finger[0] = pinchHand
                        pinch_finger[1] = i
                    bf = fingerTips[usedFingers]
                    bm = fingerMiddles[usedFingers]
                    bb = fingerbases [usedFingers]
                    usedFingers += 1
                    
                    bf.reparentTo(self.render)
                    tip_position, tip_quat = self.calcTrafo(lf.bone(3).next_joint, -lf.bone(3).direction, self.ex, self.scale)
                    bf.setPos(tip_position)
                    bf.setQuat(tip_quat)
                    
                    if str(front_pointable) == str(lf):
                        pointable_position = tip_position
                        pointable_finger = lf
                    
                    bm.reparentTo(self.render)
                    m1 = lf.bone(3).next_joint+lf.bone(3).direction*30
                    m2 = lf.bone(2).next_joint-m1
                    mid_position, mid_quat = self.calcTrafo(m1, lf.bone(2).direction, self.ex, self.scale)
                    #mid_position, mid_quat = self.calcTrafo(m1, m2, self.ex, self.scale)
                    bm.setPos(mid_position)
                    bm.setQuat(mid_quat)
                    
                    
                    bb.reparentTo(self.render)
                    b1 = lf.bone(2).next_joint+lf.bone(2).direction*30
                    b2 = leapHand.palm_position-b1
                    #base_position, base_quat = self.calcTrafo(b1, lf.bone(1).direction, self.ex, self.scale)
                    base_position, base_quat = self.calcTrafo(b1, b2, self.ex, self.scale)
                    bb.setPos(base_position)
                    bb.setQuat(base_quat)
                    
        if palmValid: palm.reparentTo(self.render)
        else: palm.detachNode()
        for i in range(usedFingers,5):
            fingerTips[i].detachNode()
            fingerMiddles[i].detachNode()
            fingerbases[i].detachNode()            
    def updatePinch(self, hand, tip, finger):
        global trigger_pinch
        global pinch_position
        global pinch_cube
        joint_position = finger.bone(3).next_joint
        distance = tip - joint_position
        if distance.magnitude < 35:
            trigger_pinch = True
            pinch_position = joint_position + Vector(distance[0]/2, distance[1]/2, distance[2]/2)
            pinch_position = Vec3((pinch_position[0], pinch_position[1], pinch_position[2]))/self.scale
            
        if trigger_pinch is True:
            temp = 1.5
            for f in renderedCube:
                distance = pinch_position- self.cubeRoots[f][0].getPos()
                distance = Vector(distance[0], distance[1], distance[2])
                if distance.magnitude<temp: 
                    temp = distance.magnitude
                    self.unLoadedCube(f) 
                    pinch_cube = f
            if temp < 1.5: 
                self.cubeRoots[pinch_cube][0].setPos(pinch_position)
                trigger_pinch = True
            else: trigger_pinch = False
    def unLoadedCube(self, cube):
        for f in self.cargos:
            if f[1] == cube: 
                f[1]=-1
    def calcTrafo(self, leapPosition, leapDirection, e_i, scale):
        position = Vec3((leapPosition[0], leapPosition[1], leapPosition[2]))/scale
        direction = Vec3((leapDirection[0], leapDirection[1], leapDirection[2])).normalized()
        ang  = e_i.angleDeg(direction)
        axis = e_i.cross(direction).normalized()
        return position, LRotationf(axis, ang)
app = Main()
app.run()
