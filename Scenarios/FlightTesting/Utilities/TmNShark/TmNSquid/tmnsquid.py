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


from scapy.all import *
from lxml import etree


ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}



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


def make_tdm_packet_list(bfile):
    """ This function reads a binary file (bfile) of TmNS Data Messages, parses the
        TDMs, and adds each TDM to the list of TDMs (tdm_list).
        It returns the TDM list."""

    tdm_list = []

    if os.path.exists(bfile):
        with open(bfile, mode='rb') as f:
            num_bytes = os.path.getsize(bfile)
            while f.tell() < num_bytes:     #iterate though each bite
                ver_adf = f.read(1)
                ver = int.from_bytes(ver_adf, byteorder='big') >> 4
                adf_words = int.from_bytes(ver_adf, byteorder='big') & 0x0f
                f.read(1)  # Read byte.  Field is RESERVED
                flags = int.from_bytes(f.read(2), byteorder='big')
                mdid = int.from_bytes(f.read(4), byteorder='big')
                seqno = int.from_bytes(f.read(4), byteorder='big')
                msglen = int.from_bytes(f.read(4), byteorder='big')
                secs = int.from_bytes(f.read(4), byteorder='big')
                nanosecs = int.from_bytes(f.read(4), byteorder='big')
                hdrlen = 24 + (adf_words * 4)
                adf_payload = ''
                if adf_words > 0:
                    adf_payload = f.read(adf_words * 4)
                payloadlen = msglen - hdrlen
                #payload = f.read(payloadlen)

                # TODO: here need to go through each package - look at tables and go into the payload -> packages -> measurements
                # look up mdid and figure out contents so we know what packages we are looking for from the MDL file
                # get package header (96 bits) - will have to look at package length and see how much more there is to claim
                # every pdid has a fixed size so can get that from the MDL
                # if field reptitions is 0 (not fixed len) then will have to count length - start with pack header - pull off in grps of 16 numbers bc feild 16 bits wide


                #payload is optional, but if present, the TmNSMessagePayload includes one or more packages
                #need to get package header:

                pkg_id = int.from_bytes(f.read(4))
                pkg_pkglen = int.from_bytes(f.read(2))
                pkg_reserved = int.from_bytes(f.read(1))
                pkg_status = int.from_bytes(f.read(1))
                pkg_time = int.from_bytes(f.read(4))
                pkglen_afterheader = payloadlen -


                new_msg = TmnsDataMessage(ver=ver, flags=flags, mdid=mdid, seqno=seqno, msglen=msglen, secs=secs,
                                          nanosecs=nanosecs, adf_payload=adf_payload, payload=payload)
                tdm_list.append(new_msg)
        return tdm_list
    else:
        print("The file '{0}' was not found.".format(bin))
        return tdm_list



# ------------------------------------------------------------------------------


def parse_mdl(mdl=None):
    """ This function parses an MDL file for all MessageDefinition elements within the file.
        For each MessageDefinition found, a new MessageDefinition object is created and added
        to the dictionary of all MDIDs.  Because MDID's are unique, the dictionary is indexed
        by the MDID.  The function has 1 input argument:
        mdl - the name of the MDL file to parse
        After all MDIDs have been parsed in the file and added to the MDID dictionary, the
        dictionary is returned. """

    mdid_dict = {}

    if os.path.exists(mdl) is False:
        print("MDL file not found.  Using defaults for MDID and Multicast Addresses.")
        return mdid_dict

    # Parse MDL file, and create the mapping between MDIDs and their associated Multicast IP Address
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl, mdl_parser)

    messages = root.xpath("//mdl:MessageDefinition", namespaces=ns)
    for message in messages:
        name = message.find("mdl:Name", namespaces=ns).text
        mdid = int(message.find("mdl:MessageDefinitionID", namespaces=ns).text, 16)
        # TODO: dscp = message.find("mdl:DSCPTableEntryRef", namespaces=ns).text
        dst_addr = message.find("mdl:DestinationAddress", namespaces=ns).text
        dst_port = int(message.find("mdl:DestinationPort", namespaces=ns).text)

        #new_mdef = MessageDefinition(name, mdid, 0, dst_addr, dst_port)
        # TODO: do DSCP table lookup. For now, hard-coded to Best Effort

        #mdid_dict[mdid] = new_mdef

    return mdid_dict

