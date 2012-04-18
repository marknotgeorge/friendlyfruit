import asyncore

from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletCapsuleShape, BulletCharacterControllerNode, BulletPlaneShape, BulletRigidBodyNode, \
    BulletWorld, ZUp
from panda3d.core import BitMask32, Vec3
from pandac.PandaModules import loadPrcFile

class GameState(ShowBase):
    def __init__(self):
        loadPrcFile("server-config.prc")
        ShowBase.__init__(self)

        # Panda pollutes the global namespace.  Some of the extra globals can be referred to in nicer ways
        # (for example self.render instead of render).  The globalClock object, though, is only a global!  We
        # create a reference to it here, in a way that won't upset PyFlakes.
        self.globalClock = __builtins__["globalClock"]

        # Set up physics: the ground plane and the capsule which represents the player.
        self.world = BulletWorld()

        # The ground first:
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode('Ground')
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, 0)
        self.world.attachRigidBody(node)

        # The player starts out not moving and not turning.
        self.__speed = Vec3()
        self.__turn_rate = 0

        # Create a task to update the scene regularly.
        self.taskMgr.add(self.update, "UpdateTask")

    # Update the scene by turning the player if necessary, and processing physics.
    def update(self, task):
        asyncore.loop(timeout=0.1, use_poll=True, count=1)

        dt = self.globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    def add_player(self, player_connection):
        height = 1.75
        radius = 0.4
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)

        self.playerNode = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.playerNP = self.render.attachNewNode(self.playerNode)
        self.playerNP.setPos(0, -20, 3)
        self.playerNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.playerNP.node())

        # The player will fall onto the ground plane when the game starts.  This is a feature, not a bug. :)

        player_connection.move_player(self.playerNP.getPos())
