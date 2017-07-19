from twisted.words.protocols import irc
import logging
from time import time
import wikipedia
import re


m = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]\.[^\s]{2,})"


class TwitchBot(irc.IRCClient, object):

    channel = "#huschee"
    nickname = "8244"
    password = "oauth:2yrcji35prj3toui6wdb94j09o98ys"

    current_time = time()

    def signedOn(self):
        self.factory.wait_time = 1
        logging.warning("Signed on as {}".format(self.nickname))

        # Set IRC caps for Twitch and join channel
        self.sendLine("CAP REQ :twitch.tv/membership")
        self.sendLine("CAP REQ :twitch.tv/commands")
        self.sendLine("CAP REQ :twitch.tv/tags")
        self.join(self.channel)

    def joined(self, channel):
        logging.warning("Joined %s" % channel)

    def privmsg(self, user, channel, msg):
        # Extract twitch name
        name = user.split('!', 1)[0].lower()

        # Log the message
        logging.info("{}: {}".format(name, msg))

        if "!whatis " in msg:
            whatis = msg.split(" ", 1)
            if whatis[1]:
                topic = whatis[1].strip()
                try:
                    result = wikipedia.summary(topic, sentences=1)
                    result = re.sub(m, "<link>", result)
                    self.write("@" + name + ": " + result)
                except wikipedia.exceptions.DisambiguationError as e1:
                    self.write("@" + name + ", what exactly do you mean: '" + "', '".join(e1.options[:4]) + "'")
                except wikipedia.exceptions.PageError as e2:
                    self.write("@" + name + ", sorry I don't know what '" + topic + "' is.")

    def parsemsg(self, s):
        """Breaks raw IRC message into tags, prefix, command, and arguments."""
        tags, prefix, trailing = {}, '', []
        if s[0] == '@':
            tags_str, s = s[1:].split(' ', 1)
            tag_list = tags_str.split(';')
            tags = dict(t.split('=') for t in tag_list)
        if s[0] == ':':
            prefix, s = s[1:].split(' ', 1)
        if s.find(' :') != -1:
            s, trailing = s.split(' :', 1)
            args = s.split()
            args.append(trailing)
        else:
            args = s.split()
        command = args.pop(0).lower()
        return tags, prefix, command, args

    def lineReceived(self, line):
        '''Handle IRC line'''
        # First, we check for any custom twitch commands
        tags, prefix, cmd, args = self.parsemsg(line)
        if cmd == "hosttarget":
            self.hostTarget(*args)
        elif cmd == "clearchat":
            self.clearChat(*args)
        elif cmd == "notice":
            self.notice(tags, args)

        # Remove IRCv3 tag information
        if line[0] == "@":
            line = line.split(' ', 1)[1]

        # Then we let IRCClient handle the rest
        super(TwitchBot, self).lineReceived(line)

    def hostTarget(self, channel, target):
        '''Track Twitch hosting status'''
        target = target.split(' ')[0]
        if target == "-":
            logging.warning("Exited host mode")
        else:
            logging.warning("Now hosting {}".format(target))

    def clearChat(self, channel, target=None):
        '''Track chat clear notices'''
        if target:
            logging.warning("{} was timed out".format(target))
        else:
            logging.warning("chat was cleared")

    def notice(self, tags, args):
        '''Track all other Twitch notices'''
        if "msg-id" not in tags:
            return
        logging.warning(tags['msg-id'])

    def write(self, msg):
        '''Send message to channel and log it'''
        self.msg(self.channel, msg)
        logging.info("{}: {}".format(self.nickname, msg))
