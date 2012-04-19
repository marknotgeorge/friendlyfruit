import asyncore

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.bullet import BulletCapsuleShape, BulletCharacterControllerNode, BulletPlaneShape, BulletRigidBodyNode, \
    BulletWorld, ZUp
from panda3d.core import DirectionalLight, Point3, VBase4, Vec3, deg2Rad
from pandac.PandaModules import loadPrcFile

loadPrcFile("client-config.prc")

class FriendlyFruit(ShowBase):
    def __init__(self, player_tag):
        ShowBase.__init__(self)
        self.__player_tag = player_tag
        self.__rotations = {}

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
        asyncore.loop(timeout=0.01, use_poll=True, count=1)

        for node, angular_velocity in self.__rotations.iteritems():
            node.setAngularMovement(angular_velocity)

        dt = self.globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    def server_created_object(self, tag, height, radius):
        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)

        node = BulletCharacterControllerNode(shape, 0.4, tag)
        node_path = self.render.attachNewNode(node)
        self.world.attachCharacter(node_path.node())

        if tag == self.__player_tag:
            self.camera.reparentTo(node_path)
        else:
            humanoid = Actor("player.egg")
            humanoid.setH(180)
            humanoid.reparentTo(node_path)

            point1 = Point3()
            point2 = Point3()
            humanoid.calcTightBounds(point1, point2)
            humanoid.setScale(height / (point2.z - point1.z))

            humanoid.setZ(-height / 2)

    def server_moves_thing(self, tag, loc_x, loc_y, loc_z, speed_x, speed_y, speed_z, angle, angular_velocity):
        node_path = self.render.find("**/" + tag)
        node_path.setPos(loc_x, loc_y, loc_z)
        node_path.node().setLinearMovement(Vec3(speed_x, speed_y, speed_z), True)

        # I don't know why deg2Rad is required in the following line; I suspect it is a Panda bug.
        node_path.setH(deg2Rad(angle))

        if angular_velocity != 0:
            self.__rotations[node_path.node()] = angular_velocity
        elif node_path.node() in self.__rotations:
            del self.__rotations[node_path.node()]
