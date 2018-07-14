#!/usr/bin/env python3

from datetime import datetime
import json
import logging
from typing import Optional, Union

from bs4 import BeautifulSoup

from database import DatabaseManager, Message

FNAME = "data/BBB_Guys.html"

logging.basicConfig(format='%(asctime)s %(message)s')


class MessageParser:
    def __init__(self, *, debug: bool = False):
        self.debug = debug
        self.soup = None
        self.msg_list = []
        self._prev_msg = None

        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

    def soupify_html(self, fname: str):
        """Read an HTML file and turns it into a bs4 object."""
        if not fname.endswith('html'):
            raise ValueError(
                "Expected an HTML file, don't give me anything fancy")

        with open(fname, 'rb') as f:
            data = f.read()
            logging.debug("Done with read")
            soup = BeautifulSoup(data, 'lxml')
            logging.debug("Souped up")

        # This is like a 40MB file, so it's nice to clear it out
        del data
        self.soup = soup.body

    def parse_all_messages(self):
        """Parse and add all messages to a list."""
        # For those wanting to follow along their own HTML tree, the tags are:
        # viewport, page, acw, messageGroup
        msg_groups = self.soup.contents[1] \
            .contents[1] \
            .contents[2] \
            .contents[1] \
            .children

        for msg_grp in msg_groups:
            for msg_header in msg_grp.children:
                message = self._parse_message(msg_header)
                if message:
                    self.msg_list.append(message)

    def _parse_message(self, message: BeautifulSoup) -> Optional[Message]:
        """Read and converts HTML data into a Message."""
        try:
            attrs = json.loads(message['data-store'])
        except KeyError:
            return self._parse_admin_message(message)

        if attrs['has_attachment']:
            return self._parse_msg_with_attach(message)
        else:
            name = attrs['name']
            msg = message.find("div", {"data-sigil": "message-text"})
            text = msg.span.text
            attrs = json.loads(msg['data-store'])
            timestamp = self._conv_datetime(attrs['timestamp'])
            new_msg = Message(name, text, timestamp, False)

        self._prev_msg = new_msg
        return new_msg

    def _parse_msg_with_attach(self, message: BeautifulSoup) -> Message:
        """Turn image and link attachment posts to Messages."""
        attrs = json.loads(message['data-store'])
        name = attrs['name']

        img_hdr = message.find_all('img')
        if img_hdr:
            fpath = img_hdr[0]['src']
            msg = message.find("div", {"data-sigil": "message-text"})
            attrs = json.loads(msg['data-store'])
            timestamp = self._conv_datetime(attrs['timestamp'])
            return Message(name, '', timestamp, True, True, fpath)
        else:
            msg = message.find("div", {"data-sigil": "message-text"})
            attrs = json.loads(msg['data-store'])
            timestamp = self._conv_datetime(attrs['timestamp'])
            try:
                link_store = message.find("a", {"data-sigil": "MLinkshim"})
                link = json.loads(link_store['data-store'])['dest_uri']
            except TypeError:
                # These seem to be unique each time?
                # I think they're some kind of FB share thing
                # Most of the time it's a URL to facebook CDN so it's not
                # like there is any useful info here anyways
                link = ''
            return Message(name, '', timestamp, True, False, link)

    def _parse_admin_message(self,
                             message: BeautifulSoup) -> Optional[Message]:
        """Read an 'admin' message and converts to a Message.

        An 'admin' message is one which is sent by Facebook instead of a user.
        A typical example is 'PersonX added PersonY to the chat'
        """
        try:
            data = message.findAll("span", {"class": "fcg"})[0]
        except IndexError:
            # Not sure what these are, but they don't seem important...
            return None

        return Message('Admin', data.text, self._prev_msg.date)

    def anonymize_people(self, fname: str = 'user-mapping.log'):
        """Change all names from 'real names' to 'User N'.

        Args:
            fname: file which stores the public<->anon user mapping
        """
        names = set([msg.person for msg in self.msg_list])
        t0p_s3cr3t_names = ['User %d' % d for d in range(len(names))]

        name_map = dict(zip(names, t0p_s3cr3t_names))

        # Save name map to file
        with open(fname, 'w') as f:
            f.write("Real Name, Fake Name\n")
            for real, fake in name_map.items():
                f.write(real + ', ' + fake + '\n')

        # Update names
        for msg in self.msg_list:
            msg.person = name_map[msg.person]

    @staticmethod
    def _conv_datetime(date: Union[int, float]) -> datetime:
        """Turn ints/floats to datetime objects."""
        date = float(date)
        if date > (1e12 - 1):
            # not sure if msec or sec timestamps?
            date = date / 1e3
        return datetime.fromtimestamp(date)


if __name__ == "__main__":
    mp = MessageParser(debug=True)
    mp.soupify_html(FNAME)
    mp.parse_all_messages()
    mp.anonymize_people()

    dm = DatabaseManager()
    session = dm.open_session()
    session.add_all(mp.msg_list)
    session.commit()
    session.close()
