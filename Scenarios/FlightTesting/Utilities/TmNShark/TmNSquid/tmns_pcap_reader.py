from typing import BinaryIO

from TmNShark.TmNSquid.tmns_message import TmnsDataMessage
from TmNShark.TmNSquid.tmns_package import TmnsPackage


class TmnsPcapReader:
    def __init__(self, pcap: BinaryIO):
        self.pcap = pcap

    def get_messages(self):
        messages = []
        while True:
            message = self.get_message()
            if message is None:
                print("Message is none now.")
                break
            messages.append(message)
        return messages

    def get_message(self):
        try:
            # find beginning of message
            # make message
            version_and_words = self._read(1)
            ver = int.from_bytes(version_and_words, byteorder='big') >> 4
            adf_words = int.from_bytes(version_and_words, byteorder='big') & 0x0f
            # skipping 4 reserved bits
            # skipping 4 bits of useless message type
            self._read(1)
            flags = int.from_bytes(self._read(2), byteorder='big')
            mdid = int.from_bytes(self._read(4), byteorder='big')
            seqno = int.from_bytes(self._read(4), byteorder='big')
            msglen = int.from_bytes(self._read(4), byteorder='big')  # provides message length in bytes
            secs = int.from_bytes(self._read(4), byteorder='big')
            nanosecs = int.from_bytes(self._read(4), byteorder='big')

            adf_payload = 0
            adf_size = (adf_words * 4)
            if adf_words > 0:
                adf_payload = int.from_bytes(self._read(adf_size), byteorder='big') # convert to bits and then count the words

            packages = []
            position = 24 + adf_payload
            while position < msglen:
                package = self.get_package()

                if package is None:
                    break

                packages.append(package)
                position = position + package.length

            message = TmnsDataMessage(version=ver, adf_words=adf_words,
                                      flags=flags, mdid=mdid,
                                      sequence_number=seqno, length=msglen,
                                      secs=secs, nanosecs=nanosecs,
                                      adf_payload=adf_payload, packages=packages)

            return message

        except EOFError:
            return None
        
    def get_package(self):
        try:
            package_id = int.from_bytes(self._read(4), byteorder='big')
            package_length = int.from_bytes(self._read(2), byteorder='big')
            _ = int.from_bytes(self._read(1), byteorder='big')
            package_status_flags = int.from_bytes(self._read(1), byteorder='big')
            package_time_delta = int.from_bytes(self._read(4), byteorder='big')
            package_payload_len = package_length - 12
            if package_payload_len < 0:
                return None
            package_payload = self._read(package_payload_len)

            package = TmnsPackage(pdid=package_id, length=package_length,
                                  status_flags=package_status_flags,
                                  time_delta=package_time_delta, payload=package_payload)
            return package

        except EOFError:
            return None

    def _read(self, byte_count: int):
        bytes_input = self.pcap.read(byte_count)
        if not bytes_input:
            raise EOFError('Stream is empty.')

        return bytes_input
