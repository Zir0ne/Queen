# -*- coding:utf-8 -*-
# !~/anaconda/bin/python

"""
    The bees's hive, manage all the information of bees.
    When Queen start, the nest should be recovery, so all alive bee's information can be recovery.

    empty_new_bee = {
        'uuid'        : None,
        'session_key' : {'value': None, 'timestamp': None}
        'module_key'  : {'value': None, 'timestamp': None}
        'identity'    : {'mac': None, 'sn': None, 'x64': None}
        'mission_flow': [],
        'checkpoint'  : {},
    }
"""

import os
import pickle
import uuid
import datetime
import threading
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Nest(object):
    """ The new of all bees """

    class ArgumentException(Exception): pass
    class InvalidPassword(Exception): pass
    class BeeNotFound(Exception): pass

    def __init__(self, nest_key):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(nest_key.encode(encoding='utf-8'))
        self.nest = {}
        self.path = os.path.join('..', 'bees')
        self.key  = digest.finalize()
        self.iv   = b'\x99\x88\x77\x66\x55\x44\x33\x22\x11\x00\x99\x88\x77\x66\x55\x44'
        self.namespace = uuid.uuid1()

    def new(self, mac, sn, x64):
        if not (isinstance(mac, str) and isinstance(sn, str) and isinstance(x64, bool)):
            raise self.ArgumentException

        bee_uuid = uuid.uuid3(self.namespace, mac + sn + str(x64))
        self.nest[bee_uuid] = {
            'uuid'        : bee_uuid,
            'session_key' : {'value': os.urandom(32), 'timestamp': datetime.datetime.now()},
            'module_key'  : {'value': os.urandom(32), 'timestamp': datetime.datetime.now()},
            'identity'    : {'mac': mac, 'sn': sn, 'x64': x64},
            'mission_flow': {'lock': threading.Lock(), 'flow': []},
            'checkpoint'  : {},
        }
        return bee_uuid

    def get(self, bee_uuid):
        if not bee_uuid in self.nest:
            raise self.BeeNotFound
        return self.nest[bee_uuid]

    def load(self):
        try:
            for entry in os.scandir(self.path):
                if entry.name.endswith('.bee'):
                    decryptor = Cipher(algorithms.AES(self.key), modes.CFB(self.iv), backend=default_backend()).decryptor()
                    abs_path  = os.path.join(self.path, entry.name)
                    fin = open(abs_path, 'rb')
                    bee = pickle.loads(decryptor.update(fin.read(os.path.getsize(abs_path))) + decryptor.finalize())
                    fin.close()
                    self.nest[bee['uuid']] = bee
        except pickle.UnpicklingError:
            raise self.InvalidPassword

    def save(self, bee_uuid):
        if not bee_uuid in self.nest:
            raise self.BeeNotFound

        digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
        digest.update(bee_uuid.bytes)
        encryptor = Cipher(algorithms.AES(self.key), modes.CFB(self.iv), backend=default_backend()).encryptor()
        fou = open(os.path.join(self.path, digest.finalize().hex() + '.bee'), 'wb')
        fou.write(encryptor.update(pickle.dumps(self.nest[bee_uuid])) + encryptor.finalize())
        fou.close()

    def save_all(self):
        for key in self.nest:
            self.save(key)


if __name__ == '__main__':
    try:
        nest = Nest('wu_yin_wu_she')
        bee_id = nest.new('122222', 'ddd', True)
        nest.save(bee_id)
    except Nest.ArgumentException:
        print('...')
    except Nest.BeeNotFound:
        print('...')

    try:
        new_nest = Nest('wu_yin_wu_she')
        new_nest.load()
        print(new_nest.nest)
    except Nest.InvalidPassword:
        print('Invalid password or invalid bee file')
