# Challenge Problems

This project contains various challenge problems (CP) for flight testing and VICTORY. 
A CP subfolder typically contains a problem description, before and after MDL files, 
a textual file describing constraints that needs be satisfied, and 
a textual file containg events/messages generated/used. 
As we refine the CPs, the set of documents may change as well as how constraints are represented.

The name of the challenge problem should include some reference to the dominant scenario to which it applies.

Example Directory Structure:

```
- /FlightTesting
  -- /CP_01_alias
     --- Problem Description.md/.ppt/.txt/.odt
     --- BEFORE_MDL.xml
     --- AFTER_MDL_Example.xml
     --- Constraints.md/.txt/.xsd
     --- Events_Messages.md/.txt
- /VICTORY
  -- /CP_01_alias
     --- Problem Description.md/.ppt/.txt/.odt
     --- BEFORE_MDL.xml
     --- AFTER_MDL_Example.xml
     --- Constaints.md/.txt/.xsd
     --- Events_Messages.md/.txt
```

