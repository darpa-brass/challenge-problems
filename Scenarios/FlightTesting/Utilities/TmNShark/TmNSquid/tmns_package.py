class TmnsPackage:
    """Class to contain TmNS Package Structures"""

    def __init__(self, pdid: int = 0, length: int = 0,
                 status_flags: int = 0, time_delta: int = 0,
                 payload: bytes = 0, measurements: [] = None):
        self.pdid = pdid
        self.length = length
        self.status_flags = status_flags
        self.time_delta = time_delta
        self.payload = payload
        self.measurements = measurements

    @staticmethod
    # @profile
    def from_bits(bits):

        # at some point will ahve to look at MDL to check boolean for whether this is standard or not, and then get pckg length

        package_id = int.from_bytes(bits[:32], byteorder='big')
        package_length = int.from_bytes(bits[32:48], byteorder='big')
        _ = int.from_bytes(bits[48:56], byteorder='big')
        package_status_flags = int.from_bytes(bits[56:64], byteorder='big')
        package_time_delta = int.from_bytes(bits[64:96], byteorder='big')

        package_payload_len = (package_length * 8) - 96
        package_payload = bits[96:package_payload_len+96]
        bits = bits[96+package_payload_len:]

        new_package = TmnsPackage(pdid=package_id, length=package_length, status_flags=package_status_flags, time_delta=package_time_delta, payload=package_payload)

        return new_package, bits
