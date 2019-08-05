class TmnsDataMessage:
    """Class to contain TmNS Data Message Structures"""
    def __init__(self, version: int = 1, adf_words: int = 0,
                 flags: int = 0, mdid: int = 0, sequence_number: int = 0,
                 length: int = 24, secs: int = 0, nanosecs: int = 0,
                 adf_payload: int = 0, packages: [] = None):
        self.version = version
        self.adf_words = adf_words
        self.flags = flags
        self.mdid = mdid
        self.sequence_number = sequence_number
        self.length = length
        self.time_sec = secs
        self.time_nanosec = nanosecs
        self.adf_payload = adf_payload
        self.packages = packages

    def get_raw(self):
        rsvd = 0
        raw_ver_adf = ((self.version << 4) | self.adf_words).to_bytes(1, byteorder='big', signed=False)
        raw_rsvd = rsvd.to_bytes(1, byteorder='big', signed=False)
        raw_flags = self.flags.to_bytes(2, byteorder='big', signed=False)
        raw_mdid = self.mdid.to_bytes(4, byteorder='big', signed=False)
        raw_seqno = self.sequence_number.to_bytes(4, byteorder='big', signed=False)
        raw_msglen = self.length.to_bytes(4, byteorder='big', signed=False)
        raw_sec = self.time_sec.to_bytes(4, byteorder='big', signed=False)
        raw_nanosec = self.time_nanosec.to_bytes(4, byteorder='big', signed=False)

        raw = b"".join([raw_ver_adf, raw_rsvd, raw_flags, raw_mdid, raw_seqno,
                        raw_msglen, raw_sec, raw_nanosec, self.packages])
        return raw

    @staticmethod
    # @profile
    def from_bits(bits: []):
        # make message
        ver = bits[:4]
        adf_words = int.from_bytes(bits[4:8].tobytes(), byteorder='big')
        # skipping 4 reserved bits
        # skipping 4 bits of useless message type
        flags = bits[16:32]   # int.from_bytes(bits[:16], byteorder='big')
        mdid = int.from_bytes(bits[32:64], byteorder='big')
        seqno = int.from_bytes(bits[64:96], byteorder='big')
        msglen = int.from_bytes(bits[96:128], byteorder='big')  # provides message length in bytes
        secs = int.from_bytes(bits[128:160], byteorder='big')
        nanosecs = int.from_bytes(bits[160:192], byteorder='big')
        hdrlen = 24 + (adf_words * 4)
        adf_payload = None
        adf_offset = 192 + (adf_words * 8 * 4)
        if adf_words > 0:
            adf_payload = bits[192:adf_offset] # convert to bits and then count the words
        payloadlen = msglen - hdrlen
        payload_offset = adf_offset+payloadlen*8
        payload = bits[adf_offset:payload_offset]
        del bits[:payload_offset]
        # bits.pop(1:payload_offset)
        # bits = bits[payload_offset:]
        # bits.remove
        # rewrite as stream

        new_msg = TmnsDataMessage(ver=ver, adf_words=adf_words, flags=flags, mdid=mdid, seqno=seqno, length=msglen, secs=secs,
                                  nanosecs=nanosecs, adf_payload=adf_payload, packages=payload)

        return new_msg, bits   # where 5 is the bits left after removing this message
