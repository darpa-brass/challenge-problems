# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---                                TmNShark                                ---
# ---                                                                        ---
# --- Last Updated: May 20, 2019                                             ---
# ------------------------------------------------------------------------------
# ---                                                                        ---
# --- This utility can convert network packets into a binary stream of TmNS  ---
# --- Data Messages (TDMs) or TDMs into network packets.  Network packets    ---
# --- can be live data from a network interface or stored offline in a PCAP  ---
# --- file.  The binary streams of TDMs can be written to/read from regular  ---
# --- files or named pipes.                                                  ---
# ---                                                                        ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import os
import argparse
import time
import socket
import errno
import signal
from time import sleep
from scapy.all import *
from lxml import etree

ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

DEFAULT_TDM_PORT = 50003
DEFAULT_BINARY_TDM_FILE = "tmns.bin"


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


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class MessageDefinition:
    """Class to contain Message Definitions"""

    def __init__(self, name='', mdid=0xffffffff, dscp=0, dst_addr='239.255.255.254', dst_port=50003):
        self.name = name
        self.mdid = mdid
        self.dscp = dscp
        self.dst_addr = dst_addr
        self.dst_port = dst_port


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def write_tdm_to_pipe(pkt):
    """ This function takes in an IP packet and searches it to see if it contains a
        TmNS Data Message.  If it does, then it extracts it from teh UDP payload and
        writes it into the pipe identified by the global g_pipein.  It utilizes two
        global variables:
        g_tdm_cnt - a global counter of the number of TDMs written to the pipe
        g_pipein - the name of the pipe to write the TDMs to."""

    global g_tdm_cnt
    global g_pipein

    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            g_pipein.write(bytes(pkt[UDP].payload))
            g_tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(g_tdm_cnt), end=" ")


# ------------------------------------------------------------------------------


def write_tdm_to_file(pkt):
    """ This function takes in an IP packet and searches it to see if it contains a
        TmNS Data Message.  If it does, then it extracts it from the UDP payload and
        appends it to the binary file of TDMs.  It utilizes two global variables:
        g_tdm_cnt - a global counter of the number of TDMs written to the file
        g_binfile = the binary file to write the TDMs to."""

    global g_tdm_cnt
    global g_binfile

    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            f = open(g_binfile, 'a+b')
            f.write(bytes(pkt[UDP].payload))
            f.close()
            g_tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(g_tdm_cnt), end=" ")


# ------------------------------------------------------------------------------


def make_tdm_packet_list(bfile):
    """ This function reads a binary file (bfile) of TmNS Data Messages, parses the
        TDMs, and adds each TDM to the list of TDMs (tdm_list).
        It returns the TDM list."""

    tdm_list = []

    if os.path.exists(bfile):
        with open(bfile, mode='rb') as f:
            num_bytes = os.path.getsize(bfile)
            while f.tell() < num_bytes:
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
                payload = f.read(payloadlen)

                new_msg = TmnsDataMessage(ver=ver, flags=flags, mdid=mdid, seqno=seqno, msglen=msglen, secs=secs,
                                          nanosecs=nanosecs, adf_payload=adf_payload, payload=payload)
                tdm_list.append(new_msg)
        return tdm_list
    else:
        print("The file '{0}' was not found.".format(bin))
        return tdm_list


# ------------------------------------------------------------------------------


def live_network_input_to_pipe(iface=None, p=None):
    """ This function opens a pipe for writing in binary mode, and then it calls
        scapy's 'sniff' function with a callback to write_tdm_to_pipe function.  If
        no interface is specified, packet sniffing is done on the default interface.
        The function requires 2 arguments:
        iface - The interface to sniff on
        p = the name of the Pipe to open
        It utilizes one global variable:
        g_pipein - a variable that stores the named pipe file descriptor.  The pipe
        is opened in this function and is written in the referenced callback function."""

    global g_pipein

    print("Named Pipe '{0}' has been opened for writing.  Waiting for Pipe Reader to connect.".format(p))
    g_pipein = open(p, 'wb')
    print("Connected to Named Pipe '{0}'.  Writing binary TDMs into pipe.".format(p))

    if iface is None:
        print("Listening on default interface.")
        try:
            sniff(prn=write_tdm_to_pipe)
        except IOError as e:
            if e.errno == errno.EPIPE:
                print("Broken Pipe: EPIPE")
    else:
        print("Listening on interface: {0}".format(iface))
        try:
            sniff(iface=iface, prn=write_tdm_to_pipe)
        except IOError as e:
            if e.errno == errno.EPIPE:
                print("Broken Pipe: EPIPE")


# ------------------------------------------------------------------------------


def live_network_input_to_file(iface=None):
    """ This function calls scapy's 'sniff' function with a callback to write_tdm_to_file
        function.  If no interface is specified, packet sniffing is done on the default
        interface.  The function requires 1 argument:
        iface = the interface to sniff on"""

    if iface is None:
        print("Listening on default interface.")
        sniff(prn=write_tdm_to_file)
    else:
        print("Listening on interface: {0}".format(iface))
        sniff(iface=iface, prn=write_tdm_to_file)


# ------------------------------------------------------------------------------


def offline_pcap_input_to_pipe(pcap=None, p=None, quick=False):
    """ This function reads a PCAP/PCAPNG file to create a list of packets.  The list
        is iterated through to filter for packets carrying TmNS Data Messages.  For each
        TDM found, the TDM is written to a pipe as a stream of binary data.  The function
        has 3 input arguments:
        pcap - the PCAP/PCAPNG file to read
        p - the name of the pipe to open and write to
        quick - true/false flag as to whether data should be written as fast as possible
        to the pipe (true) or if it should be delayed relative to the timestamp of the
        captured packet (false)."""

    tdm_cnt = 0

    print("Offline mode: Reading TDMs from PCAP/PCAPNG file and writing to pipe.")
    pkt_list = rdpcap(pcap)  # read the PCAP/PCAPNG file and return a list of packets

    # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
    print("Named Pipe '{0}' has been opened for writing.  Waiting for Pipe Reader to connect.".format(p))
    pipeout = open(p, 'wb')
    print("Connected to Named Pipe '{0}'.  Writing binary TDMs into pipe.".format(p))

    delta_from_current_time = time.time() - pkt_list[0].time

    try:
        for pkt in pkt_list:
            if pkt[UDP].dport == TDM_PORT:
                if quick is False:
                    while (pkt.time + delta_from_current_time) > time.time():
                        sleep(0.0001)
                pipeout.write(bytes(pkt[UDP].payload))
                tdm_cnt += 1
                print("\rTDM Count: {0}".format(tdm_cnt), end=" ")
        pipeout.close()
    except IOError as e:
        if e.errno == errno.EPIPE:
            print("\nBroken Pipe: EPIPE")
            print("")

    if tdm_cnt == 0:
        print("ZERO TmNS Data Messages found in {0}.  No data written to {1}.".format(pcap, p))
    else:
        print("\nThere were {0} TmNS Data Messages written to {1}.".format(tdm_cnt, p))


# ------------------------------------------------------------------------------


def offline_pcap_input_to_file(pcap=None, bfile=None, quick=False):
    """ This function reads a PCAP/PCAPNG file to create a list of packets.  The list
        is iterated through to filter for packets carrying TmNS Data Messages.  For each
        TDM found, the TDM is written to a binary file.  The function has 3 input arguments:
        pcap - the PCAP/PCAPNG file to read
        bfile - the name of the file to open and write to
        quick - true/false flag as to whether data should be written as fast as possible
        to the file (true) or if it should be delayed relative to the timestamp of the
        captured packet (false)."""

    tdm_cnt = 0

    print("Offline mode: Reading TDMs from PCAP/PCAPNG file and writing to file.")
    pkt_list = rdpcap(pcap)  # read the PCAP/PCAPNG file and return a list of packets

    # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
    f = open(bfile, 'w+b')

    delta_from_current_time = time.time() - pkt_list[0].time

    for pkt in pkt_list:
        if pkt[UDP].dport == TDM_PORT:
            if quick is False:
                while (pkt.time + delta_from_current_time) > time.time():
                    sleep(0.0001)
            f.write(bytes(pkt[UDP].payload))
            tdm_cnt += 1
            print("\rTDM Count: {0}".format(tdm_cnt), end=" ")
    f.close()

    if tdm_cnt == 0:
        print("ZERO TmNS Data Messages found in {0}.  {1} is empty.".format(pcap, bfile))
    else:
        print("\nComplete.  Binary file of {0} TmNS Data Messages is stored at {1}.".format(tdm_cnt, bfile))


# ------------------------------------------------------------------------------


def realtime_tdm_stream_to_network_output(p=None, mdid_list=None):
    """ This function reads a binary stream of TmNS Data Messages from a pipe, builds an
        IP packet for the TDM, and then sends the packet out of a network interface.  The
        destination IP address and the destination UDP port are set according to the TDM's
        MDID and the associated MDID within the mdid_list.  The function has 2 input arguments:
        p = the name of the pipe to open and read from
        mdid_list - a list of MessageDefinition objects """

    if os.path.exists(p) is False:
        os.mkfifo(p)  # Create Named Pipe if it doesn't exist

    # Loop over reading the pipe, parsing out the TDMs and sending over the network when a TDM is completely read
    tdm_cnt = 0
    print("Named Pipe '{0}' has been opened for reading.  Waiting for Pipe Writer to connect.".format(p))
    pipeout = open(p, 'rb')
    print("Connected to Named Pipe '{0}'.  Reading binary TDMs from pipe.".format(p))

    try:
        while True:
            raw_ver_adf_flags = pipeout.read(4)
            raw_mdid = pipeout.read(4)
            mdid = int.from_bytes(raw_mdid, byteorder='big')
            raw_seqno = pipeout.read(4)
            raw_msglen = pipeout.read(4)
            msglen = int.from_bytes(raw_msglen, byteorder='big')
            len_remaining = msglen - 16
            raw_rest_of_tdm = pipeout.read(len_remaining)

            raw = b"".join([raw_ver_adf_flags, raw_mdid, raw_seqno, raw_msglen, raw_rest_of_tdm])

            if mdid in mdid_list:
                ip_addr = mdid_list[mdid].dst_addr
                dport = mdid_list[mdid].dst_port
            else:
                ip_addr = '239.88.88.88'  # Default IP address to use IF MDID is not found in the MDL file
                dport = 50003  # Default UDP destination port to use IF MDID is not found in the MDL file

            msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
            msg = msg_ip_hdr / UDP(sport=55501, dport=dport) / Raw(raw)

            send(msg, verbose=0)

            tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end=" ")

    except IOError as e:
        if e.errno == errno.EPIPE:
            print("Looks like the pipe closed.  Closing the pipe and will reopen it for listening.")
            pipeout.close()
        else:
            print("some other IOError other than EPIPE. quitting")
            exit(-1)
    except ValueError:
        print("\nPipe Writer has closed.  Closing our Pipe Reader.")
        pipeout.close()


# ------------------------------------------------------------------------------


def realtime_tdm_stream_to_pcap_output(p=None, mdid_list=None, pcap=None):
    """ This function reads a binary stream of TmNS Data Messages from a pipe, builds an
        IP packet for the TDM, and then writes the packet to a PCAP/PCAPNG file for offline
        analysis.  The destination IP address and the destination UDP port are set according
        to the TDM's MDID and the associated MDID within the mdid_list.  The function has 3
        input arguments:
        p = the name of the pipe to open and read from
        mdid_list - a list of MessageDefinition objects
        pcap = the name of the PCAP/PCAPNG file to write packets out to."""

    if os.path.exists(p) is False:
        os.mkfifo(p)  # Create Named Pipe if it doesn't exist

    # Loop over reading the pipe, parsing out the TDMs and writing to a PCAP file when a TDM is completely read
    tdm_cnt = 0
    print("Named Pipe '{0}' has been opened for reading.  Waiting for Pipe Writer to connect.".format(p))
    pipeout = open(p, 'rb')
    print("Connected to Named Pipe '{0}'.  Reading binary TDMs from pipe.".format(p))

    try:
        while True:
            raw_ver_adf_flags = pipeout.read(4)
            raw_mdid = pipeout.read(4)
            mdid = int.from_bytes(raw_mdid, byteorder='big')
            raw_seqno = pipeout.read(4)
            raw_msglen = pipeout.read(4)
            msglen = int.from_bytes(raw_msglen, byteorder='big')
            len_remaining = msglen - 16
            raw_rest_of_tdm = pipeout.read(len_remaining)

            raw = b"".join([raw_ver_adf_flags, raw_mdid, raw_seqno, raw_msglen, raw_rest_of_tdm])

            if mdid in mdid_list:
                ip_addr = mdid_list[mdid].dst_addr
                dport = mdid_list[mdid].dst_port
            else:
                ip_addr = '239.88.88.88'  # Default IP address to use IF MDID is not found in the MDL file
                dport = 50003  # Default UDP destination port to use IF MDID is not found in the MDL file

            msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
            msg = msg_ip_hdr / UDP(sport=55501, dport=dport) / Raw(raw)

            wrpcap(pcap, msg, append=True)

            tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end=" ")

    except IOError as e:
        if e.errno == errno.EPIPE:
            print("Looks like the pipe closed.  Closing the pipe and will reopen it for listening.")
            pipeout.close()
        else:
            print("some other IOError other than EPIPE. quitting")
            exit(-1)
    except ValueError:
        print("\nPipe Writer has closed.  Closing our Pipe Reader.")
        pipeout.close()


# ------------------------------------------------------------------------------


def replay_tdm_stream_to_network_output(bfile=None, mdid_list=None):
    """ This function reads a binary file of TmNS Data Messages, builds an IP packet for
        the TDM, and then sends the packet out of a network interface.  The destination
        IP address and the destination UDP port are set according to the TDM's MDID and
        the associated MDID within the mdid_list.  The function has 2 input arguments:
        bfile = the name of the binary file to open and read from
        mdid_list - a list of MessageDefinition objects"""

    tdm_list = make_tdm_packet_list(bfile)
    tdm_cnt = len(tdm_list)
    pkt_list = []

    for i, tdm in enumerate(tdm_list):
        if tdm.mdid in mdid_list:
            ip_addr = mdid_list[tdm.mdid].dst_addr
            dport = mdid_list[tdm.mdid].dst_port
        else:
            ip_addr = '239.88.88.88'  # Default IP address to use IF MDID is not found in the MDL file
            dport = 50003  # Default UDP destination port to use IF MDID is not found in the MDL file
        msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
        msg = msg_ip_hdr / UDP(sport=55501, dport=dport) / Raw(tdm.get_raw())

        pkt_list.append(msg)

    send(pkt_list, verbose=0)
    print("Sent {0} TDMs out the network.".format(tdm_cnt))


# ------------------------------------------------------------------------------


def replay_tdm_stream_to_pcap_output(bfile=None, mdid_list=None, pcap=None):
    """ This function reads a binary file of TmNS Data Messages, builds an IP packet for
        the TDM, and then writes the packet to a PCAP/PCAPNG file for offline analysis.
        The destination IP address and the destination UDP port are set according
        to the TDM's MDID and the associated MDID within the mdid_list.  The function has 3
        input arguments:
        bfile = the name of the binary file to open and read from
        mdid_list - a list of MessageDefinition objects
        pcap = the name of the PCAP/PCAPNG file to write packets out to."""

    tdm_list = make_tdm_packet_list(bfile)
    tdm_cnt = len(tdm_list)
    pkt_list = []

    for i, tdm in enumerate(tdm_list):
        if tdm.mdid in mdid_list:
            ip_addr = mdid_list[tdm.mdid].dst_addr
            dport = mdid_list[tdm.mdid].dst_port
        else:
            ip_addr = '239.88.88.88'  # Default IP address to use IF MDID is not found in the MDL file
            dport = 50003  # Default UDP destination port to use IF MDID is not found in the MDL file
        msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
        msg = msg_ip_hdr / UDP(sport=55501, dport=dport) / Raw(tdm.get_raw())

        pkt_list.append(msg)

    wrpcap(pcap, pkt_list, append=True)
    print("Wrote {0} TDMs to the PCAP file: {1}".format(tdm_cnt, pcap))


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

        new_mdef = MessageDefinition(name, mdid, 0, dst_addr, dst_port)
        # TODO: do DSCP table lookup. For now, hard-coded to Best Effort

        mdid_dict[mdid] = new_mdef

    return mdid_dict


# ------------------------------------------------------------------------------


def get_list_of_ltcdatasink_mc_addrs(mdl=None, my_roleid=None):
    """ This function parses an MDL file and returns a list of all multicast addresses that
        are associated with the TmNSLTCDataSink capability associated with the TmNSApp referenced
        by the specified RoleID of the component."""

    mcaddrs = []
    msg_refs = []

    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl, mdl_parser)

    roleids = root.xpath("//mdl:RoleID", namespaces=ns)

    for r in roleids:
        if r.text == my_roleid:
            ltc_sink_msg_refs = next(r.iterancestors()).findall("mdl:TmNSLTCDataSink/mdl:MessageDefinitionRefs/"
                                                                "mdl:MessageDefinitionRef", namespaces=ns)
            for ref in ltc_sink_msg_refs:
                msg_refs.append(ref.attrib["IDREF"])

            for mref in msg_refs:
                msg = root.xpath("//mdl:MessageDefinition[@ID='{}']".format(mref), namespaces=ns)
                addr = msg[0].find("mdl:DestinationAddress", namespaces=ns).text
                mcaddrs.append(addr)

    print("Found {} Multicast Groups to subscribe to.".format(len(mcaddrs)))
    return mcaddrs


# ------------------------------------------------------------------------------


def subscribe_to_mc_groups(addrs=None):
    """ This function sends out IGMP join messages for the multicast groups included in
        the list of addresses provided as the function input.  It returns the listening
        socket."""

    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(('', DEFAULT_TDM_PORT))

    for mc in addrs:
        print("subscribing to {}".format(mc))
        mc_req = socket.inet_aton(mc) + socket.inet_aton('0.0.0.0')
        listen_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mc_req)

    return listen_sock


# ------------------------------------------------------------------------------


def sig_handler(sig, frame):
    """ Generic signal handler to catch 'CTRL+C' keystrokes from the uses."""

    # Close down any MC sockets that were opened for listening."
    if mc_sock is not None:
        mc_sock.close()
        print("Closed the MC Listening Socket")

    print("User signals: 'The End'")
    exit(0)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="MODE", help="Command / Mode Selection")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1.0')

    net2tdm_parser = subparsers.add_parser('mi', help="Message Input: Receive IP packets and extract TDMs out")
    tdm2net_parser = subparsers.add_parser('mo', help="Message Output: Receive TDM stream and output as IP packets")

    # Add arguments to the net2tdm parser
    net2tdm_parser.add_argument('-I', action='store', default=None, dest='INTERFACE',
                                help="Interface to listen for incoming TmNS Data Messages on.", type=str)
    net2tdm_parser.add_argument('-i', action='store', default=None, dest='INFILE',
                                help="PCAP or PCAPNG file to extract TmNS Data Messages from.  The presence of this "
                                     "argument will run the software in offline mode.  The absence of this argument "
                                     "will run the software in live-capture mode.", type=str)
    net2tdm_parser.add_argument('-p', action='store', default=None, dest='PIPE',
                                help="Named Pipe to write binary stream of TmNS Data Messages to (default: pipe4tmns).")
    net2tdm_parser.add_argument('-o', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                                help="Output file for storing binary stream of TmNS Data Messages (default: tmns.bin).",
                                type=str)
    net2tdm_parser.add_argument('-m', action='store', default=None, dest='MDL_FILE', help="MDL file with TmNS Data "
                                "Message subscription list (use in conjunction with the -r option).")
    net2tdm_parser.add_argument('-r', action='store', default=None, dest='ROLE_ID', help="RoleID for TmNS node "
                                "identification within the specified MDL configuation file (use with the -m option).")
    net2tdm_parser.add_argument('-P', action='store', default=DEFAULT_TDM_PORT, dest='PORT',
                                help="UDP Port number of TmNS Data Messages.", type=int)
    net2tdm_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_LOAD',
                                help="Quick Load mode will parse the provided input PCAP/PCAPNG file and return all "
                                     "TDMs as fast as possible (e.g. not at 1-for-1 received rate).  Default is "
                                     "received-time rate.")

    # Add arguments to the tdm2net parser
    tdm2net_parser.add_argument('-p', action='store', default=None, dest='PIPE',
                                help="Named Pipe to read binary stream of data from (default: pipe4tmns).")
    tdm2net_parser.add_argument('-i', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                                help="Input file for binary stream of TmNS Data Messages (default: tmns.bin).",
                                type=str)
    tdm2net_parser.add_argument('-o', action='store', default=None, dest='OUTPUT_PCAP_FILE',
                                help="Name of the resulting PCAP file for use in offline playback mode.")
    tdm2net_parser.add_argument('-m', action='store', default=None, dest='MDL_FILE',
                                help="MDL file with TmNS Data Message descriptions for configuration.")
    tdm2net_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_PLAY',
                                help="Quick Play mode will replay the input binary TmNS Data Message stream as fast "
                                     "as possible (e.g. not at 1-for-1 realtime rate).  Default is real-time rate. "
                                     "CAUTION: This mode may saturate your network if outputting onto the wire.")
    cli_args = parser.parse_args()

    g_tdm_cnt = 0  # initialize the Global TDM Counter
    g_pipein = 0
    g_binfile = None

    signal.signal(signal.SIGINT, sig_handler)  # Register signal handler for graceful exiting (e.g. CTRL-C)

    # CLI argument assignments
    mode = cli_args.MODE
    mdid_lookup = {}
    pipe_mode = True
    mc_sock = None

    if mode == 'mi':  # Message Input Mode
        interface = cli_args.INTERFACE
        infile = cli_args.INFILE
        pipename = cli_args.PIPE
        binfile = cli_args.BINFILE
        mdl_file = cli_args.MDL_FILE
        role_id = cli_args.ROLE_ID
        TDM_PORT = cli_args.PORT
        quick_load = cli_args.QUICK_LOAD

        g_binfile = binfile

        # Output Selection Mode: Output to a Named Pipe or to a Binary File
        if pipename is not None:
            pipe_mode = True
            if os.path.exists(pipename) is False:
                os.mkfifo(pipename)  # Create Named Pipe if it doesn't exist
        elif binfile is not None:
            pipe_mode = False
        else:
            print("You must select the destination of the TmNS Data Message binary file: "
                  "pipe (-p) or output file (-o).")
            print("Use '-h' for help menu.")
            exit(0)

        if mdl_file is not None:
            if os.path.exists(mdl_file) is False:
                print("Specified MDL File does not exist.  Try again.")
                exit(-1)

            if role_id is None:
                print("You didn't specify the roleID.  TmNShark needs that if you want it to "
                      "subscribe to the correct subset of TmNS Data Messages.")
                exit(-2)

            mc_list = get_list_of_ltcdatasink_mc_addrs(mdl=mdl_file, my_roleid=role_id)
            mc_sock = subscribe_to_mc_groups(addrs=mc_list)

        # Input Selection Mode: Input from a network interface (live) or from a PCAP/PCAPNG file (offline)
        if infile is None:  # LIVE MODE: No input file is specified.  Run in live capture mode.
            while True:
                if pipe_mode:
                    print("Network Interface -----> ==TDM=PIPE==")
                    live_network_input_to_pipe(iface=interface, p=pipename)  # Code will run in this function call
                    # forever until user quits or pipe breaks
                    os.remove(pipename)  # Pipe must have broken.  Delete it from the filesystem.
                    os.mkfifo(pipename)  # Then, create it all over again, which will ensure the pipe is empty.
                    print("\nRestarting.")
                else:
                    if os.path.exists(binfile):
                        os.remove(binfile)
                    print("Network Interface -----> [TDM BINARY FILE]")
                    live_network_input_to_file(iface=interface)
        else:  # OFFLINE MODE: Input file is specified.  Run in offline mode.
            if pipe_mode:
                print("[PCAP FILE] -----> ==TDM=PIPE==")
                offline_pcap_input_to_pipe(pcap=infile, p=pipename, quick=quick_load)
            else:
                print("[PCAP FILE] -----> [TDM BINARY FILE]")
                offline_pcap_input_to_file(pcap=infile, bfile=binfile, quick=quick_load)  # Code will run in this
                # function until user quits or file is completely read.

    elif mode == 'mo':  # Message Output Mode
        pipename = cli_args.PIPE
        binfile = cli_args.BINFILE
        outfile = cli_args.OUTPUT_PCAP_FILE
        mdl_file = cli_args.MDL_FILE

        # Output Selection Mode: Output to a Named Pipe or to a Binary File
        if pipename is not None:
            pipe_mode = True
            if os.path.exists(pipename) is False:
                os.mkfifo(pipename)  # Create Named Pipe if it doesn't exist
        elif binfile is not None:
            pipe_mode = False
        else:
            print("You must select the source of the TmNS Data Message binary file: pipe (-p) or input file (-i).")
            print("Use '-h' for help menu.")
            exit(0)

        # MDL file is required.  Check that argument is provided by the user.
        if mdl_file is None:
            print("You must provide an MDL file with this mode.")
            print("Use '-h' for help menu.")
            exit(0)

        mdid_lookup = parse_mdl(mdl=mdl_file)  # Parse MDL file for TmNS Data Message descriptions

        if pipe_mode:
            while True:
                if outfile is None:
                    print("==TDM=PIPE== -----> Network Interface")
                    realtime_tdm_stream_to_network_output(p=pipename, mdid_list=mdid_lookup)
                else:
                    print("==TDM=PIPE== -----> [PCAP FILE]")
                    realtime_tdm_stream_to_pcap_output(p=pipename, mdid_list=mdid_lookup, pcap=outfile)
                print("Restarting...")
        else:
            if outfile is None:
                print("[TDM BINARY FILE] -----> Network Interface")
                replay_tdm_stream_to_network_output(bfile=binfile, mdid_list=mdid_lookup)
            else:
                print("[TDM BINARY FILE] -----> [PCAP FILE]")
                replay_tdm_stream_to_pcap_output(bfile=binfile, mdid_list=mdid_lookup, pcap=outfile)

    else:
        print("You must select a mode: Message Input (mi) or Message Output (mo).")
        print("Use '-h' for help menu.")
