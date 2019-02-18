import yaml
import json
import base64
import collections
import yamlordereddictloader
import binascii
import struct
import sys


keys = "keys.json"
with open(keys, 'r') as f:
    keys = {
        int(k): base64.b64decode(v) for k, v in json.load(f).items()
    }


def load_packet(data):
    if data[-1] == 0x00:
        data = data[:-1]
    print(data.decode('utf-8'))
    return json.loads(data.decode('utf-8'))


def crypto(payload):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import (
        Cipher, algorithms, modes
    )
    from cryptography.hazmat.primitives import padding

    payload_type = payload[4]

    decryptor = Cipher(
        algorithms.AES(keys[payload[4]]),
        modes.ECB(),
        backend=default_backend()
    ).decryptor()

    data = decryptor.update(payload[42:])

    unpadder = padding.PKCS7(128).unpadder()
    unpad = unpadder.update(data)
    unpad += unpadder.finalize()
    payload_data = load_packet(unpad)

    if payload_type == 0x70:
        if 'key' in payload_data:
            keys[0x64] = payload_data['key'].encode('ascii')
    return payload_data


def crc_check(payload):
    crc = binascii.crc32(payload[42:]) & 0xFFFFFFFF
    data_crc = struct.unpack(">I", payload[6:10])[0]
    return (data_crc, crc, data_crc == crc)

with open(sys.argv[1], 'rb') as f:
    packets = yaml.load(f, Loader=yamlordereddictloader.Loader)
    for k, v in packets.items():
        if 'peer0' in k:
            print("Switch sends")
        else:
            print("Server sends")

        print("Magic: {}".format(v[0:2]))
        print("Length: {} ({})".format(struct.unpack(">H", v[2:4])[0], struct.unpack(">H", v[2:4])[0] == len(v)))
        print("Type: {}".format(v[4:6]))
        print("CRC32: {}".format(crc_check(v)))
        print("id: {}".format(v[10:42]))
        print(crypto(v))
        print()
