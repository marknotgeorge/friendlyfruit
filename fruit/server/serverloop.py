import asyncore, re, socket
from .. import config, messaging
from ..rpc import account_pb2, game_pb2

class FruitRequestHandler(messaging.Rpc):
    def message_received(self, name, msg):
        if name == "account_pb2.NewAccount":
            data = account_pb2.NewAccount()
            data.ParseFromString(msg)
            self.__new_account(data.user_id, data.password)
        if name == "account_pb2.Login":
            data = account_pb2.Login()
            data.ParseFromString(msg)
            self.__login(data.user_id, data.password)

    def __new_account(self, user_id, password):
        print "new a/c", user_id, password
        msg = account_pb2.TellUser()
        msg.message = "Your account has been created.  Thank you for registering."
        self.send_rpc(msg)
        msg = account_pb2.Kick()
        self.send_rpc(msg)

    def __login(self, user_id, password):
        msg = game_pb2.Start()
        self.send_rpc(msg)

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

    asyncore.loop(use_poll=True)
