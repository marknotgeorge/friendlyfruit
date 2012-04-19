import asyncore, re, socket
import pymongo.errors

from . import db
from .gamestate import GameState, Player
from .. import config, messaging
from ..rpc import account_pb2, game_pb2

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
            self.__player = Player(self.game_state, self)
            msg = game_pb2.Start()
            msg.player_tag = self.__player.name
            self.send_rpc(msg)

            # Set up the keyboard controls.
            player_speed = 10
            strafe_speed = player_speed / 2
            turn_speed = 30

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
        """Subscribe to an event on the client.  This allows the
        server to receive keystrokes, mouse clicks, and so on.  A
        unique tag is sent to the client, allowing events of this type
        to be distinguished from other events."""

        def handle_event(*event_args):
            handler(*(preset_args + list(event_args)))

        preset_args = list(preset_args)

        self.__next_event_tag += 1
        self.__events[self.__next_event_tag] = handle_event

        msg = game_pb2.EventListen()
        msg.event = event
        msg.tag = self.__next_event_tag
        self.send_rpc(msg)

    def __forward(self, speed):
        """Set the player to move forward (W or S keys)."""

        velocity = self.__player.get_velocity()
        velocity.y = speed
        self.__player.set_velocity(velocity)

    def __strafe(self, speed):
        """Set the player to move sideways (A or D keys)."""

        velocity = self.__player.get_velocity()
        velocity.x = speed
        self.__player.set_velocity(velocity)

    def __turn(self, rate):
        """Set the player to turn (left and right arrow keys)."""

        self.__player.set_angular_velocity(rate)

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
