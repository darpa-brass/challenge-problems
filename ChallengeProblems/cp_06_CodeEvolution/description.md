# IMMoRTALS Phase III Challenge Problem (CP) - Schema Evolution (DRAFT)

- - - -
## CP1: Adapting software systems to schema changes
Authored by
<span style="color:blue">Jacob Staples (*jstaples@securboration.com*)</span> and
<span style="color:green">Fred Eisele (*fred.eisele@vanderbilt.edu*)</span>.

### Challenge problem objective
CP1 will demonstrate the ability to preserve application intent when assumptions made by application developers about schema compliance are violated, even when those assumptions are baked-in to application code.

We will demonstrate that IMMoRTALS can adapt software systems to nontrivial schema changes without post-compilation human intervention.  The goal is to demonstrate breadth (the ability to handle different types of schema changes) and depth (the ability to handle increasingly complex schema changes of a single type) within this adaptation space.


### Motivation
CP1 is motivated by SwRI's Phase 3 Scenario 6 (schema evolution).

A *schema* describes the structure, organization, and presentation of data.  Schemas may evolve unpredictably over time to accommodate changes in the data they describe and the emergence of new use cases for that data.  This dynamism can unintentionally obsolete software systems that are not manually updated accordingly.  Although knowledgeable human operators may be able to define transformations sufficient to preserve otherwise obsolete functionality, these are one-off fixes made at great expense.  Schema evolution therefore artificially limits the effective lifespan of software.  New techniques and technologies are needed to autonomically adapt software in a manner that preserves the intent of the application while accounting for the structural and semantic discrepancies that differentiate schema versions.

The Metadata Description Language (MDL) is an XML Schema created by the MetaData Standards Working Group (MDSWG) that describes ["...requirements, design choices, and configuration information for Telementry Network Systems (TmNS)."](https://pdfs.semanticscholar.org/beaa/a03a0b38d1a74072b33f07d29aadb2756829.pdf).  MDL has changed in recent years.  For example, MDL version 0.8.17 defines 277 types (212 complex and 65 simple) whereas MDL version 0.8.19 defines 298 types (230 complex and 68 simple).  Some of these changes are simple (e.g., 0.8.19 uses bits as the primary unit of data transfer whereas 0.8.17 can use either bits or bytes).  Others require complex handling (e.g., 0.8.19 added time as a measurement type and added parent/child relationships to network nodes).  The difficulty of translating documents from 0.8.17 to 0.8.19 is evidenced by the complexity of the Extensible Stylesheet Language Transformations (XSLT) needed to perform the translation correctly (over 2600 lines).

As another example, consider the [Financial products Markup Language (FpML)](http://www.fpml.org/), an open-source XML Schema maintained by the International Swaps and Derivatives Association (ISDA) that defines (1) a vocabulary for financial derivatives and (2) protocols for transactions involving these derivatives.  The FpML standard is used by software at many of the largest banks in the United States including JPMorgan, Goldman Sachs, Bank of America, and Citibank.  FpML has undergone a number of significant changes that have necessitated software rewriting during its nearly 20-year lifespan (the recommended version as of February 2018 is [5.10](http://www.fpml.org/spec/fpml-5-10-5-rec-1/#changes)).  IMMoRTALS could drastically reduce the cost of such software rewriting by performing the bulk of the work automatically.


### Perturbation and evaluation
SwRI will perform multiple *CP evaluation runs*, each of which explores the adaptation capabilities of IMMoRTALS for a configurable *exemplar software system*.  Each evaluation run will result in the production of a performer-generated *evalation score* that determines how well application intent is preserved after transformation.  Our goal in defining the CP is to provide enough degrees of freedom to make this exploratory evaluation an interesting and meaningful task.

#### Exemplar software system
The exemplar software system is a client/server architecture in which a client (called messageSenderApp) transmits message to a server (called messageListenerApp) which then performs some action and returns a response message.  MessageSenderApp represents the software component to be adapted and messageListenerApp represents the component providing evolutionary pressure.  

Both messageSenderApp and messageListenerApp utilize code units synthesized at design time from a Web Service Definition Language (WSDL) document that describes the datatypes and messages to be communicated between components in terms of an XML schema.  This is typically achieved using a SOAP/XML framework such as [Axis](http://axis.apache.org/axis2/java/core/).  Specifically, messageSenderApp developers use synthesized code units that allow them to programmatically invoke functionality on the server without worrying about the banalities associated with correctly writing Java constructs to XML data and then managing their transmission across a TCP connection.  Similarly, messageListenerApp developers utilize synthesized code units that convert incoming XML messages received from a TCP connection into Java constructs and passes these along to developer-created application business logic.  

Note that all software modules used in the CP architecture will be implemented in languages that compile into JVM Bytecode--most notably this includes Java but also Groovy, Scala, and Kotlin among others.  Note also that the client(s) and server will communicate via a plaintext TCP channel that allows in-flight messages to be readily monitored.  


#### Evolutionary pressure
The scenario to be explored is one in which a messageListenerApp (a server) is upgraded to use a newer schema version, degrading the functionality of legacy messageSenderApp systems that attempt to communicate using the old schema version.

Documents received by messageListenerApp that do not conform to the WSDL schemas will result in runtime XML validation errors within that component.  From the point of view of the messageSenderApp, these errors will manifest as remote endpoint exception responses that degrade its functionality (since its correct operation depends upon non-exceptional messages returned by the server).  Note that these errors do not indicate incorrect behavior in messageListenerApp, which assumes schema compliance and is therefore correct in generating error messages when nonconformant data is encountered.  

Evolutionary pressure in our exemplar software system will arise as SwRI adjusts the schema compliance of messageListenerApp between three MDL schema versions named `v1`, `v2`, and `v3`.  Adaptation will be required to maintain messageSenderApp functionality when interacting with a `v2` or `v3` messageListenerApp but not when interacting with a `v1` messageListenerApp.

#### Adaptation
Our system will:
  1) construct a control flow graph (CFG) of the software system to be analyzed
  2) construct a dataflow graph (DFG) of the software system by traversing edges of the CFG from (1) determined through static and dynamic analysis to be viable
  3) identify dataflow edges from (2) by which the software system consumes or emits data assumed to be conformant to some specific version of a schema
  4) identify mismatches between the expected and actual schema version along the schema-dependent edges from (3)
  5) identify code units (DFUs) capable of addressing the schema mismatch from (4) (XSLT transformer libraries such as Saxon)
  6) identify that a selected XML translation DFU requires an Extensible Stylesheet Language Template (XSLT) input that translates document instances from vExpected of the schema into vNeeded of the schema
  7) request an appropriate XSLT be synthesized from a tool that operates over the expected and actual schema versions (see CP2 TODO)
  8) inject properly configured XSLT transformer DFU(s) into the application such that all problematic dataflow edges from (4) are handled
  9) after modification, test the application for consistency and correctness (using automated unit/validation/integration tests)


#### Challenge problem inputs/outputs


##### We provide
  * We will provide an evaluation API by which SwRI can convey configuration, trigger evaluation runs, and retrieve run results
  * We will select three versions of MDL (TBD), named `v1`, `v2`, and `v3`.
  * We will provide all code for our simple messageSenderApp/messageListenerApp architecture.  We will provide a single initial client module compliant with schema `v1` and three server modules compliant with `v1`, `v2`, and `v3`.  

##### SwRI will provide
  * `receiver_schema_version`: the version of schema used by the messageListenerApp module, which operates in a manner that assumes all documents transmitted to and received from client(s) are conformant with this version.  One of {`v1`, `v2`, `v3`}.
  * `evaluation stimuli`: SwRI will invoke the evaluation API to trigger analysis and adaptation.

#### Interaction during evaluation
Each CP evaluation run involves the following activities:
  * Configuration: SwRI will define the configuration of the software system to be evaluated
  * Control experiment: SwRI will invoke an `evaluate(adapt=false)` API method which will return an evaluation score after deploying the architecture with the configuration specified but *without performing adaptation*.  If the configuration specified is problematic, the evaluation score returned will be less than 1 (fully functional system) and greater than or equal to 0 (completely dysfunctional system).
  * Adaptation experiment: SwRI will invoke an `evaluate(adapt=true)` API method which returns an evaluation score after deploying the architecture with the configuration specified and *after performing adaptation*.  If the configuration specified is problematic, the evaluation score returned should be greater than the value returned during the control experiment and would ideally be 1 (fully functional system).

### Evaluation risks and mitigations

We have identified the following risks and propose mitigation strategies for each:

  * *Risk*: Our analysis and discovery techniques are engineered toward the JVM and its ecosystem--there is risk that software developed for other languages or environments will require wasteful re-engineering of existing tools.  *Mitigation*: We will provide to SwRI the software modules to use during evaluation that are guaranteed to conform to our language and build tool assumptions.
  * *Risk*: Schema migration via translation is not a generally solvable problem--there are many migrations that cannot be solved using translation (e.g., an entirely new field is required in schemaV1-compliant documents that did not exist in and cannot be derived from schemaV0-compliant documents).  *Mitigation*: We will provide three schema versions--`v1`, `v2`, and `v3`--that explore a spectrum of migration difficulty (rather than attacking only the hardest problem).  The `v1` to `v2` migration problem will be solvable entirely using translation.  The `v2` to `v3`  migration problem will be *mostly* solvable using translation but certain types of documents will require additional information that is nontrivially derivable from the source document (e.g., converting between AGL and MSL/HEL altitude).  The `v2` to `v3` migration problem will therefore not be entirely solved by an XSLT but may also require business logic changes (e.g., the use of a library that converts between altitude measurement types).
  * *Risk*: Evaluation is entirely dependent upon scores returned by the performer--independent measurements should be made to validate the approaches taken.  *Mitigation*: All communication within the exemplar software system is performed using plaintext TCP channels that can be easily intercepted on a loopback adapter and subsequently examined by a third party without invasive code instrumentation.  Additionally, SwRI is given control of the actual documents to be transmitted from client(s) to server (this is one of the configuration inputs for a test run).
