# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---                                TmNShark                                ---
# ---                                                                        ---
# --- Last Updated: May 30, 2019                                             ---
# ------------------------------------------------------------------------------
# ---                                                                        ---
# --- This utility can extract measurements from TmNS messages. Network      ---
# --- Packets can be live data from a network interface or stored offline in ---
# --- a PCAP file.                                                           ---
# ---                                                                        ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import argparse
import csv
from pprint import pprint
import itertools
from collections import namedtuple, defaultdict
import copy

from scapy.all import *
from lxml import etree
from bitarray import bitarray

ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

def show(xml):
    return print(etree.tounicode(xml, pretty_print=True))

class DataField:
    def __init__(self, width, measurement_name=None):
        self.width = width
        self.measurement_name = measurement_name


class TmnsPackage:
    """Class to contain TmNS Package Structures"""

    def __init__(self, pdid=0, length=0, status_flags=0, time_delta=0, payload=None):
        self.pdid = pdid
        self.length = length
        self.status_flags = status_flags
        self.time_delta = time_delta
        self.payload = payload

    @staticmethod
    def from_bits(bits):

        package_id = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]
        package_length = int.from_bytes(bits[:16], byteorder='big')
        bits = bits[16:]
        _ = int.from_bytes(bits[:8], byteorder='big')
        bits = bits[8:]
        package_status_flags = int.from_bytes(bits[:8], byteorder='big')
        bits = bits[8:]
        package_time_delta = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]

        # package = mdid_dict[mdid](package_bytes)

        package_payload_len = (package_length * 8) - 96
        package_payload = bits[:package_payload_len]
        bits = bits[package_payload_len:]

        new_package = TmnsPackage(pdid=package_id, length=package_length, status_flags=package_status_flags, time_delta=package_time_delta, payload=package_payload)

        return new_package, bits

class TmnsDataMessage:
    """Class to contain TmNS Data Message Structures"""

    def __init__(self, ver=1, adf_words=0, flags=0, mdid=0, seqno=0, msglen=24, secs=0, nanosecs=0, adf_payload=None,
                 payload=None):
        self.ver = ver
        self.adf_words = adf_words
        self.flags = flags
        self.mdid = mdid
        self.seqno = seqno
        self.msglen = msglen
        self.time_sec = secs
        self.time_nanosec = nanosecs
        self.adf_payload = adf_payload
        self.payload = payload

    def get_raw(self):
        rsvd = 0
        raw_ver_adf = ((self.ver << 4) | self.adf_words).to_bytes(1, byteorder='big', signed=False)
        raw_rsvd = rsvd.to_bytes(1, byteorder='big', signed=False)
        raw_flags = self.flags.to_bytes(2, byteorder='big', signed=False)
        raw_mdid = self.mdid.to_bytes(4, byteorder='big', signed=False)
        raw_seqno = self.seqno.to_bytes(4, byteorder='big', signed=False)
        raw_msglen = self.msglen.to_bytes(4, byteorder='big', signed=False)
        raw_sec = self.time_sec.to_bytes(4, byteorder='big', signed=False)
        raw_nanosec = self.time_nanosec.to_bytes(4, byteorder='big', signed=False)

        raw = b"".join([raw_ver_adf, raw_rsvd, raw_flags, raw_mdid, raw_seqno,
                        raw_msglen, raw_sec, raw_nanosec, self.payload])
        return raw

    @staticmethod
    def from_bits(bits):
        # make message
        ver = bits[:4]
        bits = bits[4:]
        adf_words = int.from_bytes(bits[:4].tobytes(), byteorder='big')
        bits = bits[4:]
        # skipping 4 reserved bits
        # skipping 4 bits of useless message type
        bits = bits[8:]
        flags = bits[:16]   # int.from_bytes(bits[:16], byteorder='big')
        bits = bits[16:]
        mdid = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]
        seqno = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]
        msglen = int.from_bytes(bits[:32], byteorder='big')  # provides message length in bytes
        bits = bits[32:]
        secs = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]
        nanosecs = int.from_bytes(bits[:32], byteorder='big')
        bits = bits[32:]
        hdrlen = 24 + (adf_words * 4)
        adf_payload = ''
        if adf_words > 0:
            adf_payload = bits[:(adf_words * 8 * 4)] # convert to bits and then count the words
        payloadlen = msglen - hdrlen
        payload = bits[:payloadlen*8]
        bits = bits[payloadlen*8:]

        new_msg = TmnsDataMessage(ver=ver, adf_words=adf_words, flags=flags, mdid=mdid, seqno=seqno, msglen=msglen, secs=secs,
                                  nanosecs=nanosecs, adf_payload=adf_payload, payload=payload)

        return new_msg, bits   # where 5 is the bits left after removing this message


def get_field_info(data_structure, package):
    field_info = []

    for field in data_structure.xpath(".//mdl:DataStructureField", **n):

        field_id = field.get("ID")

        measurement_name = None

        mapped_data_words = package.xpath(".//mdl:DataWordToFieldMap[.//mdl:DataStructureFieldRef[@IDREF = '{}']]".format(field_id), **n)
        for word in mapped_data_words:
            measurement_id = word.xpath("mdl:DataWord/mdl:MeasurementRef/@IDREF", **n)[0]

            try:
                measurement = data_structure.xpath("//mdl:Measurement[@ID = '{}']".format(measurement_id), **n)[0]
            except IndexError:
                print("Your file is bad.")
                os.exit(-1)
            measurement_name = measurement.find("mdl:Name", **n)

        # todo: offset (this is tricky because you have to count from the beginning of the message)
        # also offset increment (we're just going to assume they all touch for now)

        width = int(((field.xpath(".//mdl:FieldLocation/mdl:FieldWidth/mdl:Value", **n))[0]).text)
        repetitions = int((field.xpath(".//mdl:FieldRepetitions", **n)[0]).text)
        # width = int((field.xpath("//mdl:FieldWidth/mdl:Value", **n)[0]))
        # repetitions = int(field.find("//mdl:FieldRepetitions", **n)[0])

        info = DataField(width, measurement_name)

        if repetitions == 0:
            # special case because it's infinite
            field_info = itertools.chain(field_info, itertools.repeat(info))
        else:
            for i in range(repetitions):
                field_info.append(info)

    return field_info


def make_tdm_packet_list(bfile, package_decoders):
    """ This function reads a binary file (bfile) of TmNS Data Messages, parses the
        TDMs, and adds each TDM to the list of TDMs (tdm_list).
        It returns the TDM list."""

    tdm_list = []

    if os.path.exists(bfile):
        with open(bfile, mode='rb') as f:
            bits = bitarray()
            # bits.frombytes(bytes(f.read()))
            bits.fromfile(f)

            while len(bits):
                message, remaining_bits = TmnsDataMessage.from_bits(bits)
                print(hex(message.mdid))
                package, remaining_bits_message = TmnsPackage.from_bits(message.payload)
                print(hex(package.pdid))
                time = message.time_nanosec + package.time_delta + (message.time_sec * 1e9)
                # package1_payload = package.payload

                # write this all out to separate files - each measurement gets its own file - 2 cols: meas timestamp; append to it when see more that meas\
                # open file for appending and if it doesn't exist, open it, if it does, append to end *this should just work if open file in append mode

                # keep iterating through each package
                # while there are any remaining bits, keep pulling (only a pckg for message in this file)
                #print(package_decoders[package.pdid](package.payload, package.time_delta))

                measurements = package_decoders[package.pdid](package.payload, time)
                print(measurements)

                for key, value in measurements.items():
                    with open(r'test_csv_2.csv', 'a') as csvfile:
                        csv_out = csv.writer(csvfile)
                        csv_out.writerow(['value', 'timestamp'])
                        for row in value:
                            csv_out.writerow(row)

                bits = remaining_bits

            # # get array of messages
            # # then get array of packages in each message
            # # call package constructor on each payload -> you'll have package payloads
            # # num_bytes = os.path.getsize(bfile)
            # # while f.tell() < num_bytes:     #iterate though each bite
            #
            # # TODO: here need to go through each package - look at tables and go into the payload -> packages -> measurements
            # # look up mdid and figure out contents so we know what packages we are looking for from the MDL file
            # # get package header (96 bits) - will have to look at package length and see how much more there is to claim
            # # every pdid has a fixed size so can get that from the MDL
            # # if field reptitions is 0 (not fixed len) then will have to count length - start with pack header - pull off in grps of 16 numbers bc feild 16 bits wide
            #
            # # payload is optional, but if present, the TmNSMessagePayload includes one or more packages
            # # need to get package header:
            # #
            #
            # # moving all this so each decoder is defined in the class
            #
            # pprint(new_msg.__dict__)
            # pprint(new_package.__dict__)
            # print("0x{:08X}".format(new_package.pdid))
            # tdm_list.append(new_msg)
        return tdm_list
    else:
        print("The file '{0}' was not found.".format(bin))
        return tdm_list


def preprocess_mdl(mdl=None):
    """Stuff"""

    package_decoders = {}

    if os.path.exists(mdl) is False:
        print("MDL file is missing. Cannot decode.")
        sys.exit(-1)

    # Parse MDL file, and create the mapping between MDIDs and their associated Multicast IP Address
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl, mdl_parser)

    messages = root.xpath("//mdl:MessageDefinition", namespaces=ns)
    for message in messages:
        package_ids = message.xpath(".//mdl:PackageDefinitionRef/@IDREF", **n)
        for package_id in package_ids:
            try:
                package = root.xpath("//mdl:PackageDefinition[@ID = '{}']".format(package_id), **n)[0]
            except IndexError:
                print("Your file is bad.")
                os.exit(-1)

            data_structure_id = package.xpath("mdl:DataStructureRef/@IDREF", **n)[0]
            # data_structure_id = package.find("mdl:DataStructureRef", **n).get(IDREF)
            try:
                data_structure = root.xpath("//mdl:DataStructure[@ID = '{}']".format(data_structure_id), **n)[0]
            except IndexError:
                print("Your file is bad.")
                sys.exit(-1)

            pdid = int(package.find("mdl:PackageDefinitionID", **n).text, base=16)

            def package_decoder(package_bits, start_time, data_structure=data_structure, package=package):
                field_info = get_field_info(data_structure, package)
                measurement_results = defaultdict(list)
                current_time = start_time

                while len(package_bits):  # there's bits left
                    next_field = next(field_info)

                    measurement_bytes = package_bits[:next_field.width]

                    if next_field.measurement_name is not None:
                        measurement_results[next_field.measurement_name.text].append((int.from_bytes(measurement_bytes, byteorder="big"), current_time))
                        # todo: do this the right way by pulling the TimeOffsetIncrement from the DataWordToFieldMap
                        # hardcoded offset value because our file doesn't have it, but we know it experimentally (~8khz)
                        current_time += .000125

                    package_bits = package_bits[next_field.width:]

                return measurement_results

            package_decoders[pdid] = package_decoder

    return package_decoders


def main():
    parser = argparse.ArgumentParser(description="It's a squid.")
    parser.add_argument("mdl", help="Binary file full of TDMs")

    parser.add_argument("--binfile", help="Binary file full of TDMs")

    args = parser.parse_args()

    print(args)

    package_decoders = preprocess_mdl(args.mdl)
    make_tdm_packet_list(args.binfile, package_decoders)


if __name__ == "__main__":
    main()
