# Challenge Problems

This project contains various challenge problems (CP) for flight testing and VICTORY. To add a new CP, create a subfolder under either the FlightTesting or the VICTORY folder based on the problem domain. A CP subfolder should probably contain a problem description, a before MDL, a textual file describing constraints that needs be satisfied, and a textual file containg events/messages generated/used. As we refine the CPs, the set of documents may change as well as how we would like to represent the constraints.


Example Directory Structure:

```
- /FlightTesting
  -- /CP 1
     --- Problem Description.ppt/.txt/.odt
     --- BEFORE_MDL.xml
     --- AFTER_MDL_Example.xml
     --- Constraints.txt/.xsd
     --- Events_Messages.txt
- /VICTORY
  -- /CP 1
     --- Problem Description.ppt/.txt/.odt
     --- BEFORE_MDL.xml
     --- AFTER_MDL_Example.xml
     --- Constaints.txt/.xsd
     --- Events_Messages.txt
```

