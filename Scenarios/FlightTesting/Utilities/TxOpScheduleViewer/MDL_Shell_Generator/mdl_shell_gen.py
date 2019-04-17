# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ---                          MDL Shell Generator                           ---
# ---                                                                        ---
# --- Last Updated: April 17, 2019                                            ---
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

import sys
import os
import argparse
from lxml import etree
import json

ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}


# shortcut dictionary for passing common arguments
n = {"namespaces": ns}

debug = 0               # Debug value: initially 0, e.g. no debug

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


class RadioLink:
    """Class to contain Radio Link info"""
    
    def __init__(self, name, id_attr, src, dst, qp=None, lat=0):
        self.name = name
        self.id = id_attr
        self.src = src
        self.dst = dst
        self.tx_sched = []
        self.qos_policy = qp
        self.max_latency_usec = lat             # Maximum Possible Latency achievable
        self.tx_dur_per_epoch_usec = 0
        self.alloc_bw_mbps = 0
        self.latency_point_value = 0
        self.throughput_point_value = 0

    def add_txop(self, txop):
        self.tx_sched.append(txop)
        self.tx_dur_per_epoch_usec += txop.duration_usec

    def calc_max_latency(self, epoch_usec):
        # initialize max_latency_usec with wrap-around TxOps
        if len(self.tx_sched) > 0:
            self.max_latency_usec = (int(epoch_usec) - (int(self.tx_sched[-1].stop_usec) + 1)) + \
                                    int(self.tx_sched[0].start_usec)
        else:
            self.max_latency_usec = 0
        
        # iterate through the Link's TxOp Schedule, and compare latencies between TxOps with the previous max latency
        for i in range(len(self.tx_sched) - 1):
            temp_latency = int(self.tx_sched[i+1].start_usec) - (int(self.tx_sched[i].stop_usec) + 1)
            if temp_latency > self.max_latency_usec:
                self.max_latency_usec = temp_latency

    def calc_alloc_bw_mbps(self, epoch_ms):
        self.alloc_bw_mbps = ((int(self.tx_dur_per_epoch_usec) * (1000 / int(epoch_ms))) / 1000000) * MAX_BW_MBPS

    def calc_latency_value(self, max_points_thd_ms, min_points_thd_ms):
        if self.max_latency_usec < int(max_points_thd_ms*1000):
            self.latency_point_value = 100
        elif self.max_latency_usec < int(min_points_thd_ms*1000):
            ans = 100 - (self.max_latency_usec - int(max_points_thd_ms*1000)) ** 2
            if ans > 0:
                self.latency_point_value = ans
            else:
                self.latency_point_value = 0
        else:
            self.latency_point_value = 0

    def calc_throughput_value(self, min_points_thd, max_points_thd, coef):
        alloc_bw_kbps = self.alloc_bw_mbps * 1000
        if alloc_bw_kbps < min_points_thd:
            self.throughput_point_value = 0.0
        elif alloc_bw_kbps < max_points_thd:
            self.throughput_point_value = 100 - (100 * (math.e ** ((-1 * coef) * alloc_bw_kbps)))
        else:
            self.throughput_point_value = 100 - (100 * (math.e ** ((-1 * coef) * max_points_thd)))


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Argument Parser Declarations
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', action='store', default=None, dest='MDL_MASTER', help='Master MDL File', type=str)
    parser.add_argument('-o', action='store', default=None, dest='MDL_OUTPUT', help='Resulting MDL File', type=str)
    parser.add_argument('-s', action='store', default=None, dest='SCHEDULE',
                        help='JSON file that contains the daily Flight Test Schedule', type=str)
    parser.add_argument('-t', action='store', default=None, dest='TIME',
                        help='Time (hhmm, where "hh" is in range 0-23) for schedule lookup.', type=str)
    parser.add_argument('-d', action='count', default=0, dest='DEBUG', help='Set the Debug/Verbosity level')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.0.1')
    cli_args = parser.parse_args()

    # CLI argument assignments
    mdl_file = cli_args.MDL_MASTER
    mdl_output = cli_args.MDL_OUTPUT
    sched_file = cli_args.SCHEDULE
    time = cli_args.TIME
    debug = cli_args.DEBUG

    active_links = []
    l_radio_links = []

    # Load the JSON file containing the schedule and the active links associated with each time in the schedule
    with open(sched_file) as f:
        schedule = json.load(f)

    for t in schedule:
        if t['time'] == int(time):
            sched_links = t['links']
            if debug >= 1:
                print("There are {0} Links Active at {1}:".format(len(sched_links), time))
                for idx, link in enumerate(sched_links, start = 1):
                    print("    Link {0}: {1}".format(idx, link))

    # Parse MDL file, and create the RAN Config (assuming only a single RAN Config)
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(mdl_file, mdl_parser)

    # Parse MDL file for Configuration Version
    root_name = root.find("mdl:Name", namespaces=ns).text
    root_config_ver = root.find("mdl:ConfigurationVersion", namespaces=ns)
    root_config_ver.text = root_config_ver.text + '_' + time


    # Search MDL file for RadioLink elements that are not active, and remove them
    print("Searching for Radio Links.  Removing any RadioLink element that is not active.")
    radio_links_container = root.xpath("//mdl:RadioLinks", namespaces=ns)
    radio_links = root.xpath("//mdl:RadioLink", namespaces=ns)

    for radio_link in radio_links:
        rlname = radio_link.find("mdl:Name", namespaces=ns).text
        rlid = radio_link.attrib['ID']
        rlsrc_idref = radio_link.find("mdl:SourceRadioRef", namespaces=ns).attrib
        tmas = root.xpath("//mdl:TmNSApp[@ID='{}']".format(rlsrc_idref["IDREF"]), namespaces=ns)
        rlsrc = tmas[0].find("mdl:TmNSRadio/mdl:RFMACAddress", namespaces=ns).text
        ran_idref = tmas[0].find("mdl:TmNSRadio/mdl:RANConfigurationRef", namespaces=ns).attrib['IDREF']
        rldst_idref = radio_link.find("mdl:DestinationRadioGroupRef", namespaces=ns).attrib
        rgs = root.xpath("//mdl:RadioGroup[@ID='{}']".format(rldst_idref["IDREF"]), namespaces=ns)
        rldst = rgs[0].find("mdl:GroupRFMACAddress", namespaces=ns).text

        #print("Link {}: {} --> {}".format(rlname, rlsrc, rldst))
        #print("parsed a link from MDL")
        link_is_not_active = True
        for sl in sched_links:
            if (sl['src'] == int(rlsrc)) and (sl['dst'] == int(rldst)):
                new_link = RadioLink(rlname, rlid, rlsrc, rldst)
                l_radio_links.append(new_link)
                link_is_not_active = False

        if link_is_not_active:
            #print("Link {} --> {} is not active.  Removing...".format(rlsrc, rldst))
            radio_links_container[0].remove(radio_link)

    # Search MDL file for RadioGroup elements that are not active, and remove them
    print("Searching for RadioGroups.  Removing any RadioGroup element that is not actived.")
    radio_groups_container = root.xpath("//mdl:RadioGroups", namespaces=ns)
    radio_groups = root.xpath("//mdl:RadioGroup", namespaces=ns)

    for radio_group in radio_groups:
        group_rf_mac_addr = int(radio_group.find("mdl:GroupRFMACAddress", namespaces=ns).text)

        group_is_not_active = True
        for rl in l_radio_links:
            if int(rl.dst) == group_rf_mac_addr:
                group_is_not_active = False
                #print("found an RF Group")

        if group_is_not_active:
            radio_groups_container[0].remove(radio_group)

    # Search MDL file for Radio NetworkNode elements that are not active, and remove them
    print("Searching for Radios.  Removing any NetworkNode that contains an inactive Radio.")

    radios = root.xpath("//mdl:TmNSRadio", namespaces=ns)

    if debug >= 1:
        print("    Number of Radios (NetworkNodes) in the Master MDL File: {}".format(len(radios)))

    for radio in radios:
        roleid = next(radio.iterancestors()).find("mdl:RoleID", namespaces=ns).text
        src_mac = int(radio.find("mdl:RFMACAddress", namespaces=ns).text)
        dst_mac_ref = radio.find("mdl:JoinRadioGroupRefs/mdl:RadioGroupRef", namespaces=ns).attrib
        group = root.xpath("//mdl:RadioGroup[@ID='{}']".format(dst_mac_ref["IDREF"]), namespaces=ns)
        if len(group) > 0:
            dst_group_mac = int(group[0].find("mdl:GroupRFMACAddress", namespaces=ns).text)
        else:
            dst_group_mac = None

        radio_is_not_active = True
        for rl in l_radio_links:
            #print("    rl.src --> rl.dst   |   src_mac --> dst_mac: {} --> {}   |   {} --> {}".format(rl.src, rl.dst, src_mac, dst_group_mac))
            if (int(rl.src) == src_mac) and (dst_group_mac is not None):
                #print("    keep this Network Node.  This Radio is active.")
                radio_is_not_active = False

        if radio_is_not_active:
            if debug >= 2:
                print("    Radio '{}' is not active...Removing radio networknode...".format(roleid))
            tmnsapp = next(radio.iterancestors())
            tmnsapps = next(tmnsapp.iterancestors())
            networknode = next(tmnsapps.iterancestors())
            networknodes = next(networknode.iterancestors())
            networknodes.remove(networknode)

    if debug >= 1:
        radios = root.xpath("//mdl:TmNSRadio", namespaces=ns)
        print("    Number of Active Radios (Links): {}".format(len(radios)))


    # Search MDL file for QoSPolicy elements and remove all RadioLinkRef elements that are not active
    print("Searching QoS Policies.  Removing any RadioLinkRef elements that reference inactive links.")
    qos_policies = root.xpath("//mdl:QoSPolicy", namespaces=ns)
    for qp in qos_policies:
        qos_rlrefs = qp.findall(".//mdl:RadioLinkRef", namespaces=ns)
        for rlref in qos_rlrefs:
            if any(rl for rl in l_radio_links if rl.id==rlref.attrib["IDREF"]):
                if debug >= 2:
                    print("    Found RF Link referenced: {}.".format(rlref.attrib["IDREF"]))
            else:
                if debug >= 2:
                    print("    Did not find RF Link referenced ({})...removing reference from QoS Policy.".
                          format(rlref.attrib["IDREF"]))
                rlref_container = next(rlref.iterancestors())
                rlref_container.remove(rlref)


    # Search MDL file for Link Manager's App References, and remove the references to TMAs of radios that are not active
    print("Searching Link Manager's app references.  Removing any TmNSAppRef elements that reference inactive radios.")
    link_managers = root.xpath("//mdl:TmNSLinkManager", namespaces=ns)
    tmns_apps = root.xpath("//mdl:TmNSApp", namespaces=ns)
    for lm in link_managers:
        tmnsapprefs = lm.findall(".//mdl:TmNSAppRef", namespaces=ns)
        for tmaref in tmnsapprefs:
            ref_is_not_active = True
            for tma in tmns_apps:
                if tma.attrib["ID"] == tmaref.attrib["IDREF"]:
                    ref_is_not_active = False

            if ref_is_not_active:
                tmaref_container = next(tmaref.iterancestors())
                tmaref_container.remove(tmaref)


    # Write trimmed MDL file to output file.
    output = etree.tostring(root, pretty_print=True)

    if mdl_output is None:
        temp, ext = os.path.splitext(mdl_file)
        mdl_output = temp + '_' + time + '.mdl'
    if mdl_output is not None:
        with open(mdl_output, 'wb') as f:
            f.write(output)

    if debug >= 5:
        print("vvvvvvvvvvvvvvv ----- MDL OUTPUT FILE ----- vvvvvvvvvvvvvvv")
        print(" ")
        print(output)
        print(" ")
        print("^^^^^^^^^^^^^^^ ----- MDL OUTPUT FILE ----- ^^^^^^^^^^^^^^^")

    print("Done.  The trimmed MDL File can be found at: {}".format(mdl_output))
