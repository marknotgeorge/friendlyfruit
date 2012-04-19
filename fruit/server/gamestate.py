import asyncore, heapq
from time import time

from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletCapsuleShape, BulletCharacterControllerNode, BulletPlaneShape, BulletRigidBodyNode, \
    BulletWorld, ZUp
from panda3d.core import BitMask32, Vec3
from pandac.PandaModules import loadPrcFile

from fruit.rpc import game_pb2, general_pb2

# How often do we update the location of objects which haven't been moved explicitly?
STATIONARY_OBJECT_UPDATE_TIME = 5
MOVING_OBJECT_UPDATE_TIME = 0.5

class Thing(object):
    pending_updates = []

    __next_thing = 0
    __thing_list = {}

    def __init__(self, game_state):
        self.game_state = game_state
        self.update_due_time = 0
        self.schedule_for_update()
        self.__velocity = general_pb2.Vector()
        self.__velocity.x = self.__velocity.y = self.__velocity.z = 0
        self.__angular_velocity = 0

    def get_unique_name(self, name):
        Thing.__next_thing += 1
        self.name = name + str(Thing.__next_thing)
        Thing.__thing_list[self.name] = self
        return self.name

    @classmethod
    def all_things(self):
        return self.__thing_list.values()

    def schedule_for_update(self):
        heapq.heappush(Thing.pending_updates, (self.update_due_time, self))

    def reschedule_update(self):
        update_delay = STATIONARY_OBJECT_UPDATE_TIME if self.__velocity.x == 0 and self.__velocity.y == 0 and \
            self.__velocity.z == 0 and self.__angular_velocity == 0 else MOVING_OBJECT_UPDATE_TIME

        self.update_due_time = time() + update_delay
        self.schedule_for_update()

    def force_update(self):
        self.update_due_time = 0
        self.schedule_for_update()

    def move(self, x, y, z):
        self.node_path.setPos(x, y, z)
        self.force_update()

    def get_velocity(self):
        return self.__velocity

    def set_velocity(self, velocity):
        self.__velocity = velocity
        self.node.setLinearMovement(Vec3(self.__velocity.x, self.__velocity.y, self.__velocity.z), True)
        self.force_update()

    def get_angular_velocity(self):
        return self.__angular_velocity

    def set_angular_velocity(self, angular_velocity):
        self.__angular_velocity = angular_velocity
        self.game_state.set_angular_velocity(self.node, angular_velocity)
        self.force_update()

class LivingThing(Thing):
    def __init__(self, game_state, height, radius, name):
        Thing.__init__(self, game_state)
        self.height = height
        self.radius = radius

        shape = BulletCapsuleShape(radius, height - 2 * radius, ZUp)

        self.node = BulletCharacterControllerNode(shape, 0.4, self.get_unique_name(name))
        self.node_path = self.game_state.render.attachNewNode(self.node)
        self.game_state.world.attachCharacter(self.node_path.node())

class Player(LivingThing):
    __players = set()

    def __init__(self, game_state, player_connection):
        LivingThing.__init__(self, game_state, 1.75, 0.4, "Player")
        self.player_connection = player_connection

        self.__players.add(self)
        self.__known_things = set()

        # The player will fall onto the ground plane when the game starts.  This is a feature, not a bug. :)

        self.move(0, -20, 5)

    def update_known_things(self):
        candidates = set(self.all_things())
        for remove in self.__known_things - candidates:
            data = game_pb2.RemoveObject()
            data.tag = remove.name
            self.player_connection.send_rpc(data)
            self.__known_things.remove(remove)

        to_add = candidates - self.__known_things
        for add in to_add:
            data = game_pb2.AddObject()
            data.tag = add.name
            data.height = self.height
            data.radius = self.radius
            self.player_connection.send_rpc(data)
            self.__known_things.add(add)

        return to_add

    def update_locations(self, to_update):
        for thing in to_update:
            data = game_pb2.ThingState()
            data.tag = thing.name

            location = thing.node_path.getPos()
            data.location.x = location.x
            data.location.y = location.y
            data.location.z = location.z

            data.velocity.CopyFrom(thing.get_velocity())

            data.angle = thing.node_path.getH()
            data.angular_velocity = thing.get_angular_velocity()

            self.player_connection.send_rpc(data)

    @classmethod
    def update_all(self):
        update_time = time()
        to_update = set()
        while Thing.pending_updates and Thing.pending_updates[0][0] < update_time:
            _, thing = heapq.heappop(Thing.pending_updates)
            if thing.update_due_time < update_time:
                to_update.add(thing)
                thing.reschedule_update()

        for player in self.__players:
            additions = player.update_known_things()
            player.update_locations(additions | to_update)

class GameState(ShowBase):
    def __init__(self):
        loadPrcFile("server-config.prc")
        ShowBase.__init__(self)
        self.__rotations = {}

        # Panda pollutes the global namespace.  Some of the extra globals can be referred to in nicer ways
        # (for example self.render instead of render).  The globalClock object, though, is only a global!  We
        # create a reference to it here, in a way that won't upset PyFlakes.
        self.globalClock = __builtins__["globalClock"]

        # Set up physics: the ground plane and the capsule which represents the player.
        self.world = BulletWorld()

        # The ground first:
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        node = BulletRigidBodyNode("Ground")
        node.addShape(shape)
        np = self.render.attachNewNode(node)
        np.setPos(0, 0, 0)
        self.world.attachRigidBody(node)

        # Create a task to update the scene regularly.
        self.taskMgr.add(self.update, "UpdateTask")

    # Update the scene by turning objects if necessary, and processing physics.
    def update(self, task):
        asyncore.loop(timeout=0.1, use_poll=True, count=1)
        Player.update_all()

        for node, angular_velocity in self.__rotations.iteritems():
            node.setAngularMovement(angular_velocity)

        dt = self.globalClock.getDt()
        self.world.doPhysics(dt)
        return task.cont

    def set_angular_velocity(self, node, angular_velocity):
        if angular_velocity != 0:
            self.__rotations[node] = angular_velocity
        elif node in self.__rotations:
            del self.__rotations[node]
