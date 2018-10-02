# IMMoRTALS Phase III Challenge Problem (CP) - ROS Migration (DRAFT)

## Overview

The IMMoRTALS team proposes to apply and advance its research in adapting applications to third-party library evolution in the context of the Robot Operating System (ROS) code base and the specific use-cases provided by TARDEC. Our challenge problem will address two use cases: (1) Adapting applications to API migration issues, and (2) Importing non-ROS code into the ROS framework. This document covers case (1).

## Motivation

The IMMoRTALS team began developing adaptation techniques to address third-party library evolution in Phase II. Our focus included straightforward API signature changes as well as complex cases due to evolving resource models (e.g., permissions),  programming idioms, and usage patterns (e.g., changes to code from a single-threaded declare-init-use pattern to an asynchronous callback interface).

These types of changes are common in third-party library ecosystems, like ROS and Java. The current state-of-the-art for determining the impact of such changes to an application and applying a patch relies on manual analysis and programming using non-structured API documentation and change logs as inputs. The approach carries the significant disadvantage of incurring repeated engineering costs across multiple occurrences of the same change since the change is not described in some structured, machine readable manner.

In some cases (e.g., Swift migration tools provided by the XCode IDE), automated analysis and migration tools are available; however, they have the following limitations:

* Their scope is ad-hoc (e.g., limited to a single migration use case for a programming language),

* They tend to focus on mechanical changes that can be made to project files (e.g., changing XML files, build files).

* They are not extensible or transparent (i.e., they do not expose the search patterns or the repair strategies they are target).

IMMoRTALS seeks to improve the state-of-the-art by creating a DSL (called PQL, or Program Query Language) and a supporting framework for managing the changes described above. In short, PQL provides library owners with a high-level facility for creating analysis and repair programs that can be easily leveraged across all applications which use the library.

An additional thrust of our research is to explore ways to generate PQL programs automatically from code samples that describe the source and target patterns. These can be provided by library developers as samples in the native library's programming language as paradigm or representative examples of the old and new usage patterns to target; e.g., an example of sending messages in ROS using TCP-ROS and an example using DDS.

## Perturbation

Several perturbation techniques may be combined to evaluate the techniques described above. Perturbation inputs include:

* Named labels of the source and target migration versions. This can trigger the Immortals DAS to apply the registered PQL patterns associated with each version migration pair against the system under test (SUT).

* The old and new sample programs to use as input for evaluating the PQL generation code.

* One or more source files that comprise the SUT.

## Adaptation

The adaptation will include correct modification of the SUT source files for the given migration path. If the PQL generation process is also evaluated, the adaptation will include the correct generation of PQL source files.

## Evaluation

Adaptation can be evaluated in two ways: (1) Successful execution of unit and scripted integration tests provided with the SUT; (2) Manual inspection of source files for correctness. For the PQL generation process, the generated interim PQL files can also be inspected for quality.

## Assumptions

We assume that the SUT application and unit/integration will be provided for use during research and development and evaluation.

## Limitations

While a significant portion of the correct PQL file may be generated automatically using code samples, this facility is expected to augment versus replace a developer-led process by creating a PQL skeleton program along with as many patterns/repairs as possible given the samples. Results will vary depending on whether the samples contain irrelevant code elements and whether the components of the old and new samples can be matched correctly. Evaluation of this facility should not be discrete (e.g., pass/fail) but instead take into consideration a more fine-grained metric of success (e.g., lines of PQL code generated correctly relative to an expected PQL file).

Similarly, the execution of PQL to repair code should be reviewed for accuracy and precision using a fine-grained metric. In many cases, it will not be possible to migrate or repair code automatically across usage patterns (e.g., if the new pattern includes references to concepts that are not present in the source program and cannot be derived through analysis).
