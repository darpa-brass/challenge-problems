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

from TmNShark.TmNSquid.actions import preprocess_mdl
from TmNShark.TmNSquid.actions import make_tdm_packet_list
from TmNShark.TmNSquid.actions import realtime_tdm_stream_to_network_output


def main():
    parser = argparse.ArgumentParser(description="It's a squid.")

    # required
    parser.add_argument("input", help="Binary file or pipe full of TDMs")
    parser.add_argument("mdl", help="Binary file full of TDMs")

    # optional
    parser.add_argument("-p", "--pipe", dest="is_pipe", help="Pipe or binary file.")

    args = parser.parse_args()

    print(args)

    package_decoders = preprocess_mdl(args.mdl)
    # make_tdm_packet_list(args.input, package_decoders)
    if args.is_pipe:  # it's a pipe
        while True:
            realtime_tdm_stream_to_network_output(args.input, package_decoders)
    else:  # it's a binary file
        realtime_tdm_stream_to_network_output(args.input, package_decoders)


# Test whether it's faster to read in a lot of bits at once, or a lot of small chunks.
def test():
    f = open("./noise", "rb")
    for i in range(100):
        f.read(1)


def test2():
    f = open("./noise", "rb")
    f.read(100)


if __name__ == "__main__":
    # cProfile.run('main()')
    main()

