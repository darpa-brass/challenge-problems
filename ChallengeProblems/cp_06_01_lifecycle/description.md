# BRASS Scenario 6 : Natural Adaptation to MDL Schema Evolution

## Overview

Every application is based on some ontology.
The data that conforms to that ontology is represented as a schema.
A schema realizes an ontology by expressing a specific ontology conforming structure.  
Realization both embellishes and simplifies.

Generally the ontology of a system can be considered static
throughout the development process.
In the long run, i.e. 100yr software, the ontological perspective changes.
The technology upon which that ontology is realized also evolves.
Together these two pressures cause substantial changes to the schema.
What are the artifacts that adapt in response to these schema changes?

An MDL message (file) provides configuration information to various devices.
Each device's requirements can be modeled as a query,
a mapping from the MDL schema to the implicit schema had by the device.
If two MDL schema versions are monomorphic then all is copacetic,
a direct translator can be generated and any queries will work correctly.
If the mapping is isomorphic it is necessarily monomorphic in both directions.
However it is likely that a new schema is richer in some way than its predecessor;
it is monomorphic only from old to new, the inverse mapping having some ambiguity.
This ambiguity may or may not adversely affect a query;
it would be useful to know if the composition of the query and the
schema mapping is "correct".

# Evolutionary Architecture

The process is essentially asynchronous;
the events representing evolutionary pressure can be exerted on any aspect of the system.
The motivating triggering event is the translator-generation-request.

![translator generation](./das_bus_generate_xlator.svg)

This translator-generation-request is a tertiary event following a change
to a schema following the need for a change to the schema.

The translator-generation-request presumes the existence of several artifacts.
* The definition of the source, S, and target, T, schema
* The definition of the mapping, X:S->T, from S to T
* The definition of the query result schema, R, and the query, Q:R->S

The translator-generation-result-report describes successful/failure
for each of the artifacts requested or resources required.
As the resources required are identified a message requesting
their generation will be published.
This illustrates the fundamental asynchronous nature of the problem.


![translator generation](./das_bus_xlate_msg.svg)

Once the translator is running it will listen and respond
to the appearance of MDL messages of the source version.
Thus, an MDL message will be automatically translated by the running translator.


# MDL Message Translation

The primary goal is to translate MDL configuration messages.
One such translator is generated for each pair of schema versions.
For the purpose of this discussion let us choose two arbitrary schema S and T.
Currently this translator is written in a somewhat declarative form in XSLT.
The translator, X:S->T, is realized based on a mapping between S and T.


## Universal Condition

The following are barrier conditions.

### Precondition : A pair of Schema are known

The assumptions here are that the requisite MDL schema are present
as well as the mapping between schema pairs.

### Postcondition : Wherein A Device Properly Changes its Behavior

A translator is produced which responds to message events of a
certain type by converting the message to an alternate version and
publishing it as a message.

## A Request for an MDL Configuration Message Translator

![translator practice](./schema_evolution_06.svg)

Produce a translator that will subscribe to messages of a certain type and version.
From that message will be produced a message of a target type and version.

### Forward Schema Message Translator

The forward translator corresponds to the provided mapping, X:S->T.
This translator is of use for new devices which wish to use an MDL
message conforming to the old schema.

### Reverse Schema Message Translator

The reverse translator corresponds to the inverse of the provided mapping, Y:T->S.
This translator is of use for old devices which wish to
use an MDL conforming to the new schema.

## A Request for an MDL Device Query Translator

Produce a translator that will subscribe to messages of a certain type and version.
From that message will be produced a query representing a particular device type and version.

## A Request to Check an MDL Configuration Message is Device Compatible

Evaluate a translator, used for a certain message type and version,
to determine if its output message will be adequate for a particular device.

## A Request to Compose MDL Mappings

Evaluate a translator, used for a certain message type and version,
to determine if its output message will be adequate for a particular device.

## Adaptation Use Cases

The following adaptation use cases are enabled by this research:

* As the MDL schema is modified and newer documents are created using updated schema, it is often possible to keep older applications functional by using XSLT to transform documents as appropriate. This transformation may apply to the entire document or a subset and the specific direction of the transformation will depend on each case. Documents may be transformed to newer or older versions of the schema as needed. The success of this approach depends on the nature of the schema changes to the specific XML sections on which applications depend. Given the mapping of this dependency (between an application or device and the MDL schema) and the mapping between two versions of the MDL schema (e.g., an upgrade from version 1.0 to 1.1), the techniques evaluated by this CP can be used to 1) Determine whether it's possible to produce XSLT transformations that provide the type of compatibility described above, and 2) Provide such an XSLT if possible.

* In many cases, it is necessary to produce XSLT transformations across multiple versions of the MDL schema. This transformation can be produced through the use of multiple XSLT files applied sequentially, but this is inefficient and difficult to maintain and understand. The techniques described in this document can be used to produce compositional or 'flattened' XSLT files that span multiple MDL versions.

Though the techniques described in this document require the mapping information (between devices/software components and MDL schema as well as between MDL schema versions) as inputs, the techniques represent an improvement over the state of the art in several ways. Firstly, the abstraction layer for this mapping is increased, allowing a common source of mapping information to produce multiple XSLT files that target specific sections of MDL across multiple directions (from older versions of MDL to newer and vice-versa). Secondly, though XSLT can be used to describe this mapping information, it is a poor choice as the system of record for this information as it conflates transformational constructs (e.g., looping, if-then expression, case logic, etc.) with what is required to describe the mapping between data.
