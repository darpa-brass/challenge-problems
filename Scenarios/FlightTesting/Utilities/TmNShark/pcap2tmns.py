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

DEFAULT_TDM_PORT = 50003
DEFAULT_BINARY_OUTPUT_FILE = "tmns.bin"

#infile = "TmNS_Data_Messages_DAU_1.pcapng"

def write_packet_to_file(pkt):
    global tdm_cnt
    
    if UDP in pkt:
        if pkt[UDP].dport == TDM_PORT:
            f = open(outfile, 'a+b')
            f.write(bytes(pkt[UDP].payload))
            f.close()
            tdm_cnt +=1
            print("\rTDM Count: {0}".format(tdm_cnt), end =" ")

def main():
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
            #sniff(prn=lambda x: x.summary())
            f = open(outfile, 'w+b')
            f.close()
            sniff(prn=write_packet_to_file)
        else:
            print("Listening on interface: {0}".format(interface))
            f = open(outfile, 'w+b')
            f.close()
            sniff(iface=interface, prn=lambda x: x.summary())
    
    # Offline Mode is associated with reading TDMs from an input PCAP/PCAPNG file
    else:
        pkt_list = " "
        pkt_list = rdpcap(infile)       # read the PCAP/PCAPNG file and return a list of packets

        delta_from_current_time = time.time() - pkt_list[0].time
        
        # Parse the Packet List for TmNS Data Messages (TDMs), and write them to the binary TDM file
        f = open(outfile, 'w+b')
        for pkt in pkt_list:
            if pkt[UDP].dport == TDM_PORT:
                if quick_load is False:
                    while (pkt.time + delta_from_current_time) > time.time():
                        sleep(0.0001)
                f.write(bytes(pkt[UDP].payload))
                tdm_cnt += 1
                #print(tdm_cnt)
        f.close()
    
        if tdm_cnt == 0:
            print("ZERO TmNS Data Messages found in {0}.  {1} is empty.".format(infile, outfile))
        else:
            print("Complete.  Binary file of {0} TmNS Data Messages is stored at {1}.".format(tdm_cnt, outfile))

        while True:
            print("  'q' to quit  |  'h' to hexdump TDMs  ")
            choice = input()
            if choice == 'h':
                os.system("hexdump -C {}".format(outfile))
            elif choice == 'q':
                print('q: quitting')
                break
                
    

if __name__ == "__main__":
    # Argumnet Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-I', action='store', default=None, dest='INTERFACE', 
                        help="Interface to listen for incoming TmNS Data Messages on.", type=str)
    parser.add_argument('-i', action='store', default=None, dest='INFILE', 
                        help="PCAP or PCAPNG file to extract TmNS Data Messages from.", type=str)
    parser.add_argument('-o', action='store', default=DEFAULT_BINARY_OUTPUT_FILE, dest='OUTFILE', 
                        help="Output file for storing binary stream of TmNS Data Messages (defaut: tmns.bin).", 
                        type=str)
    parser.add_argument('-p', action='store', default=DEFAULT_TDM_PORT, dest='PORT', 
                        help="UDP Port number of TmNS Data Messages.", type=int)
    parser.add_argument('-q', action='store_true', default=False, dest='QUICK_LOAD',
                        help="Quick Load mode will parse the provided input PCAP/PCAPNG file and return all "
                        "TDMs as fast as possible (e.g. not at 1-for-1 playback rate).  Default is playback rate.")
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')
    cli_args = parser.parse_args()
    
    # CLI argument assignments
    interface = cli_args.INTERFACE
    infile = cli_args.INFILE
    outfile = cli_args.OUTFILE
    TDM_PORT = cli_args.PORT
    quick_load = cli_args.QUICK_LOAD
    
    live_mode = True    
    tdm_cnt = 0
            
    main()
    
                        