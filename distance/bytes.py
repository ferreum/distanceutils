#!/usr/bin/python
# File:        bytes.py
# Description: bytes
# Created:     2017-06-24


class DstBytes(object):

    def __init__(self, source):
        self.source = source

    @property
    def pos(self):
        return self.source.tell()

    @pos.setter
    def pos(self, newpos):
        self.source.seek(newpos)

    def read_n(self, n):
        result = self.source.read(n)
        if len(result) != n:
            raise EOFError
        return result

    def read_byte(self):
        return self.read_n(1)[0]

    def read_number(self):
        n = 0
        bits = 0
        while True:
            b = self.read_byte()
            if b & 0x80:
                n |= (b & 0x7f) << bits
                bits += 7
            else:
                return n | (b << bits)

    def read_fixed_number(self, length):
        data = self.read_n(length)
        n = 0
        for i, b in enumerate(data):
            n |= b << (i * 8)
        return n

    def read_string(self):
        length = self.read_number()
        data = self.read_n(length)
        return data.decode('utf-16', 'surrogateescape')

    def find_long_long(self, number):
        import struct
        data = struct.pack('q', number)
        return self.find_bytes(data)

    def find_bytes(self, data):
        while True:
            pos = 0
            b = self.read_byte()
            while b == data[pos]:
                pos += 1
                if pos >= len(data):
                    self.pos -= len(data)
                    return
                b = self.read_byte()


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
