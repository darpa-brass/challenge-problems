import argparse
from lxml import etree

ns = {"xsd": "http://www.w3.org/2001/XMLSchema",
      "mdl": "http://www.wsmr.army.mil/RCC/schemas/MDL",
      "tmatsP": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup",
      "tmatsD": "http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"}

# shortcut dictionary for passing common arguments
n = {"namespaces": ns}


def make_radio(identifier):
    return etree.fromstring(
    f"""
<NetworkNode ID="Node_{identifier}" xmlns='http://www.wsmr.army.mil/RCC/schemas/MDL'>
    <Name>{identifier}</Name>
    <Description>Radio {identifier}</Description>
    <InventoryID>GR3a</InventoryID>
    <HostName/>
    <Manufacturer/>
    <Model/>
    <ModelVersion/>
    <IEEE1588Version>2008e2e</IEEE1588Version>
    <Routes>
        <Route>
            <Destination>10.1.1.0</Destination>
            <Netmask>255.255.255.0</Netmask>
            <RadioLinkRef IDREF="fix"/>
        </Route>
    </Routes>
    <TmNSApps>
        <TmNSApp ID="TMA_{identifier}">
            <Name>New TmNS Application 1</Name>
            <RoleID>{identifier}</RoleID>
            <LoggingLevel>Error</LoggingLevel>
            <Manufacturer/>
            <Product/>
            <ProductVersion/>
            <ConfigurationVersion/>
            <TmNSManagementResourcesVersion/>
            <DirtyBit>false</DirtyBit>
            <TmNSNetworkFabricDevice>
                <MulticastRoutingMode>Dynamic</MulticastRoutingMode>
                <IGMPQuerier>Auto</IGMPQuerier>
                <IGMPQuerierInterval>30</IGMPQuerierInterval>
            </TmNSNetworkFabricDevice>
            <TmNSRadio>
                <RANConfigurationRef IDREF="RANConfig15_RAN_4919"/>
                <RFMACAddress>fix</RFMACAddress>
                <JoinRadioGroupRefs>
                    <RadioGroupRef IDREF="fix"/>
                </JoinRadioGroupRefs>
                <FragmentationPersistencePeriodUSec>0</FragmentationPersistencePeriodUSec>
                <TxPowerLeveldBm>43</TxPowerLeveldBm>
                <LowPowerModeEnable>false</LowPowerModeEnable>
                <LinkAgent>
                    <NetworkInterfaceRef IDREF="NetworkInterface_{identifier}"/>
                    <ListeningPort>12345</ListeningPort>
                </LinkAgent>
            </TmNSRadio>
            <SMInterface>
                <SNMPSetup>
                    <SNMPVersions>
                        <SNMPVersion>v3</SNMPVersion>
                    </SNMPVersions>
                    <SNMPPort>161</SNMPPort>
                    <NotificationPort>162</NotificationPort>
                    <DSCPTableEntryRef IDREF="DSCP_BestEffort_000000"/>
                    <NetworkInterfaceRefs>
                        <NetworkInterfaceRef IDREF="NetworkInterface_{identifier}"/>
                    </NetworkInterfaceRefs>
                </SNMPSetup>
            </SMInterface>
        </TmNSApp>
    </TmNSApps>
    <InternalStructure>
        <Modules>
            <Module ID="NodeModule_{identifier}">
                <Name>NodeModule 1</Name>
                <Manufacturer/>
                <Model/>
                <Position>1</Position>
                <PositionsOccupied>1</PositionsOccupied>
                <NetworkInterfaces>
                    <NetworkInterface ID="NetworkInterface_{identifier}">
                        <Name>eth1</Name>
                        <DHCPEnable>false</DHCPEnable>
                        <IPAddress>fix</IPAddress>
                        <Netmask>255.255.255.0</Netmask>
                        <PhysicalNetworkPorts>
                            <PhysicalNetworkPort ID="{identifier}_net">
                                <Name>NetworkPort 1</Name>
                                <Medium>Copper</Medium>
                                <PortNumber>1</PortNumber>
                                <PortDataRate>
                                    <Value>1000000000</Value>
                                    <BaseUnit>BitPerSecond</BaseUnit>
                                </PortDataRate>
                            </PhysicalNetworkPort>
                        </PhysicalNetworkPorts>
                    </NetworkInterface>
                </NetworkInterfaces>
                <Ports>
                    <Port ID="NetworkPort_{identifier}" Index="1" Enabled="false">
                        <Name>NetworkPort 1</Name>
                        <PortDirection>Bidirectional</PortDirection>
                        <PhysicalNetworkPortRef IDREF="{identifier}_net"/>
                    </Port>
                </Ports>
            </Module>
        </Modules>
    </InternalStructure>
</NetworkNode>
    """)


def make_link(source_radio, source_mac, destination_mac):
    return etree.fromstring(
    f"""
<RadioLink ID="RadioLink_{source_mac}_to_{destination_mac}" xmlns='http://www.wsmr.army.mil/RCC/schemas/MDL'>
    <Name>{source_mac} to {destination_mac}</Name>
    <SourceRadioRef IDREF="TMA_{source_radio}"/>
    <DestinationRadioGroupRef IDREF="RadioGroup_RAN_4919_{destination_mac}"/>
    <TxRxEnable>true</TxRxEnable>
    <HeartbeatTimeout>65535</HeartbeatTimeout>
    <LinkManagerHeartbeatTimeout>2000</LinkManagerHeartbeatTimeout>
    <LinkManagerTxOpTimeout>150</LinkManagerTxOpTimeout>
    <EncryptionEnabled>false</EncryptionEnabled>
    <EncryptionKeyID>0</EncryptionKeyID>
</RadioLink>
    """)


def make_group(destination_mac):
    return etree.fromstring(
    f"""
<RadioGroup ID="RadioGroup_RAN_4919_{destination_mac}" xmlns='http://www.wsmr.army.mil/RCC/schemas/MDL'>
    <Name>{destination_mac} Receive Group</Name>
    <GroupRFMACAddress>{destination_mac}</GroupRFMACAddress>
</RadioGroup>
    """)


def make_ran(frequency):
    return etree.fromstring(
    f"""
<RANConfiguration ID="RANConfig15_RAN_{frequency}">
    <Name>RAN_{frequency}</Name>
    <LinkAgentConnectionEncryptionEnabled>false</LinkAgentConnectionEncryptionEnabled>
    <TSSTunnelEncryptionEnabled>false</TSSTunnelEncryptionEnabled>
    <CenterFrequencyHz>{frequency}500000</CenterFrequencyHz>
    <ModulationType>SOQPSK-TG</ModulationType>
    <EpochSize>100</EpochSize>
    <LDPCBlocksPerBurst>1</LDPCBlocksPerBurst>
    <MaxGuardTimeSec>0.001</MaxGuardTimeSec>
    <RadioControlLoopDSCPRef IDREF="DSCP_NetworkControl_111000"/>
    <RANCommandControlDSCPRef IDREF="DSCP_NetworkControl_111000"/>
    <RadioGroups/>
</RANConfiguration>
    """)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('count', type=int, help="Number of TAs to generate. (1-255)")
    parser.add_argument("--add_rans", type=int, default=0, help="Number of additional RANs to generate. (0-10)")
    parser.add_argument("--base", default="base.xml", help="Base XML location.")
    parser.add_argument("--output", default="output.xml", help="Output XML location.")
    cli_args = parser.parse_args()

    if cli_args.count > 255 or cli_args.count < 1:
        print("TA Count must be in range 1-255.")
        return(-1)

    if cli_args.add_rans > 10 or cli_args.add_rans < 0:
        print("Additional RAN count must be in range 0-10.")
        return(-1)

    # initialize MDL file
    mdl_parser = etree.XMLParser(remove_blank_text=True)
    base_mdl = etree.parse(cli_args.base, mdl_parser)

    base_mdl.find("mdl:ConfigurationVersion", **n).text = f"{cli_args.count} TAs"

    network_nodes = base_mdl.find("//mdl:NetworkNodes", **n)
    radio_groups = base_mdl.find("//mdl:RadioGroups", **n)
    radio_links = base_mdl.find("//mdl:RadioLinks", **n)
    uplink_qos_refs = base_mdl.find("//mdl:QoSPolicy[@ID='QoS3_ClassicDownlink']//mdl:RadioLinkRefs", **n)
    downlink_qos_refs = base_mdl.find("//mdl:QoSPolicy[@ID='QoS4_SimpleUplink']//mdl:RadioLinkRefs", **n)
    rans = base_mdl.find("//mdl:RANConfigurations", **n)

    for i in range(cli_args.count):
        ground_mac = 0x1000 + i        
        ta_mac = 0x2000 + i
        uplink_mac = 0xF000 + i
        downlink_mac = 0xF100 + i

        # add ground radio
        ground = make_radio(f"ground_{i}")
        uplink_ref = ground.find(".//mdl:RadioLinkRef", **n)
        uplink_ref.set("IDREF", f"RadioLink_{ground_mac}_to_{uplink_mac}")
        ground_rf_mac = ground.find(".//mdl:RFMACAddress", **n)
        ground_rf_mac.text = str(ground_mac)
        downlink_group_ref = ground.find(".//mdl:RadioGroupRef", **n)
        downlink_group_ref.set("IDREF", f"RadioGroup_RAN_4919_{downlink_mac}")
        ground_ip = ground.find(".//mdl:IPAddress", **n)
        ground_ip.text = f"10.1.201.{i}"

        network_nodes.append(ground)

        # add TA radio
        ta = make_radio(f"ta_{i}")
        downlink_ref = ta.find(".//mdl:RadioLinkRef", **n)
        downlink_ref.set("IDREF", f"RadioLink_{ta_mac}_to_{downlink_mac}")
        ta_rf_mac = ta.find(".//mdl:RFMACAddress", **n)
        ta_rf_mac.text = str(ta_mac)
        uplink_group_ref = ta.find(".//mdl:RadioGroupRef", **n)
        uplink_group_ref.set("IDREF", f"RadioGroup_RAN_4919_{uplink_mac}")
        ta_ip = ta.find(".//mdl:IPAddress", **n)
        ta_ip.text = f"10.1.1.{i}"

        network_nodes.append(ta)

        # add uplink and uplink group
        uplink = make_link(f"ground_{i}", ground_mac, uplink_mac)
        radio_links.append(uplink)
        uplink_group = make_group(uplink_mac)
        radio_groups.append(uplink_group)
        uplink_qos_ref = etree.fromstring(f"<RadioLinkRef xmlns='http://www.wsmr.army.mil/RCC/schemas/MDL'/>")
        uplink_qos_ref.set("IDREF", uplink.get("ID"))
        uplink_qos_refs.append(uplink_qos_ref)

        # add downlink and downlink group
        downlink = make_link(f"ta_{i}", ta_mac, downlink_mac)
        radio_links.append(downlink)
        downlink_group = make_group(downlink_mac)
        radio_groups.append(downlink_group)
        downlink_qos_ref = etree.fromstring(f"<RadioLinkRef xmlns='http://www.wsmr.army.mil/RCC/schemas/MDL'/>")
        downlink_qos_ref.set("IDREF", downlink.get("ID"))
        downlink_qos_refs.append(downlink_qos_ref)

    if cli_args.add_rans > 0:
        frequency = 4919 + 22

        for i in range(cli_args.add_rans):
            ran = make_ran(frequency)
            rans.append(ran)
            frequency += 22

    with open(cli_args.output, "w") as f:
        f.write(etree.tounicode(base_mdl, pretty_print=True))


if __name__ == "__main__":
    main()