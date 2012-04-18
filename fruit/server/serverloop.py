import asyncore, re, socket
import pymongo.errors

from . import db
from .gamestate import GameState
from .. import config, messaging
from ..rpc import account_pb2, game_pb2, general_pb2

class FruitRequestHandler(messaging.Rpc):

    """Send and receive RPC messages on behalf of the server."""

    def __init__(self, server, conn, addr):
        messaging.Rpc.__init__(self, server, conn, addr)
        self.__next_event_tag = 0
        self.__events = {}

    @classmethod
    def set_game_state(self, game_state):
        self.game_state = game_state

    def message_received(self, name, msg):
        if name == "account_pb2.NewAccount":
            data = account_pb2.NewAccount()
            data.ParseFromString(msg)
            self.__new_account(data.user_id, data.password)
        elif name == "account_pb2.Login":
            data = account_pb2.Login()
            data.ParseFromString(msg)
            self.__login(data.user_id, data.password)
        elif name == "game_pb2.EventOccurred":
            data = game_pb2.EventOccurred()
            data.ParseFromString(msg)
            self.__events[data.tag](*[self.decode_variant(arg) for arg in data.args])

    def __new_account(self, user_id, password):
        try:
            user = {"user_id": user_id, "password": password}
            db().users.insert(user, safe=True)

            msg = account_pb2.TellUser()
            msg.message = "Your account has been created.  Thank you for registering."
            self.send_rpc(msg)
        except pymongo.errors.DuplicateKeyError:
            msg = account_pb2.Error()
            msg.message = "That user ID is already in use."
            self.send_rpc(msg)

        msg = account_pb2.Kick()
        self.send_rpc(msg)

    def __login(self, user_id, password):
        user = db().users.find_one({"user_id": user_id})
        if user is None or user["password"] != password:
            msg = account_pb2.Error()
            msg.message = "Unknown user ID or incorrect password."
            self.send_rpc(msg)

            msg = account_pb2.Kick()
            self.send_rpc(msg)
        else:
            msg = game_pb2.Start()
            self.send_rpc(msg)
            self.game_state.add_player(self)

            # The player starts out not moving and not turning.
            self.__speed = general_pb2.Vector()
            self.__speed.x = self.__speed.y = self.__speed.z = 0.0
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

    def accept(self, event, handler, preset_args):
        def handle_event(*event_args):
            handler(*(preset_args + list(event_args)))

        preset_args = list(preset_args)

        self.__next_event_tag += 1
        self.__events[self.__next_event_tag] = handle_event

        msg = game_pb2.EventListen()
        msg.event = event
        msg.tag = self.__next_event_tag
        self.send_rpc(msg)

    def move_player(self, location):
        msg = game_pb2.MovePlayer()
        msg.pos.x = location.getX()
        msg.pos.y = location.getY()
        msg.pos.z = location.getZ()
        self.send_rpc(msg)

    def set_player_speed(self):
        msg = game_pb2.PlayerSpeed()
        msg.speed.CopyFrom(self.__speed)
        self.send_rpc(msg)

    def set_player_rotation(self):
        msg = game_pb2.PlayerRotation()
        msg.rotation = self.__turn_rate
        self.send_rpc(msg)

    # Set the player to move forward (W or S keys).
    def __forward(self, speed):
        self.__speed.y = speed
        self.set_player_speed()

    # Set the player to move sideways (A or D keys).
    def __strafe(self, speed):
        self.__speed.x = speed
        self.set_player_speed()

    # Set the player to turn (left and right arrow keys).
    def __turn(self, rate):
        self.__turn_rate = rate
        self.set_player_rotation()

class FruitServer(asyncore.dispatcher):
    def __init__(self, address_family, address):
        asyncore.dispatcher.__init__(self)

        ip, port = re.split(r"\s*,\s*", address, 2)
        port = int(port)

        self.create_socket(address_family, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip, port))
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        FruitRequestHandler(self, conn, addr)

def run():
    listen4_addresses = config.get_all("network", "listen4")
    listen6_addresses = config.get_all("network", "listen6")

    for address in listen4_addresses:
        FruitServer(socket.AF_INET, address)

    for address in listen6_addresses:
        FruitServer(socket.AF_INET6, address)

    game_state = GameState()
    FruitRequestHandler.set_game_state(game_state)
    game_state.run()
