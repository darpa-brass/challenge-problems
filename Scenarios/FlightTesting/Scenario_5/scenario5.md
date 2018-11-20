title: FT Scenario 5
class: animation-fade
layout: true
<!-- This slide will serve as the base layout for all your slides -->

.bottom-bar[
  {{title}}
]

---

class: impact

# {{title}}
## Swap Data Acquisition Unit 


### Adapted from a flight test that occurred in 2012 in F-35 Lightning flight testing at NAS Patuxent River

---

# Brief Description
.col-8[
This scenario describes a pre-flight situation that involves swapping instrumentation hardware in the test article. The Data Acquisition Unit (DAU) is broken and needs to be replaced by another DAU already in stock from a different manufacturer. 
The objective is to configure the new DAU to meet the same requirements as the previous one. 
]

.col-4[
![](images/Scenario5_Picture1.png "Scenario Description")
]

---
# Test Article Network

![](images/Scenario5_Picture2.png "Test Article Network")

---

# Test Article

Aircraft: F-35B

![](images/Scenario5_Picture3.png "F-35B")

---

# Range Infrastructure

.col-6[
- Range Network:
	- Naval Air Station  Patuxent River (known as NAS Pax River)
- Equipment Used:
	- GSE (Ground Support Equipment)
- Equipment Available:
	- Replacement DAU
]

.col-6[
![](images/Scenario5_Picture4.png "Range Infrastructure")
]

---

# Flight Test Operation Flow

![](images/Scenario5_Picture5.png "Scenario 5 Operation Flow")

---

# Test Objective
## Configure Replacement DAU

- Initial configuration/requirements for the TTC DAU 
	- Sample Rate: 128 Hz
    - Data Length: 16-bit Resolution  
    - 8-channel thermocouple card
    - 6-channel signal conditioner card


- New configuration/requirements for the Vendor B DAU Replacement
    - Sample Rate: 100 Hz
    - Data Length: 8-bit Resolution
    - 4-channel thermocouple card (Quantity: 2)
    - 2-channel signal conditioner card (Quantity: 3) 

---

# Initial MDL Representation

![](images/Scenario5_Picture6.png "MDL")

---
# Initial MDL Representation
## TTC DAU Internal Structure

![](images/Scenario5_Picture7.png "MDL")

---

# Initial MDL Representation
## Measurements

![](images/Scenario5_Picture8.png "MDL")

---

# TTC DAU Datasheet

![](images/Scenario5_Picture9.png "MDL")

---

# Data Acquisition Unit Modules

![](images/Scenario5_Picture10.png "MDL")

---

# Sensors

![](images/Scenario5_Picture11.png "MDL")

---

# Sensors
## Accelerometer

![](images/Scenario5_Picture12.png "MDL")

---

# Sensors
## Thermocouple

![](images/Scenario5_Picture13.png "MDL")

---

# Initial MDL Representation
## Port Mappings

![](images/Scenario5_Picture14.png "MDL")

---

# Replacement DAU

.col-6[
- Configuration for the Vendor B DAU Replacement
	- Sample Rate: 100 Hz
    - Data Length: 8-bit Resolution
    - 2 * 4-channel thermocouple card
    - 3 * 2-channel signal conditioner card
- The objective is to configure the replacement hardware to meet the same requirements as with the TTC DAU previously used
	- Map measurements to ports and devices
	- Configure new sample rate and bit resolution
		- Vendor B capabilities are still within the requirements
]

.col-6[
![](images/Scenario5_Picture15.png "Replacement DAU")
]

---

# Initial MDL Representation for Vendor B DAU
## Sample Rate / Data Length

![](images/Scenario5_Picture16.png "MDL")

---

# Initial MDL Representation for Vendor B DAU

![](images/Scenario5_Picture17.png "MDL")

---

# Initial MDL Representation for Vendor B DAU

![](images/Scenario5_Picture18.png "MDL")

---

# Initial MDL Representation for Vendor B DAU (Port Mappings)

![](images/Scenario5_Picture19.png "MDL")

---

# Cost, Value and Risk

![](images/Scenario5_Picture20.png "MDL")

---

# Classic Solution

- Option A and B


- No MDL changes needed for this solution

---

# Suggested Solution

- Use available hardware in inventory and configure to satisfy original requirements

- MDL Configuration file needs to be updated to reflect the new hardware configuration and connections
	- Review new configuration datasheets (sample rate, data length, port connections)
	- Map measurements to ports and devices
