# BRASS Scenario 6 : Normal Adaptation to MDL Configuration Evolution

The production of an MDL message can be considered an event to which other actors subscribe and consume.
An MDL message conforms to a particular schema which may differ from that assumed by its consumer.
This problem can be addressed by translating the message or by adapting the subscriber.
The subscriber can be modelled as a type of query on the message where only some
portion of the message is of interest to the subscriber.

In addition to the MDL message itself, in normal usage there existed a prior MDL message and
there is an invertible delta transaction (IDT) which provides a mapping between the two messages.
It may be the case that this transaction is not explicitly expressed nevertheless it is logically present.

There may be several paths which may be taken to produce equivalent results.
It is the responsibility of some type of broker to decide which of these paths are to be taken.
It is tempting to statically determine which path is "correct";
the collection of different paths form an ensemble of valid approaches.
What constitutes the best path will certainly change over the natural life of a project.

## Candidate Paths beginning with Message Production

This challenge problem demonstrates each of the potential paths and provides mechanisms for their comparison.

## Universal Condition

The following conditions are true for all paths.

### Precondition : Wherein A Previously Existing MDL Configuration is Replaced

The assumptions here are that a previous MDL configuration is present.
Further it is assumed that the previous configuration has been translated into
a collection of MDL messages each conforming to the schema expected by its subscribing devices.
As any device will only be concerned with some sub-schema of its subscription,
each device is modelled as a mapping (expressed as a query)
from a message schema version to a device schema.

### Postcondition : Wherein A Device Properly Changes its Behavior

The assumptions here are that a device exists.
It may be that the new MDL does not affect the device or that the devices behavior remains unchanged.
It is the goal of the challenge problem to indicate that the device's behavior remains unchanged.

It may be that the new MDL is incompatible with the needs of the device in which case
a warning should be generated indicating that the device is diminished or
an error if the device is sufficiently degraded that it can be considered inoperable.

It may also be the case that the MDL effectively and correctly disables the device.
This is neither an error nor a warning but is, in fact, correct.

## Translating MDL Message into Alternate MDL Schema

We assume there exists a mapping and a corresponding translator between the schemas.
The problem with this approach is that although the translation of an MDL message
between schema versions may have warnings it may well be the case that these
warnings are not related to data needed by a particular device; in which case
the translation may be provably correct and yet be flagged with warnings.

## Checking Translation of MDL Message into Device Schema

We assume a mapping between the message schema and the expected MDL schema for a device.
Further, we assume a mapping/query from the expected MDL schema and a device schema.
The correctness of the translation can be checked by composition of mappings.

## Construction of Alternate Device Mapping/Translator

In this case a translation program is generated that allows the device to
directly consume MDL messages of a set of MDL schema.


## Broker Metadata

In order for the broker to do its work metadata is needed.

### Provenance

Provenance indicates the genealogy of a data item.

#### Creator

The principal that created the message.

#### Inputs

The messages and data from which the message was derived.
The notion of version is subsumed by the retention of the identities of the inputs.

#### Schemas

The inputs are presumed to conform to some schema and that schema's constraints.
The message itself also has a schema to which it conforms.

#### Mappings

A declarative description describing the relationships between the schemas.
It may be the case that there are imperative elements are present
in the descriptions but these should be avoided and flagged when they occur.



 
