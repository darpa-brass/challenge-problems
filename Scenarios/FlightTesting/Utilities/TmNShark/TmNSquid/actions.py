import csv

from scapy.all import *
from lxml import etree
from bitarray import bitarray

from TmNShark.TmNSquid.tmns_datafield import TmnsDataField
from TmNShark.TmNSquid.tmns_pcap_reader import TmnsPcapReader


ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}


def show(xml):
    return print(etree.tounicode(xml, pretty_print=True))


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

        info = TmnsDataField(width, measurement_name)

        if repetitions == 0:
            # special case because it's infinite
            field_info = itertools.chain(field_info, itertools.repeat(info))
        else:
            for i in range(repetitions):
                field_info.append(info)

    return field_info

@profile
def make_tdm_packet_list(bfile, package_decoders):
    """ This function reads a binary file (bfile) of TmNS Data Messages, parses the
        TDMs, and adds each TDM to the list of TDMs (tdm_list).
        It returns the TDM list."""

    tdm_list = []

    if os.path.exists(bfile):
        with open(bfile, mode='rb') as f:
            reader = TmnsPcapReader(f)
            messages = reader.get_messages()
            count = 0
            for message in messages:
                count = count + 1
                for package in message.packages:
                    package_time = message.time_nanosec + package.time_delta + (message.time_sec * 1e9)
                    payload = bitarray()
                    payload.frombytes(package.payload)
                    measurements = package_decoders[package.pdid](payload, package_time)
                    cnt_key = 0
                    for _measurement_name, value in measurements.items():
                        with open(r'measurements/' + str(count) + '-' + str(_measurement_name) + "-" + str(message.sequence_number) + r'.csv',
                                  'w') as csvfile:
                            cnt_key = cnt_key + 1
                            csv_out = csv.writer(csvfile)
                            csv_out.writerow(['value', 'timestamp'])
                            for row in value:
                                csv_out.writerow(row)
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

            def package_decoder(package_bits: bitarray, start_time: int, data_structure=data_structure, package=package):
                field_info = get_field_info(data_structure, package)
                measurement_results = defaultdict(list)
                current_time = start_time

                package_bits = memoryview(package_bits)

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