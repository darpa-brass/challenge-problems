-------------------------------------------------------------
--                  iNET Program (NAWCAD)                  --
-------------------------------------------------------------
--                                                         
-- Wireshark decoder for TmNS Messaging                    
--   Based off of TA Standard v0.8.2                      
--                                                        

--  Developed under the Integrated Network Enhanced Telemetry (iNET)
--  project
--
--  Developed by Southwest Research Institute
--               Automation and Data Systems Division
--               Communication and Embedded Systems Department
--
--   *** Distribution Statement C *********************************
--   Distribution authorized to U.S. Government Agencies and their
--   contractors for the purposes of reviewing and commenting on
--   this working document.  Administrative protections are employed
--   to limit premature dissemination.  Other requests for this
--   document shall be referred to the iNET Program Manager or the
--   iNET Program Office
--   **************************************************************
--
-- Short Description:
-- This is a Lua script that will dissect only TmNS Data Messages' message
-- header, as well as package header in message payload.
-- It does not dissect package payload.  To do that, you need to
-- run TmNSUtilities tool to create a MDL specific Lua script to
-- to replace this generic one.

-- Note, this Lua script uses a default destination port number of 55555.
-- If your destination is not the default, please change the line:
-- "LTC_DST_PORTS={55555}" 
-- at the beginning of this script accordingly.

-- $Date: 2014-05-12 12:35:50 -0500 (Mon, 12 May 2014) $
-- $Revision: 5696 $                                                                  
---------------------------------------------------------------


tmns_proto = Proto("TMNS","TmNS Data Message")

-------------------------------------------------------------

--- Set these ports for proper message detection and dissection ---
LTC_DST_PORTS={50003}
--no RC dissection at this point
--RC_PORT=50001

-------------------------------------------------------------

local OPTION_KIND_VALS = { [0x00]="End of options (padding)",
                           [0x01]="No Operation (NOP)",
                           [0x80]="Reserved for future allocation",
                           [0x81]="Reserved for future allocation",
                           [0x82]="DataSource Configuration",
                           [0x83]="DataSource Error",
                           [0x84]="Sync Pattern",
                           [0x85]="DestinationAddress",
                           [0x86]="Fragment Byte Offset",
                           [0x87]="Package Count" }

local MSG_FLAG_STDPKGHDR_VALS = { [0x00]="Non-Standard (MDL-based) Package Headers", 
                                  [0x01]="Standard Package Headers" }

local MSG_FLAG_PLAYBACK_VALS = { [0x00]="Live Data", 
                                 [0x01]="Playback Data" }
                                 
local MSG_FLAG_MSGFRAG_VALS = { [0x00]="Complete TDM", 
                                [0x01]="First Fragment",
                                [0x10]="Middle Fragment",
                                [0x11]="Last Fragment" }
                                
local MSG_FLAG_SIMDATA_VALS = { [0x00]="Acquired Data", 
                                [0x01]="Simulated Data" }
                                
local MSG_FLAG_TIMESYNC_VALS = { [0x00]="Time Sync'd", 
                                 [0x01]="Not Sync'd" }
                                 
local MSG_FLAG_HEALTH_VALS = { [0x00]="No Error with Data Source", 
                               [0x01]="Error with Data Source" }
                               
local MSG_FLAG_EOD_VALS = { [0x00]="Normal TmNS Data Message", 
                            [0x01]="End-Of-Data TmNS Data Message" }


-------------------------------------------------------------


local f = tmns_proto.fields

------------- TmNS Data Message Fields -------------
-- parameters are abbr(filter name), name(appear in tree), base, description enum, mask
--- TmNS Header ---
--tdm stands for TmNS Data Message
f.tdm_hdr_msg_ver = ProtoField.uint8("tmns.hdr.msg_ver", "Message Version", base.DEC, nil, 0xF0)
f.tdm_hdr_owc = ProtoField.uint8("tmns.hdr.owc", "Option Word Count", base.DEC, nil, 0x0F)
f.mdid = ProtoField.uint32("tmns.mdid", "MDID", base.HEX)
f.seqnum = ProtoField.uint32("tmns.seqnum", "Sequence Number", base.DEC)
f.msglen = ProtoField.uint32("tmns.msglen", "Message Length", base.DEC)
f.option_kind = ProtoField.uint8("tmns.option.kind", "option-kind", base.HEX, OPTION_KIND_VALS)
f.option_len = ProtoField.uint8("tmns.option.len", "option-length", base.DEC)
f.option_data = ProtoField.uint8("tmns.option.data", "option-data", base.HEX)


f.tdm_hdr_flag_rsvd = ProtoField.uint16("tmns.hdr.flag.rsvd", "Reserved", base.HEX, nil, 0xFF00)
f.tdm_hdr_flag_stdpkghdr = ProtoField.uint16("tmns.hdr.flag.stdpkghdr", "Standard Package Header Flag", base.DEC, MSG_FLAG_STDPKGHDR_VALS , 0x0080)
f.tdm_hdr_flag_playback = ProtoField.uint16("tmns.hdr.flag.playback", "Playback Data Flag", base.DEC, MSG_FLAG_PLAYBACK_VALS, 0x0040)
f.tdm_hdr_flag_msgfrag = ProtoField.uint16("tmns.hdr.flag.msgfrag", "Message Fragmentation Flags", base.DEC, MSG_FLAG_MSGFRAG_VALS, 0x0030)
f.tdm_hdr_flag_simdata = ProtoField.uint16("tmns.hdr.flag.simdata", "Data Source Sim Data Flag", base.DEC, MSG_FLAG_SIMDATA_VALS, 0x0008)
f.tdm_hdr_flag_timesync = ProtoField.uint16("tmns.hdr.flag.timesync", "Data Source Time Lock Flag", base.DEC, MSG_FLAG_TIMESYNC_VALS, 0x0004)
f.tdm_hdr_flag_health = ProtoField.uint16("tmns.hdr.flag.health", "Data Source Health Flag", base.DEC, MSG_FLAG_HEALTH_VALS, 0x0002)
f.tdm_hdr_flag_eod = ProtoField.uint16("tmns.hdr.flag.eod", "End Of Data Flag", base.DEC, MSG_FLAG_EOD_VALS, 0x0001)

f.msg_secs = ProtoField.uint32("tmns.msg_secs", "Seconds", base.DEC)
f.msg_nsecs = ProtoField.uint32("tmns.msg_nsecs", "Nanoseconds", base.DEC)

f.pdid = ProtoField.uint32("tmns.pdid", "PDID", base.HEX)
f.pkglen = ProtoField.uint16("tmns.pkglen", "Package Length", base.DEC)
f.pkg_status = ProtoField.uint16("tmns.pkg.flag", "Status Flags", base.HEX)
f.pkg_tdelta = ProtoField.uint32("tmns.pkg_time_delta", "Package Time Delta (ns)", base.DEC)

--fields added by Liu
--every tree item should be represented by a ProtoField so that the tree will default to a collapsed look instead of expanded look.
f.msg_hdr = ProtoField.string("tmns.msg.hdr", "TmNS Data Message Header")
f.measurement = ProtoField.string("tmns.measurement", "Values for MeasurementID")
f.measurement_info = ProtoField.string("tmns.measurement.info", "info")
f.occurrence = ProtoField.string("tmns.occurrence", "occurrence")
f.syllable = ProtoField.string("tmns.syllable", "syllable")

f.tdm_hdr_flags = ProtoField.string("tmns.hdr.flags", "TDM Message Flags")
f.msg_timestamp = ProtoField.string("tmns.msg.timestamp", "TDM Message Timestamp")
f.msg_payload = ProtoField.string("tmns.msg.payload", "TmNS Data Message Payload")
f.pkg = ProtoField.string("tmns.pkg", "Package") 
f.pkg_hdr = ProtoField.string("tmns.pkg.hdr", "Package Header")
f.pkg_payload = ProtoField.string("tmns.pkg.paylaod", "Package Payload")
f.pkg_padding = ProtoField.string("tmns.pkg.padding", "Package Padding")
-------------------------------------------------------------

local pkgExtractors = {}

function tmns_proto.dissector(buffer,pinfo,tree)

-------------
    local offset = 0
    local msg_type = 0
    local buf_len = buffer:len()

    pinfo.cols.protocol = "TmNS"
    
    local utc_time = pinfo.abs_ts
    local tai_time = utc_time + 35
    
    
    -- Set the msg_type and column display info
    --   msg_type definitions:
    --      1 = Latency/Throughput Critical (LTC) TmNS Data Message (TDM)
    --      2 = Reliability Critical (RC) TDM
    --      3 = not yet defined...
    --
    
--  original from Todd using single port  
--    if pinfo.dst_port == LTC_DST_PORT then
--        msg_type = 1
--    elseif pinfo.src_port == RC_PORT then
--        msg_type = 2
--    elseif pinfo.dst_port == RC_PORT then
--        msg_type = 2
--    else
--        msg_type = 3
--    end

    msg_type = 3
    for count = 1, #LTC_DST_PORTS do
      if pinfo.dst_port == LTC_DST_PORTS[count] then
        msg_type = 1
      end  
    end  
--    we are not going to worry about RC now    
--    if msg_type ~= 1 then
--      if pinfo.src_port == RC_PORT or pinfo.dst_port == RC_PORT then
--        msg_type = 2
--      end
--    end
    
    local descr_info = "TmNS"
    if msg_type == 1 then
        descr_info = string.format("%s: LTC Data", descr_info)
    elseif msg_type == 2 then
        descr_info = string.format("%s: RC Data", descr_info)
    end
    pinfo.cols.info = descr_info

-------------


    -- Decode TMNS message based on its type
    if msg_type == 1 then       -- LTC TmNS Data Message
        local tree_tmns = tree:add(tmns_proto, buffer(), "TmNS Data Message - Latency/Throughput Critical (LTC)")


        -- TmNS Data Message Header
        local tree_tmns_header = tree_tmns:add(f.msg_hdr, buffer(offset), " ")

        -- offset in bytes, so the first two header items share the same byte
        local ver_owc = buffer(offset, 1)
        tree_tmns_header:add(f.tdm_hdr_msg_ver, ver_owc)
        tree_tmns_header:add(f.tdm_hdr_owc, ver_owc)
        offset = offset+1

        -- bit.band (binary and)
        local owc_32bit_words = bit.band(ver_owc:uint(), 0x0F)
        local hdr_len = 24 + (4 * owc_32bit_words)
        tree_tmns_header:set_len(hdr_len)
        
        offset = offset + 1     -- Reserved 8 bits
        
        local tree_tmns_header_flags = tree_tmns_header:add(f.tdm_hdr_flags, buffer(offset), " ")
        tree_tmns_header_flags:set_len(2)
        
        --tree_tmns_header_flags:add(buffer(offset, 1), "Reserved", buffer(offset,1):uint())
        --offset = offset + 1
        tree_tmns_header_flags:add(f.tdm_hdr_flag_rsvd, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_stdpkghdr, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_playback, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_msgfrag, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_simdata, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_timesync, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_health, buffer(offset, 2))
        tree_tmns_header_flags:add(f.tdm_hdr_flag_eod, buffer(offset, 2))
        
        local stdpkghdr = bit.band(buffer(offset, 2):uint(),0x0080)
        offset = offset + 2
               
        local mdid = buffer(offset, 4)                  
      
        tree_tmns_header:add(f.mdid, mdid) 
        
        offset = offset + 4
       
        descr_info = string.format("%s >>---> MDID:0x%08x", descr_info, mdid:uint()) 
        
        pinfo.cols.info = descr_info
        
        local seqnum = buffer(offset, 4)
        tree_tmns_header:add(f.seqnum, seqnum)
        offset = offset + 4
        
        local msglen = buffer(offset, 4)
        tree_tmns_header:add(f.msglen, msglen)
        offset = offset + 4
        
        local tree_tmns_header_timestamp = tree_tmns_header:add(f.msg_timestamp, buffer(offset), " ")
        tree_tmns_header_timestamp:set_len(8)
        
        local msg_secs = buffer(offset, 4)
        tree_tmns_header_timestamp:add(f.msg_secs, msg_secs)
        offset = offset + 4
        
        local msg_nsecs = buffer(offset, 4)
        tree_tmns_header_timestamp:add(f.msg_nsecs, msg_nsecs)
        offset = offset + 4
        
        tree_tmns_header_timestamp:append_text(string.format("%d.%09d", msg_secs:uint(), msg_nsecs:uint()))
        
        -- if there are Application-Defined Fields, then process them here
        if owc_32bit_words > 0 then
            local adf_len = 4 * owc_32bit_words
            tree_tmns_header_adf = tree_tmns_header:add(buffer(offset), "Application-Defined Fields")
            tree_tmns_header_adf:set_len(adf_len)
            
            local option_num = 0
            
            -- Decode the ADF
            while offset < hdr_len do
                option_num = option_num + 1
                tree_tmns_header_adf_option = tree_tmns_header_adf:add(buffer(offset), string.format("Option:%d", option_num))
                
                local opt_kind = buffer(offset, 1)
                tree_tmns_header_adf_option:add(f.option_kind, opt_kind)
                offset = offset + 1
                
                if opt_kind:uint() < 0x80 then
                    -- option-length and option-data are not used for option-kinds less than 0x80
                    tree_tmns_header_adf_option:set_len(1)
                else
                    -- option-length and option-data are required for option-kinds greater than or equal to 0x80
                    local opt_len = buffer(offset, 1)
                    tree_tmns_header_adf_option:add(f.option_len, opt_len)
                    local opt_len_dec = opt_len:uint()
                    tree_tmns_header_adf_option:set_len(opt_len_dec)
                    offset = offset + 1
                    
                    tree_tmns_header_adf_option:add(buffer(offset, (opt_len_dec - 2)), "option-data:", buffer(offset, (opt_len_dec - 2)))
                    offset = offset + opt_len_dec - 2
                end
            end
        end
        
        
        -- TmNS Data Message Payload
        local payload_len = buf_len - hdr_len
        if payload_len > 0 then
            tree_tmns_payload = tree_tmns:add(f.msg_payload, buffer(offset), " ")
         
            -- Do not attempt to parse payload IF non-standard package headers are used
            if (stdpkghdr == 0x80) then     -- 0x80 indicates standard package headers are used
                local pkg_num = 0
                
                --buf_len is the tmns message length
                while offset < buf_len do
                    pkg_num = pkg_num + 1
                    --package has to be at least 12 bytes long
                    if buf_len - offset < 12 then
                      tree_tmns:set_text("TmNS Data Message - Something is wrong with this message")
                      tree_tmns_payload:set_text("TmNS Data Message Payload: not formed according to standard")
                      local tree_tmns_payload_pkg = tree_tmns_payload:add(f.pkg, buffer(offset), string.format("#%d ", pkg_num) .. "not enough bytes to form a package")                       
                      break            
                    end
                             
                    local pdid = buffer(offset, 4)
                    --grab the package id number
                    local packageID = pdid:uint()
                    
                    local tree_tmns_payload_pkg = tree_tmns_payload:add(f.pkg, buffer(offset), 
                                  string.format("#%d pdid: ", pkg_num) .. string.format("0x%08x", packageID)) 
                    
                    local tree_tmns_payload_pkg_hdr = tree_tmns_payload_pkg:add(f.pkg_hdr, buffer(offset), " ")
                    tree_tmns_payload_pkg_hdr:set_len(12)
                    
                    tree_tmns_payload_pkg_hdr:add(f.pdid, pdid)
                    offset = offset + 4
                    
                    local pkglen = buffer(offset, 2)
                    tree_tmns_payload_pkg_hdr:add(f.pkglen, pkglen)
                    local lenOfPkg = pkglen:uint()
                    if (lenOfPkg < 12) then
                      tree_tmns:set_text("TmNS Data Message - Something is wrong with this message")
                      tree_tmns_payload:set_text("TmNS Data Message Payload: not formed according to standard")
                      tree_tmns_payload_pkg:set_text(string.format("Package: #%d ", pkg_num) .. "This package is mal formed.")
                      tree_tmns_payload_pkg_hdr:set_text("package length is " .. lenOfPkg .. ", less than minimum requirement of 12 bytes")
                      break
                    end
                    -- highlight the whole package, include padding, which is not counted in package length.
                    if lenOfPkg - math.floor(lenOfPkg / 4) * 4 == 0 then 
                      tree_tmns_payload_pkg:set_len(pkglen:uint())
                    else
                      tree_tmns_payload_pkg:set_len(math.floor(lenOfPkg / 4 + 1) * 4 )
                    end
                    offset = offset + 2
                    
                    local pkg_status = buffer(offset, 2)
                    tree_tmns_payload_pkg_hdr:add(f.pkg_status, pkg_status)
                    offset = offset + 2
                    
                    local pkg_tdelta = buffer(offset, 4)
                    tree_tmns_payload_pkg_hdr:add(f.pkg_tdelta, pkg_tdelta)
                    offset = offset + 4
                    
                    -- pkg_payload_len does not include pkg header
                    -- offset is the start of actual measurement values
                    local pkg_payload_len = pkglen:uint() - 12
                    --debug("pkg_payload_len is " .. pkg_payload_len)
                    if pkg_payload_len > 0 then
                        if pkg_payload_len <= buf_len - offset then
                            tree_tmns_payload_pkg_payload = tree_tmns_payload_pkg:add(f.pkg_payload, buffer(offset), " ")
                            tree_tmns_payload_pkg_payload:set_len(pkg_payload_len)            
    
                            --package needs to end on 32-bit boundaries
                            if (pkg_payload_len - math.floor(pkg_payload_len / 4) * 4) ~= 0 then
                                --there should be padding bytes
                                if offset + (math.floor(pkg_payload_len / 4) + 1 ) * 4 <= buf_len then
                                  tree_tmns_payload_pkg:add(f.pkg_padding, buffer(offset + pkg_payload_len), "")
                                  offset = offset + (math.floor(pkg_payload_len / 4) + 1 ) * 4
                                else
                                  tree_tmns:set_text("TmNS Data Message - Something is wrong with this message")
                                  tree_tmns_payload:set_text("TmNS Data Message Payload: not formed according to standard")
                                  tree_tmns_payload_pkg:set_text(string.format("Package: #%d ", pkg_num) .. "This package is mal formed.")
                                  tree_tmns_payload_pkg:add(f.pkg_padding, buffer(offset + pkg_payload_len), "No padding found. Package should end on a 32 bit boundary")  
                                  break
                                end
                            else 
                                offset = offset + pkg_payload_len
                            end   
                        else
                            tree_tmns:set_text("TmNS Data Message - Something is wrong with this message")
                            tree_tmns_payload:set_text("TmNS Data Message Payload: not formed according to standard")
                            tree_tmns_payload_pkg:set_text(string.format("Package: #%d ", pkg_num) .. "This package is mal formed.")
                            tree_tmns_payload_pkg_payload = tree_tmns_payload_pkg:add(f.pkg_payload, buffer(offset), "Payload not long enough as defined in MDL ")
                            break
                        end
                                                          
                    end                    
                end     -- end while loop
                
            else
                -- standard package headers are not used
                descr_info = string.format("%s | *** Non-Standard Package Headers ***", descr_info)
                pinfo.cols.info = descr_info
                
                tree_tmns_payload:append_text(" | *** Non-Standard Package Headers ***")
            end
            
        end

     
    elseif msg_type == 2 then   -- RC TmNS Data Message
        local tree_rans = tree:add(tmns_proto, buffer(), "TmNS Data Message - Reliability Critical (RC)")
           
    end


-------------
end     -- end tmns.proto function

-------------

udp_table = DissectorTable.get("udp.port")
--register all the ports we found in the MDL 
for index = 1, #LTC_DST_PORTS do 
  udp_table:add(LTC_DST_PORTS[index],tmns_proto)
end
--udp_table:add(RC_PORT,tmns_proto)


