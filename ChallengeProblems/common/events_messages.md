# Events and Messages

An implementation of a durable message queue as broker will be provided.
The individual performers are free to implement whatever architecture they choose.
Conceptually the following information should be available for any message generated.


## Metadata

In order for the broker to do its work metadata is needed.
This is used to find 

### Identity

A uuid must be provided for every message.

### Provenance

Provenance indicates the genealogy of a data item.

#### Creator

The principal that created the message.

#### Inputs / Dependencies

The messages and data from which the message was derived.
The notion of version is subsumed by the retention of the identities of the inputs.

#### Schemas

The inputs are presumed to conform to some schema and that schema's constraints.
The message itself also has a schema to which it conforms.

#### Mappings

A declarative description describing the relationships between the schemas.
It may be the case that there are imperative elements are present
in the descriptions but these should be avoided and flagged when they occur.

### State

This includes the status of this message.
The initial message may be marked as a candidate solution.
This implies that other analysis will be performed 
using the information contained in the original message.

