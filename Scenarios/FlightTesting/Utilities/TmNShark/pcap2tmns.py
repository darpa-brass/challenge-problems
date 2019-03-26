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
from time import sleep
from scapy.all import *
import numpy as np

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

    #def set_tdm_payload(self, payload):
    #    if len(payload) == len(self.payload):
    #        self.payload =

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

        raw = b"".join([raw_ver_adf, raw_rsvd, raw_flags, raw_mdid, raw_seqno, raw_len, raw_sec, raw_nanosec, self.payload])
        return raw


def write_packet_to_file(pkt):
    global tdm_cnt
    
    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            f = open(binfile, 'a+b')
            f.write(bytes(pkt[UDP].payload))
            f.close()
            tdm_cnt +=1
            print("\rTDM Count: {0}.    CTRL-C to quit".format(tdm_cnt), end =" ")

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


def main():                 # TODO: This probably goes away...
    global interface
    global live_mode
    global tdm_cnt
    
    if infile is not None:
        live_mode = False
        print("Offline mode: Reading TDMs from PCAP/PCAPNG file.")

    if live_mode:
        if interface is None:
            print("Listening on default interface.")
            interface = ''
            if os.path.exists(binfile):
                os.remove(binfile)
            sniff(prn=write_packet_to_file)
        else:
            print("Listening on interface: {0}".format(interface))
            if os.path.exists(binfile):
                os.remove(binfile)
            sniff(iface=interface, prn=write_packet_to_file)
    
    # Offline Mode is associated with reading TDMs from an input PCAP/PCAPNG file
    else:
        pkt_list = rdpcap(infile)       # read the PCAP/PCAPNG file and return a list of packets

        delta_from_current_time = time.time() - pkt_list[0].time
        
        # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
        f = open(binfile, 'w+b')
        for pkt in pkt_list:
            if pkt[UDP].dport == TDM_PORT:
                if quick_load is False:
                    while (pkt.time + delta_from_current_time) > time.time():
                        sleep(0.0001)
                f.write(bytes(pkt[UDP].payload))
                tdm_cnt += 1
                print("\rTDM Count: {0}".format(tdm_cnt), end =" ")
        f.close()
    
        if tdm_cnt == 0:
            print("ZERO TmNS Data Messages found in {0}.  {1} is empty.".format(infile, binfile))
        else:
            print("\nComplete.  Binary file of {0} TmNS Data Messages is stored at {1}.".format(tdm_cnt, binfile))

        while True:
            print("  'q' to quit  |  'h' to hexdump TDMs  ")
            choice = input()
            if choice == 'h':
                os.system("hexdump -C {}".format(binfile))
            elif choice == 'q':
                print('q: quitting')
                break

    if replay:
        if live_mode:
            pass        # TODO: read from pipe and create new packets as new TDMs become available
        else:
            tdm_list = make_tdm_packet_list(binfile)
            print("{}".format(tdm_list[0].seqno))


# ------------------------------------------------------------------------------


def live_network_input():
    global interface
    global tdm_cnt

    if interface is None:
        print("Listening on default interface.")
        interface = ''
        if os.path.exists(binfile):
            os.remove(binfile)
        sniff(prn=write_packet_to_file)
    else:
        print("Listening on interface: {0}".format(interface))
        if os.path.exists(binfile):
            os.remove(binfile)
        sniff(iface=interface, prn=write_packet_to_file)


# ------------------------------------------------------------------------------


def offline_pcap_input():
    global tdm_cnt

    print("Offline mode: Reading TDMs from PCAP/PCAPNG file.")
    pkt_list = rdpcap(infile)  # read the PCAP/PCAPNG file and return a list of packets

    delta_from_current_time = time.time() - pkt_list[0].time

    # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
    f = open(binfile, 'w+b')
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

    while True:
        print("  'q' to quit  |  'h' to hexdump TDMs  ")
        choice = input()
        if choice == 'h':
            os.system("hexdump -C {}".format(binfile))
        elif choice == 'q':
            print('q: quitting')
            break


# ------------------------------------------------------------------------------


def realtime_tdm_stream_to_network_output():
    pass


# ------------------------------------------------------------------------------


def replay_tdm_stream_to_network_output():
    tdm_list = make_tdm_packet_list(binfile)
    tdm_cnt = len(tdm_list)

    for i, tdm in enumerate(tdm_list):
        msg = IP(version=4, ihl=5, flags='DF', ttl=4, src='172.16.0.31', dst='239.255.0.1')/UDP(sport=55501, dport=50003)/Raw(tdm.get_raw())
        sr1(msg)
        break




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
    net2tdm_parser.add_argument('-o', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                        help="Output file or pipe for storing binary stream of TmNS Data Messages (defaut: tmns.bin).",
                        type=str)
    net2tdm_parser.add_argument('-p', action='store', default=DEFAULT_TDM_PORT, dest='PORT',
                        help="UDP Port number of TmNS Data Messages.", type=int)
    net2tdm_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_LOAD',
                        help="Quick Load mode will parse the provided input PCAP/PCAPNG file and return all "
                        "TDMs as fast as possible (e.g. not at 1-for-1 received rate).  Default is received-time rate.")

    # Add arguments to the tdm2net parser
    tdm2net_parser.add_argument('-i', action='store', default=DEFAULT_BINARY_TDM_FILE, dest='BINFILE',
                        help="Input file or pipe for stream of TmNS Data Messages (defaut: tmns.bin).",
                        type=str)
    tdm2net_parser.add_argument('-o', action='store', default=None, dest='OUTPUT_PCAP_FILE',
                        help="Name of the resulting PCAP file for use in offline playback mode.")
    tdm2net_parser.add_argument('-m', action='store', default=None, dest='MDL_FILE',
                        help="MDL file with TmNS Data Message descriptions for configuration.")
    tdm2net_parser.add_argument('-r', action='store_true', default=False, dest='REPLAY',
                        help="Replay the binary TmNS Data Message file over the network.")
    tdm2net_parser.add_argument('-q', action='store_true', default=False, dest='QUICK_PLAY',
                                help="Quick Play mode will replay the input binary TmNS Data Message stream as fast"
                                     "as possible (e.g. not at 1-for-1 realtime rate).  Default is real-time rate. "
                                     "CAUTION: This mode may saturate your network if outputting onto the wire.")
    cli_args = parser.parse_args()

    tdm_cnt = 0     # initialize the TDM Count

    # CLI argument assignments
    mode = cli_args.MODE

    if mode == 'ni':
        interface = cli_args.INTERFACE
        infile = cli_args.INFILE
        binfile = cli_args.BINFILE
        TDM_PORT = cli_args.PORT
        quick_load = cli_args.QUICK_LOAD

        if infile is None:
            live_mode = True
            live_network_input()
        else:
            live_mode = False
            offline_pcap_input()
    elif mode == 'no':
        binfile = cli_args.BINFILE
        outfile = cli_args.OUTPUT_PCAP_FILE
        mdl_file = cli_args.MDL_FILE
        replay = cli_args.REPLAY
        quick_play = cli_args.QUICK_PLAY

        if replay is False:
            live_mode = True
            realtime_tdm_stream_to_network_output()
        else:
            live_mode = False
            replay_tdm_stream_to_network_output()
    else:
        print("You must select a mode: Network Input (ni) or Network Output (no).")
        print("Use '-h' for help menu.")

    #interface = cli_args.INTERFACE
    #infile = cli_args.INFILE
    #binfile = cli_args.BINFILE
    #TDM_PORT = cli_args.PORT
    #quick_load = cli_args.QUICK_LOAD
    #mdl_file = cli_args.MDL_FILE
    #replay = cli_args.REPLAY
    
    #live_mode = True
    #tdm_cnt = 0

    #main()
    
                        