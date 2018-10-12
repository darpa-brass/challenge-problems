# Phase 3 Challenge Problem Ideas -- Resource DSL

## SwRI Scenario 5

### Overview and solution sketch

This scenario is about replacing a broken hardware component by finding and
configuring a different hardware component that retains as much of the original
capabilities as possible.

We can model the various components and their capabilities in our resource DSL.
Each component will have a corresponding entry in the DFU (Discrete Functional Unit)
dictionary. Capabilities will be modeled by a resource provision record that
includes the type of the capability and relevant properties (e.g. sample rate,
resolution). In prior phases, we used DFUs to model software components, but
from a resource perspective, they can be used to model hardware components in
a flight test plan.

The application model will load a sequence of components and perform basic
checks of the relevant capabilities. The components to be loaded will be
parameterized and implicitly typed by the capabilities that they should
provide. This will allow us to generate different configurations of the system
by instantiating the application model by different components.

We can also produce a variational model of the system by querying the
dictionary for relevant components and instantiating the application model by
choices of components. This allows efficiently comparing the interactions of
different sets of possible components in order to maximize the value of the
repaired system.

The mission requirements will check the relevant properties of the complete
application model and perform the valuation required to compare different
configurations. The valuation will be based on the value of missions that can
be performed with the repaired system.

When a component breaks, a variational model of the system will be produced to
analyze the possible repairs. First, the DFU dictionary will be queried to
identify candidate replacement parts. Second, the application model will be
instantiated by a choice of all of the candidates, yielding a variational model
of the system. Third, this model will be evaluated against the mission
requirements. Finally, the variational valuation will be analyzed and a
corresponding configuration extracted.


### Evaluation

In this section, we briefly describe how this challenge problem will help to
evaluate the value of our technology (the Resource DSL), and considerations for
maximizing the value of this evaluation.

The DSL helps to solve this challenge problem in two main ways:

 1. By providing a language for precisely describing:

    (a) the requirements and capabilities of components,

    (b) the integration of components into a system with its own requirements
        and capabilities, as well as dependencies between the components in
        the system, and

    (c) the suitability and value of a system for accomplishing a particular
        set of mission requirements.

 2. By enabling the description and efficient exploration and analysis of
    a large number of different configurations of a system.

The value of the Resource DSL as a specification language for practical problem
domains will be evaluated by virtue of the fact that the components and
system(s) that we describe will be based as closely as possible on the actual
components and systems provided by SwRI. Our ability to model these real
components and systems accurately will validate the expressiveness of the DSL
from a pragmatic perspective.

In order to properly evaluate the utility of the Resource DSL as an analysis
tool, it would help to have several independent dimensions of variability. The
problem as described in SwRI's initial description of Scenario 5 has just one
main dimension of variability---the component to be replaced.

The variability of the problem can be increased in two different ways: (1) if
each component is itself configurable in various ways; (2) if finding an
optimal configuration may involve replacing more than one component. As an
example of (2), suppose that we want to replace a broken part with a part that
provides the same capabilities as the broken parts, but requires also replacing
a different (non-broken) part elsewhere in the system.

Our two major technical goals of this phase are to improve the scalability of
analyses using the DSL, and to extend the analysis to support optimization
problems. This challenge problem involves optimization (to maximize the value
of missions performed with the repaired system), which is great, but we'll have
to work with SwRI to identify additional dimensions of variability in order to
properly evaluate scalability.


### Needs, Concerns, and Mitigations

This challenge problem will require working closely with SwRI to identify the
precise capabilities of the relevant components that we'll use to populate the
DFU dictionary. These capabilities are not provided in the MDL specifications
(demonstrating a need for something like our DSL) and we do not have the
relevant domain knowledge to infer them on our own.

We will also need to work with SwRI to identify additional sources of
variability, as described in the Evaluation section above.

The scenario as described by SwRI requires outputting an MDL specification of
how to configure low-level details of the component, e.g. how to connect each
pin within the larger system. This is not a very good match for our DSL.
However, generating this pin configuration might be an easy problem to solve
after we have identified a suitable component, assuming our specifications are
rich enough to ensure that the component can actually be connected within our
system. Once again, this requires talking to SwRI to understand exactly how
these pin assignments can be inferred, and how to capture the relevant
information (from the perspective of finding a suitable replacement part) in
the DSL.

### Evaluation Workflow

The Immortals team will create a REST endpoint dedicated to this scenario. The endpoint
can receive additional information related to the challenge problem, but it's
expected that most if not all of the information needed will reside in the OrientDB
instance. Hence, the endpoint acts as a trigger to provide the DAS some context
as to which aspect of its ecosystem to focus on.

At a minimum, the DAS requires the following information as input to the challenge problem:

  1. The DAU inventory, along with all relevant attributes of each DAU unit, needs to
  be known ahead of time since the resource DSL must represent this information internally
  in a suitable form for the resource DSL to reason about.
  2. The DAU unit that is targeted for replacement (this needs to be known at perturbation time).
  3. Which other components of the flight test plan (sensors, recorders, etc.) can
  be considered variable (i.e., replaceable) if doing so makes finding a suitable DAU
  possible. This information should be made available ahead of time.

The Immortals DAS will first use the resource DSL to determine a suitable DAU that
is equivalent or better than the replaced DAU which also minimizes purchase cost
and timeline cost to configure and provision the new DAU. The purchase and timeline costs
must be provided as attributes on the DAU in the inventory ahead of time.

Once the replacement DAU is determined, the DAS will transfer the port configuration
from the original DAU to the replacement. At the time of this writing, the requirements
for this task are not clear. Part of the challenge is that we don't have the rules
for which constraints must be satisfied (i.e., the requirements for the flight test, the
rules of thumb the instrument engineer is following, etc.). Also, it's not clear
which aspects of the system are fixed and which are variable. For example, the MDL specification
currently does not include flight test requirements. Should the Measurements XML element be taken
as the proxy for these requirements and held fixed? This leaves the sensors, sensor configurations
and the DAUs variable. We need some guidance/discussion here. We have also requested an end-to-end
sample (with sample data, perturbation input and expected outcome) we can use to evaluate our system.

The Immortals DAS will persist information about the replacement DAU and other components
as well as modified configuration information back to the OrientDB database for evaluation.
