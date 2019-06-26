from typing import BinaryIO

from TmNShark.TmNSquid.tmns_message import TmnsDataMessage
from TmNShark.TmNSquid.tmns_package import TmnsPackage


class TmnsPcapReader:
    def __init__(self, pcap: BinaryIO):
        self.pcap = pcap

    def get_messages(self):
        # fill this in if have multiple messages
        pass

    def get_message(self):
        # message = TmnsDataMessage()
        # find beginning of message
        # make message
        version_and_words = self.pcap.read(1)
        ver = int.from_bytes(version_and_words, byteorder='big') >> 4
        adf_words = int.from_bytes(version_and_words, byteorder='big') & 0x0f
        # ver = int.from_bytes(version_and_words, byteorder='big') # TODO only first 4 bits
        # adf_words = int.from_bytes(version_and_words, byteorder='big') # TODO only last 4 bits
        # skipping 4 reserved bits
        # skipping 4 bits of useless message type
        self.pcap.read(1)
        flags = int.from_bytes(self.pcap.read(2), byteorder='big')
        mdid = int.from_bytes(self.pcap.read(4), byteorder='big')
        seqno = int.from_bytes(self.pcap.read(4), byteorder='big')
        msglen = int.from_bytes(self.pcap.read(4), byteorder='big')  # provides message length in bytes
        secs = int.from_bytes(self.pcap.read(4), byteorder='big')
        nanosecs = int.from_bytes(self.pcap.read(4), byteorder='big')

        hdrlen = 3 + (adf_words * 4)
        adf_payload = 0
        adf_size = (adf_words * 4)
        if adf_words > 0:
            adf_payload = int.from_bytes(self.pcap.read(adf_size), byteorder='big') # convert to bits and then count the words

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

    def get_package(self):
        package_id = int.from_bytes(self.pcap.read(4), byteorder='big')
        package_length = int.from_bytes(self.pcap.read(2), byteorder='big')
        _ = int.from_bytes(self.pcap.read(1), byteorder='big')
        package_status_flags = int.from_bytes(self.pcap.read(1), byteorder='big')
        package_time_delta = int.from_bytes(self.pcap.read(4), byteorder='big')

        # package = mdid_dict[mdid](package_bytes)

        # package_payload_len = (package_length * 8) - 96
        # package_payload = self.pcap.read(96:package_payload_len + 96)
        package_payload_len = package_length - 12
        package_payload = self.pcap.read(package_payload_len)
        # bits = self.pcap.read[96 + package_payload_len:]

        package = TmnsPackage(pdid=package_id, length=package_length,
                              status_flags=package_status_flags,
                              time_delta=package_time_delta, payload=package_payload)

        return package
