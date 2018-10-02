# IMMoRTALS Phase III CPs 
## CP 3. ROS Migration Evolution
### Motivation
ROS 2, which leverages ROS-SE(ROS Secure), has shown much more security features than ROS 1. But since there are already large amount of software packages for ROS 1 or other systems that are relatively mature enough, it will save lots of manual efforts if we can make use of various existing ROS 1 software packages, and utilize a few functions from non-ROS software that would be highly value-added if they can be integrated into the system.
​
Despite the potential benefits, normally we don’t have enough time to manually migrate these software from ROS 1 to ROS 2, and it could be even harder for non-ROS software to fit into ROS 2 system.
​
Thus, we need to find a way to convert the existing software packages for ROS 1 into ROS 2 packages automatically, by analyzing the ROS APIs and the software packages we want to mitigate. The problem is similar to selected update because the ROS’s update also leads to incompatibility, but this time we modify the packages, not the updated system.
​
​
### Perturbation
​The complexity in the perturbation space lies on the fact that there are multiple versions of ROS, between some versions like ROS 1 Indigo and ROS 1 Kinetic the changes are relatively small, but from ROS 1 to ROS 2 the changes are huge. Our tool should solve the problems for all versions. But we need to manually get the API information of different versions, the code we generated for two particular versions cannot be used in other two versions.
​
​Also, ROS 1 support packages in many kinds of languages, but ROS 2 only support python and C++ for now.  For languages other than these two, our tool cannot solve them without some manual work.


### Adaptation
#### Input
(1)The group of functions we want to migrate
(2)The model for ROS version 1 and ROS version 2 (whole knowledge of old and new APIs which are obtained manually)
#### Assumptions
(1) The assumption of the wrapper is that the group of functions we want to migrate only invoke APIs in ROS version 1.  For APIs that are in ROS version 1 but not ROS version 2, we don’t migrate functions that call them.
(2) The assumption of static analysis in Python is that although Python is a quite dynamic language, most of the time, programmers won’t use these dynamic features. So we can still perform some static analysis on it.
#### Adaptation
Given these inputs, we will:
(1) Write a wrapper that takes the messages of what functions send to ROS 1 as input, and outputs messages ROS 2 can accept. Using the API knowldege we collect.
​(2) Perform static analysis on the group of functions we want to migrate to get the dependence knowledge.

The functions we want to migrate may depend on functions in other packages, in this case we need to identify these dependences and migrate them as a whole. In order to fully understand what the migrate functions depend on, we need to apply some static analysis like call graph generation, data dependency analysis. 

To solve the challenge in statically analyzing python code. We can maintain a list, that records the cases in python where normal static analysis cannot handle them well. Then given a python program, if it doesn’t contain those cases, we can simply apply the common static analysis to it. We assume most of the time we can do that. Another situation is that, the dependency relationships in the variable level is complex, but the function level dependency is clear. So we can only apply function level analysis if its enough. For functions that are in other languages like C++, we need to find out the interface between C++ and python in ROS, and build the dependency relationship according to the interface.

These analysis can only be applied on code, not for configuration files. For databases, usually they won’t hardcode the database name in code, sometimes they ask users to input database name in runtime, so we cannot guarantee. 

​(3) Combine the wrapper we got from (1) and the self-sufficient piece of code we got from (2), this is our final output and it should run properly in the target ROS.

​
### Evaluation
The intent of the system is to preserve the original functionality of the code in ROS 1, while operating successfully in a ROS 2 environment. 
The performance of the code shall be determined by successfully completing the three tests outlined in the test procedure above, namely:
(1)Successful compilation of converted code
(2)Successful launch through ROSlaunch
(3)Converted code’s successful (simulated) completion of the original code’s task, within no longer than 10% (objective) or 25% (threshold) greater runtime than the original code performed its task. (according to the TARDEC document )
​
If we provide some test cases, then we can evaluate the successful rate of those test case, so the partially succeed rate scoring is appropriate.