import argparse, asyncore, socket, sys

from . import gameloop
from .. import messaging
from ..rpc import account_pb2, game_pb2

args = None

class ServerConnection(messaging.Rpc):
    """This class connects to the server, and handles messages that
    arrive.  The superclass provides a function to send messages back
    to the server (send_rpc).  These messages are sent asynchronously,
    when asyncore.loop is entered.

    The superclass also catches and displays exceptions.  It then
    invokes uncaught_exception; the client exits when this function is
    called, but the server does nothing because it should attempt to
    carry on running."""

    def __init__(self, sock):
        messaging.Rpc.__init__(self, sock=sock)
        self.app = None

    def uncaught_exception(self, e):
        sys.exit(1)

    def message_received(self, name, msg):
        if name == "account_pb2.Kick":
            sys.exit(0)
        elif name == "account_pb2.TellUser":
            data = account_pb2.TellUser()
            data.ParseFromString(msg)
            print data.message
        elif name == "account_pb2.Error":
            data = account_pb2.Error()
            data.ParseFromString(msg)
            print data.message
        elif name == "game_pb2.Start":
            self.__start_game()
        elif name == "game_pb2.MovePlayer":
            data = game_pb2.MovePlayer()
            data.ParseFromString(msg)
            self.app.server_moves_player(data.pos.x, data.pos.y, data.pos.z)
        elif name == "game_pb2.PlayerSpeed":
            data = game_pb2.PlayerSpeed()
            data.ParseFromString(msg)
            self.app.server_sets_player_speed(data.speed.x, data.speed.y, data.speed.z)
        elif name == "game_pb2.PlayerRotation":
            data = game_pb2.PlayerRotation()
            data.ParseFromString(msg)
            self.app.server_sets_player_rotation(data.rotation)
        elif name == "game_pb2.EventListen":
            data = game_pb2.EventListen()
            data.ParseFromString(msg)
            self.app.accept(data.event, self.__send_event_to_server, [data.tag])

    def __send_event_to_server(self, tag, *args):
        data = game_pb2.EventOccurred()
        data.tag = tag
        data.args.extend([self.encode_variant(arg) for arg in args])
        self.send_rpc(data)

    def __start_game(self):
        self.app = gameloop.FriendlyFruit()
        

def parse_command_line():
    global args

    argparser = argparse.ArgumentParser(description="Client for the FriendlyFruit game network.")

    argparser.add_argument("-u", "--user-id", required=True,
                           help="connect using this account", dest="user_id")

    argparser.add_argument("-p", "--password", required=True,
                           help="your password", dest="password")

    argparser.add_argument("--port", default=41810, type=int,
                           help="connect to the server on this port", dest="port")

    argparser.add_argument("--register", action="store_true",
                           help="register a new account on the server", dest="new_account")

    argparser.add_argument("host", help="connect to this machine")

    args = argparser.parse_args()

def run():
    parse_command_line()

    sock = socket.create_connection((args.host, args.port))
    server_connection = ServerConnection(sock)

    if args.new_account:
        register = account_pb2.NewAccount()
        register.user_id = args.user_id
        register.password = args.password
        server_connection.send_rpc(register)
    else:
        login = account_pb2.Login()
        login.user_id = args.user_id
        login.password = args.password
        server_connection.send_rpc(login)

    while True:
        asyncore.loop(use_poll=True, count=1)
        if server_connection.app is not None:
            server_connection.app.run()
