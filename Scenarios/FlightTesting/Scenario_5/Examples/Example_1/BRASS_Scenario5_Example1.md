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
### Example 1

---

# Overview

This scenario describes a pre-flight situation that involves swapping instrumentation hardware in the test article. The Data Acquisition Unit (DAU) is broken and needs to be replaced by another DAU already in stock from a different manufacturer. The objective is to configure the new DAU to meet the same requirements as the previous one.

---

# Background

See Scenario 5 slides for additional domain background.

---

# Test Objective
## Configure Replacement DAU

- Configuration/requirements for TTC DAU
    - Sample Rate: 128 Hz
    - Data Length: 16-bit resolution
    - 8-channel thermocouple card (Quantity: 1)
    - 6-channel signal conditional card (Quantity: 1)


- Configuration/requirements for Vendor B DAU
    - Sample Rate: 200 Hz
    - Data Length: 8-bit resolution
    - 6-channel thermocouple card (Quantity: 2)
    - 3-channel signal conditional card (Quantity: 3)

