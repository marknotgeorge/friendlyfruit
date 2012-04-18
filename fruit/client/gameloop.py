import asyncore

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.bullet import BulletCapsuleShape, BulletCharacterControllerNode, BulletPlaneShape, BulletRigidBodyNode, \
    BulletWorld, ZUp
from panda3d.core import BitMask32, DirectionalLight, Point3, VBase4, Vec3
from pandac.PandaModules import loadPrcFile

loadPrcFile("client-config.prc")

class FriendlyFruit(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Panda pollutes the global namespace.  Some of the extra globals can be referred to in nicer ways
        # (for example self.render instead of render).  The globalClock object, though, is only a global!  We
        # create a reference to it here, in a way that won't upset PyFlakes.
        self.globalClock = __builtins__["globalClock"]

        # Turn off the debugging system which allows the camera to be adjusted directly by the mouse.
        self.disableMouse()

        # Set up physics: the ground plane and the capsule which represents the player.
        self.world = BulletWorld()

        # The ground first:
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, 0)
        self.world.attachRigidBody(node)

        # Now the player:

        height = 1.75
        radius = 0.4
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)

        self.playerNode = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.playerNP = self.render.attachNewNode(self.playerNode)
        self.playerNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.playerNP.node())
        self.camera.reparentTo(self.playerNP)

        # The player starts out not turning.
        self.__turn_rate = 0

        # Load the 3dWarehouse model.
        cathedral = self.loader.loadModel("3dWarehouse_Reykjavik_Cathedral.egg")
        cathedral.reparentTo(self.render)
        cathedral.setScale(0.5)

        # Load the Blender model.
        self.humanoid = Actor("player.egg")
        self.humanoid.setScale(0.5)
        self.humanoid.reparentTo(self.render)
        self.humanoid.loop("Walk")

        humanoidPosInterval1 = self.humanoid.posInterval(58, Point3(13, -10, 0), startPos=Point3(13, 10, 0))
        humanoidPosInterval2 = self.humanoid.posInterval(58, Point3(13, 10, 0), startPos=Point3(13, -10, 0))
        humanoidHprInterval1 = self.humanoid.hprInterval(3, Point3(180, 0, 0), startHpr=Point3(0, 0, 0))
        humanoidHprInterval2 = self.humanoid.hprInterval(3, Point3(0, 0, 0), startHpr=Point3(180, 0, 0))

        # Make the Blender model walk up and down.
        self.humanoidPace = Sequence(humanoidPosInterval1, humanoidHprInterval1, humanoidPosInterval2,
                                     humanoidHprInterval2, name="humanoidPace")

        self.humanoidPace.loop()

        # Create a light so we can see the scene.
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(2, 2, 2, 0))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        # Create a task to update the scene regularly.
        self.taskMgr.add(self.update, "UpdateTask")

    # Update the scene by turning the player if necessary, and processing physics.
    def update(self, task):
        asyncore.loop(timeout=0, use_poll=True, count=1)

        if self.__turn_rate != 0:
            if self.__last_turn is None: self.__last_turn = task.time
            self.playerNode.setAngularMovement(self.__turn_rate * (task.time - self.__last_turn))
            self.__last_turn = task.time

        dt = self.globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    def server_moves_player(self, x, y, z):
        self.playerNP.setPos(x, y, z)

    def server_sets_player_speed(self, x, y, z):
        self.playerNode.setLinearMovement(Vec3(x, y, z), True)

    def server_sets_player_rotation(self, rate):
        self.__last_turn = None
        self.__turn_rate = rate
