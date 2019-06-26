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


def main():
    parser = argparse.ArgumentParser(description="It's a squid.")
    parser.add_argument("mdl", help="Binary file full of TDMs")

    parser.add_argument("--binfile", help="Binary file full of TDMs")

    args = parser.parse_args()

    print(args)

    package_decoders = preprocess_mdl(args.mdl)
    make_tdm_packet_list(args.binfile, package_decoders)


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
    # print(timeit.timeit(test, number=100))
    # print(timeit.timeit(test2, number=100))

