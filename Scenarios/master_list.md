title: Master Scenario List
class: animation-fade
layout: true
<!-- This slide will serve as the base layout for all your slides -->

.bottom-bar[
  {{title}}
]

---

class: impact

# Master
# Scenario
# List

---

# What This Presentation Is

- List of scenario "abstracts"
    - Background information to help understand the scenario
    - Description of the problem to be solved
    - Evaluation of benefits to the domain

---

# What we want from you

- Let us know 
    - by October 12 which scenarios you'll be pursuing in Phase III
    - now if you see something interesting and you'd like for us to grow one of these in a new direction for you

---

# Scenarios vs Challenge Problems

- BRASS's goal is to develop and grow adaptive software techniques
- These scenarios vary in complexity
    - Some are arguably too simple by themselves to make up a whole CP
- A CP is one or more scenarios that your team works together to tell a greater story
    - Can be done as a whole or as individual parts, so "CP" here is one of the three your team is responsible for in Phase III
- We'll work with you to define exactly the problem statement for your CP(s)

---

# CP Complexity

- We've marked weaker scenarios that are likely not "hard" enough (as currently described) to need BRASS techniques to solve
- We've also provided related scenarios to help provide direction on likely expansion directions
    - Not every scenario with a related section needs to be expanded
    - You have full freedom to combine others, we designed the scenarios to be modular
- Be prepared to show that the CP you've assembled has enough difficulty to be interesting 
    - This can include asking us to make a problem harder than the current formulation

---


# Table of Contents

- Flight Test
    - [1](#f1) [2](#f2) [3](#f3) [4](#f4) [5](#f5) [6](#f6) [7](#f7) [8](#f8) [9](#f9)
    
- VICTORY
    - [1](#v1) [2](#v2) [3](#v3) [4](#v4) [5](#v5) [6](#v6) [7](#v7) [8](#v8) [9](#v9)


---

class: impact

# Flight Test

---

name: f1

# FT Scenario 1
## Increase of Bandwidth For Safety of Flight Data

- Background
    - A fighter has a mission with a fixed scheduled transmission bandwidth. During the flight test, flight crew encountered heavy vibration. As a result, the requirement for safety data increased to make sure everything is fine. Now the mission needs a higher amount of bandwidth to be able to send the safety data down to the ground station, in order to continue to fly. For this scenario, range bandwidth is available.
    - Voice and safety data need to be guaranteed for the test mission to be successful.

---

# FT Scenario 1
- Description
    - This scenario involves updating the MDL to reflect a new transmission schedule.
- Evaluation Criteria
    - Maximum latency, total bandwidth use, density (how many other flights can still meet their own requirements?)
- Note: "Easy"
- Related: [FT Scenario 2](#f2), [FT Scenario 4](#f4)

---

name: f2

# FT Scenario 2
## Change in Frequency of Operation

- Background
    - A fighter is operating at an assigned frequency. Testing is interrupted when another higher priority mission needs to use the same frequency. To accommodate the higher priority mission, the assets associated with the fighter must be reconfigured immediately at a newly assigned frequency. 

---

# FT Scenario 2
- Description
    - This scenario involves updating the MDL to reflect a new transmission schedule.
- Evaluation Criteria
    - Maximum latency, total bandwidth use, density (how many other flights can still meet their own requirements?)
- Note: "Easy"
- Related: [FT Scenario 1](#f1), [FT Scenario 4](#f4)

---

name: f3

# FT Scenario 3
## Sensor Failure in Structural Strain Test

- Background
    - The objectives of the tests are to measure the strain on the tail boom of the AH-1G Helicopter.
    - Three sensors are mounted at positions on the tail. During flight test, the sensor mounted in position 3 failed.
---

# FT Scenario 3
- Description
    - There are two pieces of this scenario that can be explored.
        - Detection of the failure, given time series measurement data.
        - Recovery from the failure.
- Evaluation Criteria
    - On the detection side, speed and accuracy of detection.
    - On the recovery side, value and quality preserved by adaptation (drop data versus resample versus synthesize). 
- Note: Potentially "Easy" if not exploring all pieces, including measurement synthesis.

---

name: f4

# FT Scenario 4
## Live Reconfiguration of Relay Topology

- Background
    - A relay is using one aircraft to transmit data from one aircraft to another such that the aircraft of interest need not be accessible directly by ground antenna.
    - The scenario involves a single radio on the ground network, a single radio on a relay network (TA1), and a single radio on TA2 network as shown in the next slide. During the scenario the TA1 relay is needed for another priority mission so we need to adapt by using available assets to preserve the transmission of data in the case TA2 is outside the transmission range. 
    - In this scenario the transmission schedule is fixed for all radios in the scenario.
---

# FT Scenario 4
- Description
    - This scenario involves preservation of the transmission when the aircraft is outside the transmission range of the ground radio without losing end-to-end communication.
- Evaluation Criteria
    - Latency of link, quality of signal, opportunity cost to other active missions.
- Note: "Easy"
- Related: [FT Scenario 1](#f1), [FT Scenario 2](#f2)

---

name: f5

# FT Scenario 5
## Swap Data Acquisition Unit

- Background
    - This scenario describes a pre-flight situation that involves swapping instrumentation hardware in the test article. The Data Acquisition Unit (DAU) is broken and needs to be replaced by another DAU already in stock from a different manufacturer. 
    - The objective is to configure the new DAU to meet the same requirements as the previous one. 

---

# FT Scenario 5
- Description
    - This scenario involves verifying that a given DAU is capable of meeting the original requirements of a test setup, and creation of an MDL configuration that meets those requirements.
    - This can alternatively include analysis of available hardware to find a good match.
- Evaluation Criteria
    - In the verification case, analysis of the created configuration and its satisfaction of the original requirements (where possible).
    - In the optimization case, power/weight/cost of the suggested configuration and the same verification that it does indeed work.
- Related: [VICTORY Scenario 5](#v5), [VICTORY Scenario 7](#v7)

---

name: f6

# FT Scenario 6
## Updates to MDL Schema and Software

- Background
    - The MDL schema has updated from v0.8.17 to v0.8.19, and software is patchily adjusting for the change. The configuration management software is still on v0.8.17, but must configure and communicate with devices using v0.8.19 for the latest round of flight tests. 
    - There must be a pathway to deliver a v0.8.19 file to the DAU from the v0.8.17 configuration manager to set up the device, and reverse the communication when exporting the configuration from the device for verification.
---

# FT Scenario 6
- Description
    - This scenario involves automated synthesis of translators from schema diffs and changelogs.
- Evaluation Criteria
    - Schema validity of transforms, preservation of functional information

---

name: f7

# FT Scenario 7
## Opportunistic Bandwidth Use

- Background
    - This scenario describes a situation that involves two test articles initially sharing the same frequency for their missions. Suddenly TA1 is grounded and leaves the other aircraft (TA2) with more bandwidth for the next 30 minutes.
    - The goal is for the airborne aircraft (TA2) to take advantage of the extra bandwidth.

---

# FT Scenario 7
- Description
    - This scenario involves planning new tests on the macro scale, or adjusting downlink data streams at the micro scale, to maximize use of available bandwidth.
- Evaluation Criteria
    - Gained test value, bandwidth use.

---

name: f8

# FT Scenario 8
## Numerical Processing for Computationally Limited Systems

- Background
    - Historical ground processing hardware is limited to specific shapes of data processing calculations it can do (e.g. polynomials and lookup tables). Any others are either entirely unimplementable, or require using alternate code pathways with significant performance tradeoffs.
    - On-board processing capabilities are increasing on TAs, and it is becoming possible to add additional "Computational Elements" to a TA network to preprocess measurements in order to optimize bandwidth usage.
---

# FT Scenario 8
- Description
    - This scenario involves processing the data processing grammar of MDL and implementing the calculations.
- Evaluation Criteria
    - If aiming to drop bandwidth usage, reduction in total data needing to go to the ground.
    - If aiming to help legacy hardware, reformulation of calculations to match system constraints.
    - Performance of compiled calculations versus naive implementation.
- Related: [VICTORY Scenario 9](#v9)

---

class: impact

# VICTORY/BRASS Scenarios

---

name: v1

# VICTORY Scenario 1
## Adapting Adopted Specifications Inside VICTORY

- Background
    - VICTORY specifies WSDL 1.1 instead of WSDL 2.0, mainly due to lack of support for 2.0 at the time. It's possible in the future that WSDL 1.1 will become obsolete and VICTORY will need to move to 2.0. 
    - Side Note: TLS would be another example, but unsure of the feasibility of this use-case. Right now VICTORY just moved away from TLS 1.0 and required TLS 1.1, making TLS 1.2 optional. In the future, TLS 1.1 will become obsolete and TLS 1.2 will be required. Scenario would be to determine if there's a way to adapt TLS versions automatically?

---

# VICTORY Scenario 1
- Description
    - This scenario involves transforming the VICTORY WSDLs from the 1.1 standard to the 2.0 standard automatically. Ideally, current implementations using the 1.1 version of the VICTORY WSDLs would also be manipulated to conform to the new format of the 2.0 version of the VICTORY WSDLs.
- Evaluation Criteria
    - If only manipulating WSDLs, the evaluation will be to implement a VICTORY component type using the modified WSDLs and ensure the VICTORY component type passes the Compliance Test Suite.
    - If manipulating both WSDLs and accompanying software, the evaluation will be to test the modified implementation with the Compliance Test Suite.

---

name: v2

# VICTORY Scenario 2
## Adapting Authored Specifications Inside VICTORY
- Background
    - As VICTORY evolves, so do the specifications. While specifications must change in order to align with the current needs of the ground vehicle community, it's not realistic to assume existing implementations of VICTORY will always be updated to align with the evolving specifications. Legacy VICTORY services implemented on ground vehicles still need to be able to interact with newer clients. 
    - In the case of the Camera Gimbal VICTORY Component Type, the 1.6 version of VICTORY has a slew camera gimbal command which takes a roll, pitch, and yaw rate in degrees/second. The 1.7 version of VICTORY updated the slew camera gimbal command, making it more complex. 

---

# VICTORY Scenario 2
- Description
    - This scenario involves a client sending a V1.7 Slew command to a service running a V1.6 Camera Gimbal VICTORY component type, and the service being able to successfully the process the request and slew the camera accordingly.
- Evaluation Criteria
    - Did sending a V1.7 slew command to a service running a V1.6 Camera Gimbal VICTORY component type result in the successful slewing of the camera managed by the V1.6 service?
- Related: [VICTORY Scenario 4](#v4)

---

name: v3

# VICTORY Scenario 3
## Eliminating Dead Code Inside VICTORY Implementations

- Background
    - VICTORY uses a monolithic schema approach, meaning the data for all VICTORY component types are defined inside a few, large schema files. Generally, automated tools are used to convert the VICTORY schemas into objects inside code. Most implementations of VICTORY consist of only a small subset of VICTORY component types, yet these automated tools generate objects for all VICTORY data. This could result in substantial "dead code," taking up unnecessary disk space and opening the door to security breaches. 

---

# VICTORY Scenario 3

- Description
    - This scenario involves reducing the security concerns of the monolithic schema approach by eliminating the "dead code" issue. This can be done in one of two ways:
        - Use the VCL to determine which VICTORY component types are being implemented, and remove any unnecessary data inside the schemas.
        - Once the automated tool has generated code based on the schemas, remove all the dead code from the implementation.
- Evaluation Criteria
    - Did the final implementation take up less memory than the original implementation?
    - Did the implementation still pass the Compliance Test Suite (CTS) after the manipulation of the code (removal of dead code)?

---

name: v4

# VICTORY Scenario 4
## Constructing a VCL File Through Auto-Discovery

- Background
    - VICTORY recommends the use of Zeroconf for discovering VICTORY services on the network. While VICTORY Configuration Language (VCL) files are typically constructed manually, the ability to discover VICTORY services and construct a VCL file automatically would be beneficial.

---

# VICTORY Scenario 4

- Description
    - This scenario involves using Zeroconf and the defined VICTORY announcement strings to discover VICTORY services on the network, then construct a VCL file from scratch based on the information obtained during the discovery process.
- Evaluation Criteria
    - Does the VCL file constructed align with the VICTORY services running on the network?
- Note: "Easy"
- Related: [VICTORY Scenario 2](#v2)

---

name: v5

# VICTORY Scenario 5
## Service Performance vs. System Specifications

- Background
    - As VICTORY adoption is still in the early stages, there are not yet any end devices that natively support VICTORY. As such, current integrations of VICTORY on a platform involve running software adapters on a shared processing unit (SPU) to convert data on legacy non-VICTORY interfaces to VICTORY command, status, and health messages on the VICTORY network. The performance capabilities of SPUs can vary from dual core ARM processors with limited RAM and disk space to more robust Intel i7 based systems. The number of VICTORY services and their configuration that a given SPU can run while maintaining an acceptable degree of performance is limited based on the system specs of the SPU and the performance characteristics of the applications providing the services.

---

# VICTORY Scenario 5

- Description
    - This scenario involves determining whether or not an SPU running the services as specified in a VCL file can meet CPU and memory utilization requirements.
- Evaluation Criteria
    - Does the performance of the SPU remain within acceptable ranges when configured with a VCL that was evaluated to meet performance requirements?
    - Does the performance of the SPU exceed acceptable ranges when configured with a VCL that was evaluated to exceed performance requirements?
- Note: Potentially "Easy", depending on depth of reasoning.
- Related: [FT Scenario 5](#f5), [VICTORY Scenario 7](#v7)

---

name: v6

# VICTORY Scenario 6
## Network Performance and Utilization

- Background
    - Typical VICTORY services publish data and health information at periodic rates, and may even include encoded video streams. It could be possible that with a large amount of VICTORY services and fast data and health publishing rates, network utilization could exceed a set maximum threshold of, for instance, 37 percent of the network bandwidth.

---

# VICTORY Scenario 6

- Description
    - This scenario determines whether or not a network would remain under a given utilization when the VICTORY network is configured with a specific VCL.
- Evaluation Criteria
    - Did the network utilization remain under the threshold when the VICTORY network was configured with a VCL that was evaluated to not exceed the network utilization threshold?
    - Did the network utilization exceed the threshold when the VICTORY network was configured with a VCL that was evaluated to exceed the network utilization threshold?
- Related: [VICTORY Scenario 8](#v8)

---

name: v7

# VICTORY Scenario 7
## Adapting to System Malfunctions

- Background
    - When a Shared Processing Unit (SPU) running VICTORY services breaks down and needs to be replaced by another SPU in stock, the new SPU must be configured to meet the same requirements as the original SPU. 

---

# VICTORY Scenario 7

- Description
    - This scenario uses cost, value, and risk to determine the best approach for replacing the broken SPU. If the new SPU is different than the original SPU, other factors must be taken into consideration, such as the disk space allocated to the VICTORY Data Logger. 
- Evaluation Criteria
    - Was the new SPU configured to meet the same requirements as the original SPU?
    - Was the VICTORY Data Logger configuration modified to be in-line with the new SPU specifications?
- Related: [FT Scenario 5](#f5), [VICTORY Scenario 5](#v5)

---

name: v8

# VICTORY Scenario 8
## Using Equipment and Environment for Configuration Adaption

- Background
    - Ground vehicles may be equipped with a variety of hardware and software packages. Depending on what is installed on the vehicle, the VICTORY services can be reconfigured in a variety of ways based on the current environment.
    - In the case of a shot detected, automatically reconfiguring VICTORY services to respond to the threat could be beneficial.

---

# VICTORY Scenario 8

- Description
     - This scenario involves surveying the VICTORY services running on the vehicle, then reconfiguring applicable VICTORY services in the event of a threat detected by the system.
- Evaluation Criteria
    - If the vehicle contains a camera on a gimbal, was the camera gimbal reconfigured to move to the point of the threat? 
    - If the vehicle contains a video encoder, was the frame rate reconfigured for optimum performance? Was the resolution increased for higher video quality?
    - Continued on next slide...

---

# VICTORY Scenario 8

- Evaluation Criteria Cont.
    - If the vehicle is running a VICTORY Data Logger, was the logger reconfigured to to the following:
        - Check available disk space on SPU, and increase the maximum log size accordingly.
        - Increase the update rate of data streams on the VDB for increased logging.
        - Ensure all data streams are being logged. Add any that aren't currently included.
        - Add/update time filters so any data being logged from the time the threat was detected won't accidentally be erased.
- Related: [VICTORY Scenario 6](#v6)

---

name: v9

# VICTORY Scenario 9
## Improving Sensor Fusion Through Numerical Adaptation

- Background
    - A use case in VICTORY is using the data provided by shared services (position, orientation, and direction of travel) to point a camera to an arbitrary position. This can be the location of a threat, or any other point of interest. Thus far, demonstrations using this sort of sensor fusion has been completed with moderate success. 
    - Some of the challenges with accuracy may have to do with rounding errors of floating point values used by these shared services.

---

# VICTORY Scenario 9

- Description
    - This scenario involves using numerical adaptation to improve accuracy when using sensor fusion to move a camera to a specific point of interest.
- Evaluation Criteria
    - How did the accuracy of the camera movement after correcting rounding errors compare to the accuracy of the camera without the correction?
- Note: "Easy"
- Related: [FT Scenario 9](#f9)

