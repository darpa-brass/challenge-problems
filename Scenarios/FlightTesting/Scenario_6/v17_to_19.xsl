<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tmats="https://wsmrc2vger.wsmr.army.mil/rcc/manuals/106-11" xmlns:mdl="http://inetprogram.org/projects/MDL" xmlns:tmatsP="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsP" xmlns:tmatsD="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsD" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:tmatsCommon="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsCommon" exclude-result-prefixes="tmats tmatsCommon tmatsP tmatsD" version="1.0">
    <!--Identity transform and MDL target version-->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:param name="targetMDLVersion" select="'http://inetprogram.org/projects/MDL MDL_v0_8_19.xsd'"/>
    <xsl:template match="mdl:MDLRoot/@xsi:schemaLocation">
        <xsl:attribute name="xsi:schemaLocation">
            <xsl:value-of select="$targetMDLVersion"/>
        </xsl:attribute>
    </xsl:template>
    <!--Remove processing instructions-->
    <xsl:template match="//processing-instruction()"/>
    <!--Add ProperName field-->
    <xsl:param name="properName" select="'None'"/>
    <xsl:template match="mdl:Measurement/mdl:MeasurementActive">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
        <!-- have to keep the prefixed namespace, even though they're the same -->
        <!-- <xsl:element name="ProperName" namespace="http://inetprogram.org/projects/MDL">
            <xsl:value-of select="$properName"/>
        </xsl:element> -->
        <mdl:ProperName>
            <xsl:value-of select="$properName"/>
        </mdl:ProperName>
    </xsl:template>
    <!--Convert ModelNumber to Model and SerialNumber to SerialIdentifier-->
    <xsl:template match="mdl:Module/mdl:ModelNumber">
        <xsl:element name="Model" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:Module/mdl:SerialNumber">
        <xsl:element name="SerialIdentifier" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:SubModule/mdl:ModelNumber">
        <xsl:element name="Model" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:SubModule/mdl:SerialNumber">
        <xsl:element name="SerialIdentifier" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:Antenna/mdl:ModelNumber">
        <xsl:element name="Model" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:Antenna/mdl:SerialNumber">
        <xsl:element name="SerialIdentifier" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:Device/mdl:ModelNumber">
        <xsl:element name="Model" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="mdl:Device/mdl:SerialNumber">
        <xsl:element name="SerialIdentifier" namespace="http://inetprogram.org/projects/MDL">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <!--Remove obsolete LinkControlMode from RadioLink-->
    <xsl:template match="mdl:RadioLink/mdl:LinkControlMode"/>
    <!--Convert 'Other' to 'Extension' in enum types-->
    <xsl:template match="mdl:DeviceType[text()='Other']">
        <xsl:copy>
            <xsl:attribute name="extension">Extension</xsl:attribute>Extension</xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataOperationType[text()='Other']">
        <xsl:copy>
            <xsl:attribute name="extension">Extension</xsl:attribute>Extension</xsl:copy>
    </xsl:template>
    <!--Convert Hex to Decimal-->
    <xsl:template name="hex2num">
        <xsl:param name="hex"/>
        <xsl:param name="num" select="0"/>
        <xsl:param name="MSB" select="translate(substring($hex, 1, 1), 'abcdef', 'ABCDEF')"/>
        <xsl:param name="value" select="string-length(substring-before('0123456789ABCDEF', $MSB))"/>
        <xsl:param name="result" select="16 * $num + $value"/>
        <xsl:choose>
            <xsl:when test="string-length($hex) &gt; 1">
                <xsl:call-template name="hex2num">
                    <xsl:with-param name="hex" select="substring($hex, 2)"/>
                    <xsl:with-param name="num" select="$result"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$result"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--Convert Byte to Bit-->
    <xsl:template match="mdl:MinimumCapacity[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MinimumCapacity[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CapacityAllocation[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CapacityAllocation[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AveragePacketDelay[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AveragePacketDelay[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Jitter[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Jitter[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Limit[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Limit[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Min[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Min[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Max[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Max[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Avpkt[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Avpkt[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Bandwidth[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Bandwidth[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Perturb[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Perturb[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Quantum[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Quantum[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Burst[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Burst[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MPU[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MPU[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Rate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Rate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Peakrate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Peakrate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MTU[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MTU[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Ceiling[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Ceiling[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CBurst[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CBurst[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:UnitsNumerator[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:UnitsNumerator[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:UnitsDenominator[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:UnitsDenominator[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataAttributes[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataAttributes[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AggregateRate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AggregateRate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataWordWidth[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataWordWidth[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SyllableWidth[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SyllableWidth[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FieldWidth[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FieldWidth[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FieldOffsetIncrement[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FieldOffsetIncrement[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OffsetValue[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OffsetValue[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:PackageLengthFieldDescription[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:PackageLengthFieldDescription[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FixedPackageLength[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FixedPackageLength[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MaximumMessageLength[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MaximumMessageLength[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FixedMessageLength[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:FixedMessageLength[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MaximumMessageLatency[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MaximumMessageLatency[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MessageRate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:MessageRate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Size[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Size[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:InputUnits[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:InputUnits[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OutputUnits[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OutputUnits[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataBufferLength[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DataBufferLength[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Azimuth[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Azimuth[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Elevation[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Elevation[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CenterFrequency[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:CenterFrequency[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Deviation[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Deviation[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ClockRate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ClockRate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ManualGain[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ManualGain[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AGCTimeConstant[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:AGCTimeConstant[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SweepRangeLow[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SweepRangeLow[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SweepRangeHigh[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:SweepRangeHigh[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:BitRate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:BitRate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DeviceStatusMonitoringPeriod[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DeviceStatusMonitoringPeriod[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DeviceAutoDiscoveryPeriod[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:DeviceAutoDiscoveryPeriod[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:PortDataRate[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:PortDataRate[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Sensitivity[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Sensitivity[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Excitation[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:Excitation[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:InputValue[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:InputValue[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OutputValue[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:OutputValue[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ConditionParameter[mdl:SIUnits='Byte']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">Bit</xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:ConditionParameter[mdl:SIUnits='BytePerSecond']">
        <xsl:copy>
            <xsl:apply-templates select="mdl:SIUnits/preceding-sibling::*[position() &gt; 1]"/>
            <xsl:variable name="element" select="name(mdl:SIUnits/preceding-sibling::*[position() = 1])"/>
            <xsl:variable name="decimal">
                <xsl:if test="starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x')">
                    <xsl:call-template name="hex2num">
                        <xsl:with-param name="hex" select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                    </xsl:call-template>
                </xsl:if>
                <xsl:if test="not(starts-with(mdl:SIUnits/preceding-sibling::*[position() = 1], '0x'))">
                    <xsl:value-of select="mdl:SIUnits/preceding-sibling::*[position() = 1]"/>
                </xsl:if>
            </xsl:variable>
            <xsl:element name="{$element}" namespace="http://inetprogram.org/projects/MDL">
                <xsl:value-of select="$decimal * 8"/>
            </xsl:element>
            <xsl:element name="SIUnits" namespace="http://inetprogram.org/projects/MDL">BitPerSecond</xsl:element>
        </xsl:copy>
    </xsl:template>
    <!--Network Node refactoring-->
    <xsl:template match="mdl:Network/mdl:NetworkNode">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates select="mdl:TmNSManageableApps/preceding-sibling::*|mdl:TmNSManageableApps"/>
            <xsl:element name="InternalStructure" namespace="http://inetprogram.org/projects/MDL">
                <xsl:if test="mdl:TmNSManageableApps/mdl:TmNSManageableApp/mdl:TmNSDAU/mdl:Module">
                    <xsl:apply-templates select="mdl:TmNSManageableApps/mdl:TmNSManageableApp/mdl:TmNSDAU/mdl:Module"/>
                </xsl:if>
                <xsl:if test="not(mdl:TmNSManageableApps/mdl:TmNSManageableApp/mdl:TmNSDAU/mdl:Module)">
                    <xsl:call-template name="fake-module"/>
                </xsl:if>
            </xsl:element>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:TmNSManageableApp/mdl:TmNSDAU">
        <xsl:copy>
            <xsl:apply-templates select="mdl:ReadOnly"/>
            <xsl:apply-templates select="mdl:Owner"/>
            <xsl:apply-templates select="mdl:Calibration"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:TmNSDAU/mdl:Module[position() = 1]">
        <xsl:copy>
            <xsl:call-template name="dau-module-start"/>
            <!-- include the network interface and port from the parent network node -->
            <xsl:apply-templates select="ancestor::mdl:NetworkNode/mdl:NetworkInterface"/>
            <xsl:apply-templates select="mdl:NetworkInterface"/>
            <!-- merge network node with module -->
            <xsl:if test="mdl:Routes | ancestor::mdl:NetworkNode/mdl:Routes">
                <xsl:element name="Routes" namespace="http://inetprogram.org/projects/MDL">
                    <xsl:apply-templates select="mdl:Routes/*"/>
                    <xsl:apply-templates select="ancestor::mdl:NetworkNode/mdl:Routes/*"/>
                </xsl:element>
            </xsl:if>
            <xsl:if test="mdl:Connector | ancestor::mdl:NetworkNode/mdl:Connector">
                <xsl:element name="Connector" namespace="http://inetprogram.org/projects/MDL">
                    <xsl:apply-templates select="mdl:Connector/*"/>
                    <xsl:apply-templates select="ancestor::mdl:NetworkNode/mdl:Connector/*"/>
                </xsl:element>
            </xsl:if>
            <!-- ports is required, even if empty -->
            <xsl:element name="Ports" namespace="http://inetprogram.org/projects/MDL">
                <xsl:apply-templates select="mdl:Ports/*"/>
                <xsl:call-template name="port-merge"/>
            </xsl:element>
            <xsl:apply-templates select="mdl:SubModule"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="mdl:TmNSDAU/mdl:Module[position() &gt; 1]">
        <xsl:copy>
            <xsl:call-template name="dau-module-start"/>
            <xsl:apply-templates select="mdl:Position/following-sibling::*"/>
        </xsl:copy>
    </xsl:template>
    <!--Submodules need ids-->
    <xsl:template match="mdl:SubModule">
        <xsl:copy>
            <xsl:attribute name="ID">
                <xsl:value-of select="generate-id()"/>
            </xsl:attribute>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <!--Port indexes must be merged-->
    <xsl:template name="port-merge">
        <xsl:variable name="offset" select="count(mdl:Ports/*)"/>
        <xsl:for-each select="ancestor::mdl:NetworkNode/mdl:Ports/*">
            <xsl:copy>
                <xsl:attribute name="Index">
                    <xsl:value-of select="@Index+$offset"/>
                </xsl:attribute>
                <xsl:apply-templates select="@*[name()!='Index']|node()"/>
            </xsl:copy>
        </xsl:for-each>
    </xsl:template>
    <xsl:template name="dau-module-start">
        <!-- change this if you want to specify Module IDs -->
        <xsl:attribute name="ID">
            <xsl:value-of select="generate-id()"/>
        </xsl:attribute>
        <xsl:apply-templates select="mdl:Position/preceding-sibling::*|mdl:Position"/>
        <!-- change this if you want to specify positions occupied -->
        <xsl:element name="PositionsOccupied" namespace="http://inetprogram.org/projects/MDL">1</xsl:element>
        <!-- link by default with the app it was a child of -->
        <xsl:element name="RunningApps" namespace="http://inetprogram.org/projects/MDL">
            <xsl:element name="ManageableAppRef" namespace="http://inetprogram.org/projects/MDL">
                <xsl:attribute name="IDREF">
                    <xsl:value-of select="ancestor::mdl:TmNSManageableApp/@ID"/>
                </xsl:attribute>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    <xsl:template name="fake-module">
        <mdl:Module>
            <xsl:attribute name="ID">
                <xsl:value-of select="generate-id()"/>
            </xsl:attribute>
            <mdl:Name>Generated Module</mdl:Name>
            <mdl:Description>Generated Module</mdl:Description>
            <mdl:Manufacturer>n/a</mdl:Manufacturer>
            <mdl:Model>n/a</mdl:Model>
            <mdl:SerialIdentifier>n/a</mdl:SerialIdentifier>
            <mdl:InventoryID>n/a</mdl:InventoryID>
            <mdl:Position>1</mdl:Position>
            <mdl:PositionsOccupied>1</mdl:PositionsOccupied>
            <!-- add an app reference for each TMA in the parent node -->
            <mdl:RunningApps>
                <xsl:for-each select="mdl:TmNSManageableApps/mdl:TmNSManageableApp">
                    <mdl:ManageableAppRef>
                        <xsl:attribute name="IDREF">
                            <xsl:value-of select="@ID"/>
                        </xsl:attribute>
                    </mdl:ManageableAppRef>
                </xsl:for-each>
            </mdl:RunningApps>
            <xsl:apply-templates select="mdl:NetworkInterface|mdl:Routes|mdl:Connector"/>
            <!-- ports is required, even if empty -->
            <mdl:Ports>
                <xsl:apply-templates select="mdl:Ports/*"/>
            </mdl:Ports>
        </mdl:Module>
    </xsl:template>
    <!--Device refactoring-->
    <xsl:template match="mdl:Network/mdl:Device">
        <xsl:copy>
            <xsl:apply-templates select="@*"/>
            <!-- the last two elements are appended because DeviceType is the last guaranteed element, but they can come after -->
            <xsl:apply-templates select="mdl:DeviceType/preceding-sibling::*|mdl:DeviceType|mdl:LogicalLocation|mdl:PhysicalLocation"/>
            <mdl:DeviceStructure>
                <xsl:call-template name="fake-device-module"/>
            </mdl:DeviceStructure>
        </xsl:copy>
    </xsl:template>
    <!--The generated device module template is used every time because device modules did not exist in v0_8_17-->
    <xsl:template name="fake-device-module">
        <mdl:DeviceModule>
            <xsl:attribute name="ID">
                <xsl:value-of select="generate-id()"/>
            </xsl:attribute>
            <mdl:Name>Generated Module</mdl:Name>
            <mdl:Description>Generated Module</mdl:Description>
            <mdl:Manufacturer>n/a</mdl:Manufacturer>
            <mdl:Model>n/a</mdl:Model>
            <mdl:SerialIdentifier>n/a</mdl:SerialIdentifier>
            <mdl:InventoryID>n/a</mdl:InventoryID>
            <mdl:Position>1</mdl:Position>
            <mdl:PositionsOccupied>1</mdl:PositionsOccupied>
            <!-- add the info that is not kept in the parent Device -->
            <xsl:apply-templates select="mdl:DataOperationRef|mdl:Sensitivity|mdl:Excitation|mdl:Calibration|mdl:Connector"/>
            <!-- ports is required, even if empty -->
            <mdl:Ports>
                <xsl:apply-templates select="mdl:Ports/*"/>
            </mdl:Ports>
        </mdl:DeviceModule>
    </xsl:template>
    <!--Move NameValue elements into NameValues containers-->
    <xsl:template match="mdl:VendorConfig|mdl:GenericParameter">
        <xsl:copy>
            <xsl:apply-templates select="mdl:ReadOnly|mdl:Owner"/>
            <mdl:NameValues>
                <xsl:apply-templates select="mdl:NameValue"/>
            </mdl:NameValues>
        </xsl:copy>
    </xsl:template>
    <!--Add ConditionParameter container to Sensitivity and Excitation elements-->
    <xsl:template match="mdl:Device/mdl:Sensitivity|mdl:Device/mdl:Excitation">
        <xsl:copy>
            <mdl:ConditionParameter>
                <xsl:apply-templates select="*"/>
            </mdl:ConditionParameter>
        </xsl:copy>
    </xsl:template>
    <!-- Tmats Schema Changes -->
    <!-- Add Tmats Version Attribute -->
    <xsl:template match="mdl:PCMFormatAttributes">
        <xsl:copy>
            <xsl:attribute name="TmatsVersion" namespace="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsCommon">106-13</xsl:attribute>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="tmats:PCMMeasurements">
        <xsl:element name="tmatsP:PCMMeasurements">
            <xsl:attribute name="TmatsVersion" namespace="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsCommon">106-13</xsl:attribute>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <!--the Tmats version on measurement fragments isn't required, so we don't need to do anything right now-->
    <xsl:template match="tmats:MeasurementFragments">
        <xsl:element name="tmatsD:MeasurementFragments">
            <!--<xsl:attribute name="TmatsVersion" namespace="http://www.wsmr.army.mil/RCCsite/Documents/106-13_Telemetry%20Standards/TmatsCommon">106-13</xsl:attribute>-->
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    <!--assign Tmats P group namespace-->
    <xsl:template match="tmats:InputData">
        <xsl:element name="tmatsP:InputData">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='InputData']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:Format">
        <xsl:element name="tmatsP:Format">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='Format']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:SyncCriteria">
        <xsl:element name="tmatsP:SyncCriteria">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='SyncCriteria']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:VariableWordLength">
        <xsl:element name="tmatsP:VariableWordLength">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='VariableWordLength']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:SubframeSynchronization">
        <xsl:element name="tmatsP:SubframeSynchronization">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='SubframeSynchronization']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:AsyncEmbeddedFormat">
        <xsl:element name="tmatsP:AsyncEmbeddedFormat">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='AsyncEmbeddedFormat']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:FormatChange">
        <xsl:element name="tmatsP:FormatChange">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='FormatChange']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:AlternateTagData">
        <xsl:element name="tmatsP:AlternateTagData">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='AlternateTagData']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:AsynchronousDataMergeFormat">
        <xsl:element name="tmatsP:AsynchronousDataMergeFormat">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='AsynchronousDataMergeFormat']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:Comments">
        <xsl:element name="tmatsP:Comments">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="tmats:*[ancestor::*[local-name()='Comments']]">
        <xsl:element name="tmatsP:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <!--All Tmats not specified are Tmats D group-->
    <xsl:template match="tmats:*">
        <xsl:element name="tmatsD:{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <!--Convert FragmentTrasferOrder to attribute-->
    <xsl:template match="tmats:MeasurementFragments/@FragmentTransferOrder">
        <xsl:element name="tmatsD:FragmentTransferOrder">
            <xsl:value-of select="."/>
        </xsl:element>
    </xsl:template>
    <!--remove Length element-->
    <xsl:template match="tmats:Measurement/tmats:Length"/>
    <xsl:template match="tmats:IDCounter/tmats:WordLength" priority=".6"/>
</xsl:stylesheet>