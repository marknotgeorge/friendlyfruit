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
        self.playerNP.setPos(0, -20, 3)
        self.playerNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.playerNP.node())
        self.camera.reparentTo(self.playerNP)

        # The player will fall onto the ground plane when the game starts.  This is a feature, not a bug. :)

        # The player starts out not moving and not turning.
        self.__speed = Vec3()
        self.__turn_rate = 0

        # Set up the keyboard controls.
        player_speed = 75
        strafe_speed = player_speed / 2
        turn_speed = 50000

        self.accept('w', self.__forward, [player_speed])
        self.accept('w-up', self.__forward, [0])
        self.accept('s', self.__forward, [-player_speed])
        self.accept('s-up', self.__forward, [0])

        self.accept('a', self.__strafe, [-strafe_speed])
        self.accept('a-up', self.__strafe, [0])
        self.accept('d', self.__strafe, [strafe_speed])
        self.accept('d-up', self.__strafe, [0])

        self.accept('arrow_left', self.__turn, [turn_speed])
        self.accept('arrow_left-up', self.__turn, [0])
        self.accept('arrow_right', self.__turn, [-turn_speed])
        self.accept('arrow_right-up', self.__turn, [0])

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
        if self.__turn_rate != 0:
            if self.__last_turn is None: self.__last_turn = task.time
            self.playerNode.setAngularMovement(self.__turn_rate * (task.time - self.__last_turn))
            self.__last_turn = task.time

        dt = self.globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    # Move the player according to the speed set by the keyboard controls.
    def __move_player(self):
        self.playerNode.setLinearMovement(self.__speed, True)

    # Set the player to move forward (W or S keys).
    def __forward(self, speed):
        self.__speed.setY(speed)
        self.__move_player()

    # Set the player to move sideways (A or D keys).
    def __strafe(self, speed):
        self.__speed.setX(speed)
        self.__move_player()

    # Set the player to turn (left and right arrow keys).
    def __turn(self, rate):
        self.__last_turn = None
        self.__turn_rate = rate