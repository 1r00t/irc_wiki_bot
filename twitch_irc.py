from twisted.internet import protocol, reactor
import logging
import time
import bot
import argparse


class BotFactory(protocol.ClientFactory):
    protocol = bot.TwitchBot
    wait_time = 1

    def clientConnectionLost(self, connector, reason):
        # Reconnect when disconnected
        logging.error("Lost connection, reconnecting")
        self.protocol = reload(bot).TwitchBot
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        # Keep retrying when connection fails
        msg = "Could not connect, retrying in {}s"
        logging.warning(msg.format(self.wait_time))
        time.sleep(self.wait_time)
        self.wait_time = min(512, self.wait_time * 2)
        connector.connect()

    def buildProtocol(self, addr):
        p = bot.TwitchBot(args.channel)
        p.factory = self
        return p


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("channel")
    args = parser.parse_args()

    # Make logging format prettier
    logging.basicConfig(format="[%(asctime)s] %(message)s",
                        datefmt="%H:%M:%S",
                        level=logging.INFO)

    # Connect to Twitch IRC server
    reactor.connectTCP('irc.twitch.tv', 6667, BotFactory())
    reactor.run()
