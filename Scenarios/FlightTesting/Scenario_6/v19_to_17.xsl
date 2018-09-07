<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tmats="https://wsmrc2vger.wsmr.army.mil/rcc/manuals/106-11" xmlns:mdl="http://inetprogram.org/projects/MDL" xmlns:tmatsP="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsP" xmlns:tmatsD="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsD" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:tmatsCommon="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsCommon" exclude-result-prefixes="tmats tmatsCommon tmatsP tmatsD" version="1.0">
    <!--Identity transform and MDL target version-->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:param name="targetMDLVersion" select="'http://inetprogram.org/projects/MDL MDL_v0_8_17.xsd'"/>
    <xsl:template match="mdl:MDLRoot/@xsi:schemaLocation">
        <xsl:attribute name="xsi:schemaLocation">
            <xsl:value-of select="$targetMDLVersion"/>
        </xsl:attribute>
    </xsl:template>
    <!--Remove processing instructions-->
    <xsl:template match="//processing-instruction()"/>
    <!--Remove ProperName field-->
    <xsl:template match="mdl:Measurement/mdl:ProperName"/>
    <!--Convert Model to ModelNumber and SerialIdentifier to SerialNumber-->
    <xsl:template match="mdl:Module/mdl:Model">
        <mdl:ModelNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:ModelNumber>
    </xsl:template>s
    <xsl:template match="mdl:Module/mdl:SerialIdentifier">
        <mdl:SerialNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:SerialNumber>
    </xsl:template>
    <xsl:template match="mdl:SubModule/mdl:Model">
        <mdl:ModelNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:ModelNumber>
    </xsl:template>
    <xsl:template match="mdl:SubModule/mdl:SerialIdentifier">
        <mdl:SerialNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:SerialNumber>
    </xsl:template>
    <xsl:template match="mdl:Antenna/mdl:Model">
        <mdl:ModelNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:ModelNumber>
    </xsl:template>
    <xsl:template match="mdl:Antenna/mdl:SerialIdentifier">
        <mdl:SerialNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:SerialNumber>
    </xsl:template>
    <xsl:template match="mdl:Device/mdl:Model">
        <mdl:ModelNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:ModelNumber>
    </xsl:template>
    <xsl:template match="mdl:Device/mdl:SerialIdentifier">
        <mdl:SerialNumber>
            <xsl:apply-templates select="@*|node()"/>
        </mdl:SerialNumber>
    </xsl:template>
    <!--Add LinkControlMode to RadioLink-->
    <xsl:template match="mdl:RadioLink">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates select="mdl:AutomaticPowerControlEnable/preceding-sibling::*"/>
            <mdl:LinkControlMode>true</mdl:LinkControlMode>
            <xsl:apply-templates select="mdl:AutomaticPowerControlEnable|mdl:AutomaticPowerControlEnable/following-sibling::*"/>
        </xsl:copy>
    </xsl:template>
    <!--Convert 'Extension' to 'Other' in enum types that have an other value-->
    <xsl:template match="mdl:DeviceType/text()[.='Extension']">Other</xsl:template>
    <xsl:template match="mdl:DataOperationType/text()[.='Extension']">Other</xsl:template>
    <!--Network Node refactoring-->
    <!--All NetworkInterfaces are removed from modules and put in the parent NetworkNode-->
    <!--(since we have no way to tell what belongs in the NetworkNode and what belongs in the modules)-->
    <xsl:template match="mdl:Network/mdl:NetworkNode">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates select="mdl:TmNSManageableApps/preceding-sibling::*|mdl:TmNSManageableApps"/>
            <!-- if the node is a DAU, take only select items from the modules -->
            <xsl:if test="mdl:TmNSManageableApps/mdl:TmNSManageableApp/mdl:TmNSDAU">
                <xsl:call-template name="dau-merge-info"/>
            </xsl:if>
            <!-- otherwise, take everything from the modules (since non DAUs don't have modules) -->
            <xsl:if test="not(mdl:TmNSManageableApps/mdl:TmNSManageableApp/mdl:TmNSDAU)">
                <xsl:call-template name="absorb-modules"/>
            </xsl:if>
        </xsl:copy>
    </xsl:template>
    <xsl:template name="dau-merge-info">
        <!-- take all the network interfaces -->
        <xsl:apply-templates select="mdl:InternalStructure/mdl:Module/mdl:NetworkInterface"/>
        <!-- take the routes if they exist, as v0_8_17 modules don't have routes -->
        <xsl:if test="mdl:InternalStructure/mdl:Module/mdl:Routes">
            <mdl:Routes>
                <xsl:apply-templates select="mdl:InternalStructure/mdl:Module/mdl:Routes/*"/>
            </mdl:Routes>
        </xsl:if>
        <!-- make a fake port, because we don't know which port, if any, was originally the NetworkNode -->
        <mdl:Ports>
            <mdl:Port Index="1">
                <xsl:attribute name="ID">generated-port-<xsl:value-of select="generate-id()"/>
                </xsl:attribute>
                <mdl:Name>Generated Port</mdl:Name>
                <mdl:Description>Generated port to avoid taking valid ports from modules</mdl:Description>
                <mdl:PortDirection>Unspecified</mdl:PortDirection>
            </mdl:Port>
        </mdl:Ports>
    </xsl:template>
    <xsl:template name="absorb-modules">
        <xsl:apply-templates select="mdl:InternalStructure/mdl:Module/mdl:NetworkInterface"/>
        <xsl:if test="mdl:InternalStructure/mdl:Module/mdl:Routes">
            <mdl:Routes>
                <xsl:apply-templates select="mdl:InternalStructure/mdl:Module/mdl:Routes/*"/>
            </mdl:Routes>
        </xsl:if>
        <xsl:apply-templates select="mdl:InternalStructure/mdl:Module/mdl:Connector"/>
        <mdl:Ports>
            <xsl:call-template name="port-merge"/>
        </mdl:Ports>
    </xsl:template>
    <xsl:template match="mdl:TmNSManageableApp/mdl:TmNSDAU">
        <xsl:copy>
            <xsl:apply-templates select="mdl:ReadOnly"/>
            <xsl:apply-templates select="mdl:Owner"/>
            <xsl:apply-templates select="mdl:Calibration"/>
            <xsl:apply-templates select="ancestor::mdl:NetworkNode/mdl:InternalStructure/mdl:Module"/>
        </xsl:copy>
    </xsl:template>
    <!--Discard all elements not present in v0_8_17 and elements included in the NetworkNode-->
    <xsl:template match="mdl:Module">
        <xsl:copy>
            <xsl:apply-templates select="mdl:PositionsOccupied/preceding-sibling::*"/>
            <xsl:apply-templates select="mdl:Connector|mdl:Ports|mdl:SubModule"/>
        </xsl:copy>
    </xsl:template>
    <!--Port indexes must be merged-->
    <xsl:template name="port-merge">
        <xsl:for-each select="mdl:InternalStructure/mdl:Module/mdl:Ports/*">
            <xsl:copy>
                <xsl:attribute name="Index">
                    <xsl:value-of select="position()"/>
                </xsl:attribute>
                <xsl:apply-templates select="@*[name()!='Index']|node()"/>
            </xsl:copy>
        </xsl:for-each>
    </xsl:template>
    <!--Device refactoring-->
    <xsl:template match="mdl:Network/mdl:Device">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <!-- the last two elements are appended because DeviceType is the last guaranteed element, but they can come after -->
            <xsl:apply-templates select="mdl:DeviceType/preceding-sibling::*|mdl:DeviceType|mdl:LogicalLocation|mdl:PhysicalLocation"/>
            <xsl:apply-templates select="mdl:DeviceStructure/mdl:DeviceModule"/>
            <mdl:Ports>
                <xsl:call-template name="device-port-merge"/>
            </mdl:Ports>
        </xsl:copy>
    </xsl:template>
    <!--Device Port indexes must be merged too-->
    <xsl:template name="device-port-merge">
        <xsl:for-each select="mdl:DeviceStructure/mdl:DeviceModule/mdl:Ports/*">
            <xsl:copy>
                <xsl:attribute name="Index">
                    <xsl:value-of select="position()"/>
                </xsl:attribute>
                <xsl:apply-templates select="@*[name()!='Index']|node()"/>
            </xsl:copy>
        </xsl:for-each>
    </xsl:template>
    <!--DeviceModule element is stripped to go back in a Device-->
    <xsl:template match="mdl:DeviceStructure/mdl:DeviceModule">
        <xsl:apply-templates select="mdl:DataOperationRef|mdl:Sensitivity|mdl:Excitation|mdl:Calibration|mdl:Connector"/>
    </xsl:template>
    <!--Move NameValue elements out of NameValues containers-->
    <xsl:template match="mdl:VendorConfig|mdl:GenericParameter">
        <xsl:copy>
            <xsl:apply-templates select="mdl:ReadOnly|mdl:Owner"/>
            <xsl:apply-templates select="mdl:NameValues/mdl:NameValue"/>
        </xsl:copy>
    </xsl:template>
    <!--Remove ConditionParameter container from Sensitivity and Excitation elements-->
    <xsl:template match="mdl:DeviceModule/mdl:Sensitivity|mdl:DeviceModule/mdl:Excitation">
        <xsl:copy>
            <xsl:apply-templates select="mdl:ConditionParameter/*"/>
        </xsl:copy>
    </xsl:template>
    <!--Remove all extension attributes (only present on extensible enums)-->
    <xsl:template match="@extension"/>
    <!--Replace invalid values from MeasurementTypeEnum-->
    <xsl:template match="mdl:MeasurementType/text()[.='Time']">Analog</xsl:template>
    <xsl:template match="mdl:MeasurementType/text()[.='Video']">Analog</xsl:template>
    <xsl:template match="mdl:MeasurementType/text()[.='Overhead']">Analog</xsl:template>
    <xsl:template match="mdl:MeasurementType/text()[.='Extension']">Analog</xsl:template>
    <!--Replace invalid values from DigitalEncodingEnum-->
    <xsl:template match="mdl:DigitalEncoding/text()[.='MILSTD1750ASinglePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='MILSTD1750ADoublePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='DECSinglePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='DECDoublePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='DECGDoublePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='IBMSinglePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='IBMDoublePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='TISinglePrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='TIExtendedPrecision']">BCD</xsl:template>
    <xsl:template match="mdl:DigitalEncoding/text()[.='Extension']">BCD</xsl:template>
    <!--Remove elements that don't exist in v0_8_17-->
    <xsl:template match="mdl:TestMission/mdl:HandoffRules"/>
    <xsl:template match="mdl:Measurement/mdl:MeasurementTimeRef"/>
    <xsl:template match="mdl:DataAttributes/mdl:TimeAttributes"/>
    <xsl:template match="mdl:DataWordToFieldMap/mdl:TimeOffset"/>
    <xsl:template match="mdl:DataWordToFieldMap/mdl:TimeOffsetIncrement"/>
    <xsl:template match="mdl:SubModule/mdl:Children"/>
    <xsl:template match="mdl:SubModule/@ID"/>
    <xsl:template match="mdl:Port/mdl:PortType"/>
    <xsl:template match="mdl:Port/mdl:AnalogAttributes"/>
    <xsl:template match="mdl:Port/mdl:Excitation"/>
    <xsl:template match="mdl:Port/@Enabled"/>
    <!-- Tmats Schema Changes -->
    <!-- Remove Tmats Version Attribute -->
    <xsl:template match="@tmatsCommon:TmatsVersion"/>
    <!--Remove Tmats P group namespace-->
    <xsl:template match="tmatsP:*">
        <xsl:element name="tmats:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <!--Remove Tmats D group namespace-->
    <xsl:template match="tmatsD:*">
        <xsl:element name="tmats:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <!--Convert FragmentTransferOrder to element-->
    <xsl:template match="tmatsD:MeasurementFragments">
        <tmats:MeasurementFragments>
            <xsl:attribute name="FragmentTransferOrder">
                <xsl:value-of select="tmatsD:FragmentTransferOrder"/>
            </xsl:attribute>
            <xsl:apply-templates select="tmatsD:FragmentTransferOrder/following-sibling::*"/>
        </tmats:MeasurementFragments>
    </xsl:template>
</xsl:stylesheet>