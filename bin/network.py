# -*- coding:utf-8 -*-
# !~/anaconda/bin/python

"""
    The network communication module which contain two sub-modules.
    1. Communication module, deals with data send and receive, the encryption and decryption, the camouflage and so on.
    2. Communication protocol parsing and encapsulation.

    The first sub-module is replaceable. Now we complete as TCP communication protocol, later, we will change to HTTP.
"""

import socketserver
import threading
import struct
import uuid


class Protocol(object):
    """
        The network protocol class.
        This class maintains consistency of parsing and packing method between server and client side,
        The data transfer in network is byte stream, that's why we need packing and parsing
    """

    class ParseError(Exception): pass
    class PackError(Exception):  pass

    @staticmethod
    def packing(m_list):
        try:
            bytes_stream = m_list[0]['o_id'].bytes()
            for mission in m_list:
                param_stream = bytes()
                for key in mission['params']:
                    param_stream += struct.pack('<i', len(key))[0]
                    param_stream += key.encode('ascii')
                    if isinstance(mission['params'][key], int) and mission['params'][key].bit_length() < 32:
                        param_stream += b'I' + struct.pack('<i', mission['params'][key])
                    if isinstance(mission['params'][key], int) and mission['params'][key].bit_length() > 31:
                        param_stream += b'Q' + struct.pack('<q', mission['params'][key])
                    if isinstance(mission['params'][key], float):
                        param_stream += b'D' + struct.pack('<d', mission['params'][key])
                    if isinstance(mission['params'][key], bool):
                        param_stream += b'?' + b'1' if mission['params'][key] else b'0'
                    if isinstance(mission['params'][key], str):
                        param_stream += b'U' + struct.pack('<i', len(mission['params'][key]) * 2) + mission['params'][key].encoding('utf-8')
                    if isinstance(mission['params'][key], bytes):
                        param_stream += b'B' + struct.pack('<i', len(mission['params'][key])) + mission['params'][key]
                bytes_stream += mission['type'] + mission['m_id'].bytes() + struct.pack('<i', len(param_stream)) + param_stream
        except:
            raise Protocol.PackError
        return bytes_stream

    @staticmethod
    def parsing(bytes_stream):
        m_list = []
        try:
            bee_uuid = uuid.UUID(bytes=bytes_stream[0:16])
            position = 16
            while position < len(bytes_stream):
                m_type   = bytes_stream[position]
                m_uuid   = uuid.UUID(bytes=bytes_stream[position+1:position+17])
                m_len    = struct.unpack('<i', bytes_stream[position+17:position+21])[1]
                m_params = {}
                m_pos    = position+21
                while m_pos - position - 21 < m_len:
                    p_name_len = int(bytes_stream[m_pos])
                    p_name = bytes_stream[m_pos+1:m_pos+1+p_name_len].decode('ascii')
                    p_type = bytes_stream[m_pos+1+p_name_len]
                    if p_type == b'I':
                        m_params[p_name] = struct.unpack('<i', bytes_stream[m_pos+2+p_name_len:m_pos+6+p_name_len])[1]
                        m_pos = m_pos + 6 + p_name_len
                    if p_type == b'Q':
                        m_params[p_name] = struct.unpack('<q', bytes_stream[m_pos+2+p_name_len:m_pos+10+p_name_len])[1]
                        m_pos = m_pos + 10 + p_name_len
                    if p_type == b'?':
                        m_params[p_name] = True if bytes_stream[m_pos+2+p_name_len] == b'1' else False
                        m_pos = m_pos + 3 + p_name_len
                    if p_type == b'D':
                        m_params[p_name] = struct.unpack('<d', bytes_stream[m_pos+2+p_name_len:m_pos+10+p_name_len])[1]
                        m_pos = m_pos + 10 + p_name_len
                    if p_type == b'U':
                        length = struct.unpack('<i', bytes_stream[m_pos+2+p_name_len:m_pos+6+p_name_len])[1]
                        m_params[p_name] = bytes_stream[m_pos+6+p_name_len:m_pos+6+p_name_len+length].decode('utf-8')
                        m_pos = m_pos + 6 + p_name_len + length
                    if p_type == b'B':
                        length = struct.unpack('<i', bytes_stream[m_pos + 2 + p_name_len:m_pos + 6 + p_name_len])[1]
                        m_params[p_name] = bytes_stream[m_pos+6+p_name_len:m_pos+6+p_name_len+length]
                        m_pos = m_pos + 6 + p_name_len + length
                position = m_pos
                m_list.append({'type': m_type, 'm_id': m_uuid, 'o_id': bee_uuid, 'params': m_params})
        except:
            raise Protocol.ParseError
        return m_list


class RequestHandler(socketserver.StreamRequestHandler):
    """
        This class is the entry for handling client's request,
        all the actions taken by Queen will perform in this separate thread
    """

    def handle(self):
        # try to completely receive all data
        length = struct.unpack('<I', self.request.recv(4))
        received = self.request.recv(length)

        try:
            # remove the camouflage and decrypt the data
            # this is not implemented in this TCP communication version
            bytes_stream = received

            # parse content
            mission_list = Protocol.parsing(bytes_stream)

        except Protocol.ParseError:
            pass
        except Protocol.PackError:
            pass


class Network(object):
    """ The network class provide interfaces for start or stop network server """

    def __init__(self, bind_address):
        self.server = socketserver.ThreadingTCPServer(bind_address, RequestHandler, True)
        self.thread = None

    def service_start(self):
        if not self.thread:
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

    def service_stop(self):
        if self.thread:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.thread = None


# Test this module
if __name__ == '__main__':
    import socket

    def client(address, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(address)
            sock.sendall(bytes(message, 'ascii'))
            response = str(sock.recv(1024), 'ascii')
            print("Received: {}".format(response))

    network = Network(('0.0.0.0', 12322))
    network.service_start()
    ip, port = network.server.server_address
    client((ip, port), "Hello World 1\n")
    client((ip, port), "Hello World 2\n")
    client((ip, port), "Hello World 3\n")
    network.service_stop()
