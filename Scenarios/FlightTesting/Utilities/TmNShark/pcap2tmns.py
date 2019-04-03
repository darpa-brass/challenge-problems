# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---                     PCAP to TmNS Data Message File                     ---
# ---                                                                        ---
# --- Last Updated: March 20, 2019                                           ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import sys
import os
import argparse
import time
import errno
import signal
from time import sleep
from scapy.all import *
from lxml import etree
import numpy as np

ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

DEFAULT_TDM_PORT = 50003
DEFAULT_BINARY_TDM_FILE = "tmns.bin"

#infile = "TmNS_Data_Messages_DAU_1.pcapng"

class TmnsDataMessage:
    '''Class to contain TmNS Data Message Structures'''

    def __init__(self, ver=1, adf_words=0, flags=0, mdid=0, seqno=0, len=24, secs=0, nanosecs=0, adf_payload=None, payload=None):
        self.ver = ver
        self.adf_words=adf_words
        self.flags = flags
        self.mdid = mdid
        self.seqno = seqno
        self.len = len
        self.time_sec = secs
        self.time_nanosec = nanosecs
        self.adf_payload = adf_payload
        self.payload = payload

    def get_raw(self):
        rsvd = 0
        raw_ver_adf = ((self.ver << 4) | self.adf_words).to_bytes(1, byteorder='big', signed=False)
        raw_rsvd = rsvd.to_bytes(1, byteorder='big', signed=False)
        raw_flags = (self.flags).to_bytes(2, byteorder='big', signed=False)
        raw_mdid = (self.mdid).to_bytes(4, byteorder='big', signed=False)
        raw_seqno = (self.seqno).to_bytes(4, byteorder='big', signed=False)
        raw_len = (self.len).to_bytes(4, byteorder='big', signed=False)
        raw_sec = (self.time_sec).to_bytes(4, byteorder='big', signed=False)
        raw_nanosec = (self.time_nanosec).to_bytes(4, byteorder='big', signed=False)

        raw = b"".join([raw_ver_adf, raw_rsvd, raw_flags, raw_mdid, raw_seqno,
                        raw_len, raw_sec, raw_nanosec, self.payload])
        return raw


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class MessageDefinition:
    '''Class to contain Message Definitions'''

    def __init__(self, name='', mdid=0xffffffff, dscp=0, dst_addr='239.255.255.254', dst_port=50003):
        self.name = name
        self.mdid = mdid
        self.dscp = dscp
        self.dst_addr = dst_addr
        self.dst_port = dst_port


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def write_packet_to_pipe(pkt):
    global tdm_cnt
    global pipein
    
    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            pipein.write(bytes(pkt[UDP].payload))
            tdm_cnt +=1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end =" ")


# ------------------------------------------------------------------------------


def write_packet_to_file(pkt):
    global tdm_cnt
    global pipein

    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            f = open(binfile, 'a+b')
            f.write(bytes(pkt[UDP].payload))
            f.close()
            tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end=" ")


# ------------------------------------------------------------------------------


def make_tdm_packet_list(bin):
    tdm_list = []
    msg_cnt = 0

    if os.path.exists(bin):
        with open(bin, mode='rb') as f:
            num_bytes = os.path.getsize(bin)
            while (f.tell() < num_bytes):
                ver_adf = f.read(1)
                ver = int.from_bytes(ver_adf, byteorder='big') >> 4
                adf_words = int.from_bytes(ver_adf, byteorder='big') & 0x0f
                f.read(1)       # Read byte.  Field is RESERVED
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

                new_msg = TmnsDataMessage(ver=ver, flags=flags, mdid=mdid, seqno=seqno, len=msglen, secs=secs,
                                          nanosecs=nanosecs, adf_payload= adf_payload, payload=payload)
                tdm_list.append(new_msg)
                msg_cnt = len(tdm_list)
        return tdm_list
    else:
        print("The file '{0}' was not found.".format(bin))
        return tdm_list


# ------------------------------------------------------------------------------


def live_network_input_to_pipe():
    global interface
    global tdm_cnt
    global pipein

    print("Named Pipe '{0}' has been opened for writing.  Waiting for Pipe Reader to connect.".format(pipe))
    pipein = open(pipe, 'wb')
    print("Connected to Named Pipe '{0}'.  Writing binary TDMs into pipe.".format(pipe))

    if interface is None:
        print("Listening on default interface.")
        try:
            sniff(prn=write_packet_to_pipe)
        except IOError as e:
            print("got an IOError")
            if e.errno == errno.EPIPE:
                print("its an EPIPE")
    else:
        print("Listening on interface: {0}".format(interface))
        try:
            sniff(iface=interface, prn=write_packet_to_pipe)
        except IOError as e:
            if e.errno == errno.EPIPE:
                print("Broken Pipe: EPIPE")


# ------------------------------------------------------------------------------


def live_network_input_to_file():
    global interface
    global tdm_cnt
    global pipein

    if os.path.exists(binfile):
        os.remove(binfile)

    if interface is None:
        print("Listening on default interface.")
        sniff(prn=write_packet_to_file)
    else:
        print("Listening on interface: {0}".format(interface))
        sniff(iface=interface, prn=write_packet_to_file)


# ------------------------------------------------------------------------------


def offline_pcap_input_to_pipe():
    global tdm_cnt

    print("Offline mode: Reading TDMs from PCAP/PCAPNG file and writing to pipe.")
    pkt_list = rdpcap(infile)  # read the PCAP/PCAPNG file and return a list of packets

    # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
    print("Named Pipe '{0}' has been opened for writing.  Waiting for Pipe Reader to connect.".format(pipe))
    pipeout = open(pipe, 'wb')
    print("Connected to Named Pipe '{0}'.  Writing binary TDMs into pipe.".format(pipe))

    delta_from_current_time = time.time() - pkt_list[0].time

    for pkt in pkt_list:
        if pkt[UDP].dport == TDM_PORT:
            if quick_load is False:
                while (pkt.time + delta_from_current_time) > time.time():
                    sleep(0.0001)
            pipeout.write(bytes(pkt[UDP].payload))
            tdm_cnt += 1
            print("\rTDM Count: {0}".format(tdm_cnt), end=" ")
    pipeout.close()

    if tdm_cnt == 0:
        print("ZERO TmNS Data Messages found in {0}.  No data written to {1}.".format(infile, pipe))
    else:
        print("\nComplete.  There were {0} TmNS Data Messages written to {1}.".format(tdm_cnt, pipe))

    #while True:
    #    print("  'q' to quit  |  'h' to hexdump TDMs  ")
    #    choice = input()
    #    if choice == 'h':
    #        os.system("hexdump -C {}".format(binfile))
    #    elif choice == 'q':
    #        print('q: quitting')
    #        break


# ------------------------------------------------------------------------------


def offline_pcap_input_to_file():
    global tdm_cnt

    print("Offline mode: Reading TDMs from PCAP/PCAPNG file and writing to file.")
    pkt_list = rdpcap(infile)  # read the PCAP/PCAPNG file and return a list of packets

    # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
    f = open(binfile, 'w+b')

    delta_from_current_time = time.time() - pkt_list[0].time

    for pkt in pkt_list:
        if pkt[UDP].dport == TDM_PORT:
            if quick_load is False:
                while (pkt.time + delta_from_current_time) > time.time():
                    sleep(0.0001)
            f.write(bytes(pkt[UDP].payload))
            tdm_cnt += 1
            print("\rTDM Count: {0}".format(tdm_cnt), end=" ")
    f.close()

    if tdm_cnt == 0:
        print("ZERO TmNS Data Messages found in {0}.  {1} is empty.".format(infile, binfile))
    else:
        print("\nComplete.  Binary file of {0} TmNS Data Messages is stored at {1}.".format(tdm_cnt, binfile))


# ------------------------------------------------------------------------------


def realtime_tdm_stream_to_network_output(mdid_lookup):
    global interface

    if os.path.exists(pipe) is False:
        os.mkfifo(pipe)      # Create Named Pipe if it doesn't exist

    # Loop over reading the pipe, parsing out the TDMs and sending over the network when a TDM is completely read
    tdm_cnt = 0
    print("Named Pipe '{0}' has been opened for reading.  Waiting for Pipe Writer to connect.".format(pipe))
    pipeout = open(pipe, 'rb')
    print("Connected to Named Pipe '{0}'.  Reading binary TDMs from pipe.".format(pipe))

    if interface is None:
        print("Outgoing TDMs on default Network Interface.")
    else:
        print("Outgoing TDMs on Network Interface: {0}".format(interface))

    try:
        while True:
            raw_ver_adf_flags = pipeout.read(4) #os.read(pipein, 4)
            raw_mdid = pipeout.read(4) #os.read(pipein, 4)
            mdid = int.from_bytes(raw_mdid, byteorder='big')
            #mdid = mdid + 3992977408        # TODO: REMOVE...THIS IS TEMPORARY
            mdid = mdid + 16        # TODO: REMOVE...THIS IS TEMPORARY
            print(" mdid: 0x{0:08x}".format(mdid))      # TODO: REMOVE...THIS IS TEMPORARY
            raw_mdid = mdid.to_bytes(4, byteorder='big', signed=False)      # TODO: REMOVE...THIS IS TEMPORARY
            raw_seqno = pipeout.read(4) #os.read(pipein, 4)
            raw_msglen = pipeout.read(4) #os.read(pipein, 4)
            msglen = int.from_bytes(raw_msglen, byteorder='big')
            #print("ver|flags|rsvd|flags = {}".format(int.from_bytes(raw_ver_adf_flags, byteorder='big')))
            #print("MDID = {}".format(int.from_bytes(raw_mdid, byteorder='big')))
            #print("seq # = {}".format(int.from_bytes(raw_seqno, byteorder='big')))
            #print("msglen is {}.  Is this greater than 16?".format(msglen))
            len_remaining = msglen - 16
            print("remaining length: {}".format(len_remaining))
            raw_rest_of_tdm = pipeout.read(len_remaining) #os.read(pipein, len_remaining)

            raw = b"".join([raw_ver_adf_flags, raw_mdid, raw_seqno, raw_msglen, raw_rest_of_tdm])

            if mdid in mdid_lookup:
                ip_addr = mdid_lookup[mdid].dst_addr
                #ip_addr = '10.1.1.201'
                dport = mdid_lookup[mdid].dst_port
            else:
                ip_addr = '239.88.88.88'    # Default IP address to use IF MDID is not found in the MDL file
                #ip_addr = '10.1.1.201'
                #ip_addr = '172.16.0.27'  # TODO: REMOVE...THIS IS TEMPORARY
                dport = 50003               # Default UDP destination port to use IF MDID is not found in the MDL file

            msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
            msg = msg_ip_hdr / UDP(sport=55501, dport=dport) / Raw(raw)

            if interface is None:
                send(msg, verbose=0)
            else:
                send(msg, iface=interface, verbose=0)

            tdm_cnt += 1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end=" ")
    except IOError as e:
        if e.errno == errno.EPIPE:
            print("Looks like the pipe closed.  Closing the pipe and will reopen it for listening.")
            pipeout.close()
        else:
            print("some other IOError other than EPIPE. quitting")
            exit(-1)
    except BrokenPipeError as e:
        if e.errno == errno.EPIPE:
            print("errno is EPIPE")
        print("broken pipe error occurred.")
    except ValueError:
        print("\nPipe Writer has closed.  Closing our Pipe Reader.")
        pipeout.close()


# ------------------------------------------------------------------------------


def replay_tdm_stream_to_network_output(mdid_lookup):
    tdm_list = make_tdm_packet_list(binfile)
    tdm_cnt = len(tdm_list)
    pkt_list = []

    for i, tdm in enumerate(tdm_list):
        if tdm.mdid in mdid_lookup:
            ip_addr = mdid_lookup[tdm.mdid].dst_addr
            dport = mdid_lookup[tdm.mdid].dst_port
        else:
            ip_addr = '239.88.88.88'    # Default IP address to use IF MDID is not found in the MDL file
            dport = 50003               # Default UDP destination port to use IF MDID is not found in the MDL file
        msg_ip_hdr = IP(version=4, ihl=5, flags='DF', ttl=4, dst=ip_addr)
        msg = msg_ip_hdr/UDP(sport=55501, dport=dport)/Raw(tdm.get_raw())

        pkt_list.append(msg)

    if interface is None:
        send(pkt_list, verbose=0)
    else:
        send(pkt_list, inter=interface, verbose=0)

# ------------------------------------------------------------------------------


def parse_mdl(mdl_file):
    mdid_dict = {}

    if os.path.exists(mdl_file) is False:
        print("MDL file not found.  Using defaults for MDID and Multicast Addresses.")
        return mdid_dict

    # Parse MDL file, and create the mapping between MDIDs and their associated Multicast IP Address
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl_file, mdl_parser)

    messages = root.xpath("//mdl:MessageDefinition", namespaces=ns)
    for message in messages:
        name = message.find("mdl:Name", namespaces=ns).text
        mdid = int(message.find("mdl:MessageDefinitionID", namespaces=ns).text, 16)
        dscp = message.find("mdl:DSCPTableEntryRef", namespaces=ns).text
        dst_addr = message.find("mdl:DestinationAddress", namespaces=ns).text
        dst_port = int(message.find("mdl:DestinationPort", namespaces=ns).text)

        new_mdef = MessageDefinition(name, mdid, 0, dst_addr, dst_port)         # TODO: do DSCP table lookup. For now, hard-coded to Best Effort
        mdid_dict[mdid] = new_mdef

    return mdid_dict


# ------------------------------------------------------------------------------


def sig_handler(sig, frame):
    print("User signals: 'The End'")
    exit(0)


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="MODE", help="Command / Mode Selection")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.3')

    net2tdm_parser = subparsers.add_parser('ni', help="Network Input: Receive IP packets and extract TDMs out")
    tdm2net_parser = subparsers.add_parser('no', help="Network Output: Receive TDM stream and output them in IP packets")

    # Add arguments to the net2tdm parser
    net2tdm_parser.add_argument('-I', action='store', default=None, dest='INTERFACE',
                        help="Interface to listen for incoming TmNS Data Messages on.", type=str)
    net2tdm_parser.add_argument('-i', action='store', default=None, dest='INFILE',
                        help="PCAP or PCAPNG file to extract TmNS Data Messages from.  The presence of this argument "
                             "will run the software in offline mode.  The absence of this argument will run the "
                             "software in live-capture mode.", type=str)
    net2tdm_parser.add_argument('-p', action='store', default=None, dest='PIPE',
                        help="Named Pipe to write binary stream of TmNS Data Messages to (default: pipe4tmns).")
    net2tdm_parser.add_argument('-o', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                        help="Output file for storing binary stream of TmNS Data Messages (default: tmns.bin).",
                        type=str)
    net2tdm_parser.add_argument('-P', action='store', default=DEFAULT_TDM_PORT, dest='PORT',
                        help="UDP Port number of TmNS Data Messages.", type=int)
    net2tdm_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_LOAD',
                        help="Quick Load mode will parse the provided input PCAP/PCAPNG file and return all "
                        "TDMs as fast as possible (e.g. not at 1-for-1 received rate).  Default is received-time rate.")

    # Add arguments to the tdm2net parser
    tdm2net_parser.add_argument('-p', action='store', default=None, dest='PIPE',
                                help="Named Pipe to read binary stream of data from (default: pipe4tmns).")
    tdm2net_parser.add_argument('-i', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                        help="Input file for binary stream of TmNS Data Messages (default: tmns.bin).",
                        type=str)
    tdm2net_parser.add_argument('-I', action='store', default=None, dest='INTERFACE',
                        help="Interface to send outgoing TmNS Data Messages on. CURRENTLY BROKEN!!!", type=str)
    tdm2net_parser.add_argument('-o', action='store', default=None, dest='OUTPUT_PCAP_FILE',
                        help="Name of the resulting PCAP file for use in offline playback mode. NOT YET IMPLEMENTED!")
    tdm2net_parser.add_argument('-m', action='store', default=None, dest='MDL_FILE',
                        help="MDL file with TmNS Data Message descriptions for configuration.")
    tdm2net_parser.add_argument('-r', action='store_true', default=False, dest='REPLAY',
                        help="Replay the binary TmNS Data Message file over the network.  If not set, the application "
                             "will run in live mode reading from the named pipe (see arg '-i').")
    tdm2net_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_PLAY',
                                help="Quick Play mode will replay the input binary TmNS Data Message stream as fast"
                                     "as possible (e.g. not at 1-for-1 realtime rate).  Default is real-time rate. "
                                     "CAUTION: This mode may saturate your network if outputting onto the wire.")
    cli_args = parser.parse_args()

    tdm_cnt = 0     # initialize the TDM Count

    signal.signal(signal.SIGINT, sig_handler)  # Register signal handler for graceful exiting (e.g. CTRL-C)

    # CLI argument assignments
    mode = cli_args.MODE
    mdid_lookup = {}
    pipein = 0
    pipeout = 0

    if mode == 'ni':
        interface = cli_args.INTERFACE
        infile = cli_args.INFILE
        pipe = cli_args.PIPE
        binfile = cli_args.BINFILE
        TDM_PORT = cli_args.PORT
        quick_load = cli_args.QUICK_LOAD

        # Output Selection Mode: Output to a Named Pipe or to a Binary File
        if pipe is not None:
            pipe_mode = True
            if os.path.exists(pipe) is False:
                os.mkfifo(pipe)  # Create Named Pipe if it doesn't exist
        elif binfile is not None:
            pipe_mode = False
        else:
            print("You must select the destination of the TmNS Data Message binary file: "
                  "pipe (-p) or output file (-o).")
            print("Use '-h' for help menu.")
            exit(0)

        # Input Selection Mode: Input from a network interface (live) or from a PCAP/PCAPNG file (offline)
        if infile is None:              # LIVE MODE: No input file is specified.  Run in live capture mode.
            live_mode = True
            while True:
                if pipe_mode:
                    live_network_input_to_pipe()    # Code will run in this function call forever until user quits or pipe breaks
                    os.remove(pipe)         # Pipe must have broken.  Delete it from the filesystem.
                    os.mkfifo(pipe)         # Then, create it all over again, which will ensure the pipe is empty.
                    print("\nRestarting.")
                else:
                    live_network_input_to_file()
        else:                           # OFFLINE MODE: Input file is specified.  Run in offline mode.
            live_mode = False
            if pipe_mode:
                offline_pcap_input_to_pipe()
            else:
                offline_pcap_input_to_file()        # Code will run in this function until user quits or file is completely read.

    elif mode == 'no':
        pipe = cli_args.PIPE
        binfile = cli_args.BINFILE
        interface = cli_args.INTERFACE
        outfile = cli_args.OUTPUT_PCAP_FILE
        mdl_file = cli_args.MDL_FILE
        replay = cli_args.REPLAY
        quick_play = cli_args.QUICK_PLAY

        if pipe is not None:
            pipe_mode = True
            if os.path.exists(pipe) is False:
                os.mkfifo(pipe)                     # Create Named Pipe if it doesn't exist
        elif binfile is not None:
            pipe_mode = False
        else:
            print("You must select the source of the TmNS Data Message binary file: pipe (-p) or input file (-i).")
            print("Use '-h' for help menu.")
            exit(0)

        if mdl_file is None:
            print("You must provide an MDL file with this mode.")
            print("Use '-h' for help menu.")
            exit(0)

        mdid_lookup = parse_mdl(mdl_file)

        if replay is False:
            live_mode = True
            while True:
                realtime_tdm_stream_to_network_output(mdid_lookup)
                print("Restarting...")
        else:
            live_mode = False
            replay_tdm_stream_to_network_output(mdid_lookup)
    else:
        print("You must select a mode: Network Input (ni) or Network Output (no).")
        print("Use '-h' for help menu.")

    #main()
    
                        