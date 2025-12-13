---
title: "B2Bi Basics eLearning"
category: "Imported"
tags: ["imported", "pptx", "presentation"]
creator: "converter"
created: "2025-12-12"
description: "Imported from MASTER 24 - B2Bi Basics - Message Processing Part 5_updated.pptx"
---

## Step 1: B2Bi Basics eLearning

![Slide 1](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-01.jpg)

Message Processing Part 5
B2Bi Basics

## Step 2: Learning Objectives &amp; Introduction		

![Slide 2](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-02.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 3: Message Processing Part 5 – Overview 

![Slide 3](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-03.jpg)

Items
EDI Splitting
EDI Acknowledgements
Bypass EDI Processing

## Step 4: After completing this module, you will have basic knowledge around EDI and how inbound EDI handling works in B2Bi

![Slide 4](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-04.jpg)

Module Objectives

## Step 5: Introduction to EDI Concepts &amp; Structure		

![Slide 5](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-05.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 6: EDI Concepts

![Slide 6](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-06.jpg)

Electronic Data Interchange (EDI) is a system that allows document information to be exchanged between businesses, government structures and other entities.
Developed in the United States in the mid-1960s by the Transportation Data coordination Committee (TDCC).
Since the early 1970s, some industries started to work with EDI, such as transportation, pharmaceuticals, automotive and banking. Each sector developed its own set of data elements and messages to meet its needs.
1960s
In 1975, the first TDCC standard was published.
1978 the TDCC was renamed to the Electronic Data Interchange Association (EDIA) and later became the ANSI ASC X12 group which gradually extended and replaced those formats created by the TDCC. European development of TRADACOMS, ODETTE and JEDI started around 1984.
In 1985, work started on EDIFACT (EDI for Administration, Commerce &amp; Transport), an international standard published by the predecessors of the United Nations.

## Step 7: EDI Structure

![Slide 7](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-07.jpg)

Interchange
Functional Group
Functional Group
Transaction
Transaction
Transaction
Transaction
Transaction
Transaction
Interchange
, containing:
partner’s unique identification ID data
reference number to identify the envelope
date at which the message has been sent
Functional Groups 
(not mandatory in EDIFACT), containing:
partners unique identification ID data
reference number to identify the functional groups
data information (e.g.: type of message available in the functional groups)
Transaction
, containing: 
reference numbers to identify the transaction
‘real’ business data

## Step 8: Acknowledgement – Layers Overview

![Slide 8](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-08.jpg)

Application
 Acknowledgment
(ORDERS -&gt; ORDRSP) 
(APERAK)
(850 -&gt; 855)
-----------------------
Functional (Syntax
) 
Acknowledgement
(CONTRL, 997)
-----------------------
Communication 
Acknowledgment
(protocol specific)
B2Bi
Trading Partners
Application 
Acknowledgment
(ORDERS -&gt; ORDRSP)
(APERAK)
(850 -&gt; 855)
-----------------------
Functional (Syntax
) 
Acknowledgement
(CONTRL, 997)
-----------------------
Communication 
Acknowledgment
(protocol specific)
Communication Channel

## Step 9: EDIFACT

![Slide 9](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-09.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 10: On the enveloping tab of the Outbound Agreement, you can request an Acknowledgement from the Partner.

![Slide 10](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-10.jpg)

If you Expect an acknowledgement, set the Timeout Period, which is the time that you will wait for an Acknowledgement.
When you expect an Acknowledgement, one of three things will happen.
Positive CONTRL message arrives
Negative CONTRL message arrives
No CONTRL message arrives 
with in the timeout period
The result of the Acknowledgement processing is available in the 
Message
 Log.
Acknowledgement for Outbound EDIFACT Messages

## Step 11: Request Acknowledgement EDIFACT

![Slide 11](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-11.jpg)

Timeout period
Request acknowledgement

## Step 12: When and how to generate Acknowledgements is defined on the Inbound tab of the Inbound Agreement:

![Slide 12](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-12.jpg)

Criteria
: when to create acknowledgement
Type
: Which type of Acknowledgement
Specify Delivery Exchange
Use alternate 
Delivery Partner
Use a 
Service for Acknowledgement 
processing
Agreement for enveloping 
the acknowledgement 
Acknowledgement Processing for Inbound EDIFACT Messages

## Step 13: Criteria is called 

![Slide 13](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-13.jpg)

Generate Acknowledgement Rule
.
The possible values are:
On Request 
– Create CONTRL message when requested (UNB 0029)
Always
 – Always create CONTRL message
If Error 
– Create CONTRL message if the syntax validation finds an error
Never
 – Don’t acknowledge the incoming EDIFACT Interchange
NOTE: 
Syntax validation is part of executing the map. If there is no map, only the headers will be validated.
Acknowledgement Processing for Inbound EDIFACT Messages

## Step 14: When an EDIFACT acknowledgement will be created based on the criteria, select the 

![Slide 14](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-14.jpg)

Type of CONTRL message 
from a dropdown list.
The available types are:
EANCOM D93A
EANCOM D96A
UN EDIEL Version 2
UN Version 2.x, 3 and  4
EDG@S 3.2 and 4
Acknowledgement Processing for Inbound EDIFACT Messages
Select Type of CONTRL message to generate

## Step 15: Acknowledgement Processing for Inbound EDIFACT Messages

![Slide 15](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-15.jpg)

Criteria
Use a Service
Delivery Exchange
Type
Select agreement to use for enveloping the CONTRL message
Send 997 to a different partner

## Step 16: To disable the acknowledgement processing select 

![Slide 16](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-16.jpg)

Bypass EDI processing
.
Acknowledgement Processing for Inbound EDIFACT Messages

## Step 17: Message that originates in the TE can be monitored in the Message Tracker.

![Slide 17](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-17.jpg)

For 
incoming messages
, the status is “Delivered to Processing”.
For 
outgoing messages
, the status is “Delivered”.
Monitor Acknowledgements
Monitoring in the Message Tracker, Outbound EDIFACT
CONTRL from Trading Partner
INVOIC to Trading Partner
XML form Backend

## Step 18: Missing CONTRL

![Slide 18](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-18.jpg)

Monitor Acknowledgements

## Step 19: Monitor Acknowledgements

![Slide 19](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-19.jpg)

   Monitoring in the Message Tracker, Inbound EDIFACT.
INVOIC from Partner
CONTRL to Partner
In-house to Backend

## Step 20: In the Message Log there is detailed tracking of the Hierarchy of each message. 

![Slide 20](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-20.jpg)

You can see the 
incoming message
, the resulting 
outgoing message
, the 
Acknowledgement
, and all the 
intermediate messages
.
Monitor Acknowledgements
Monitor in the Message Log

## Step 21: For outbound EDIFACT, the Interchange and the Documents remain in 

![Slide 21](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-21.jpg)

Active
 state 
until B2Bi receives the acknowledgement
.
If the acknowledgement does not arrive within the configured timeout period. The Interchange and the Documents event change severity to 
ERROR
.
Monitor Acknowledgements
Monitor in the Message Log

## Step 22: Related Documents or Transactions sets from the same Interchange can be rejected based on several criteria:

![Slide 22](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-22.jpg)

None
 – Don’t reject any correct Documents or Transaction sets
If any document is stopped, 
reject entire Interchange
.
If any document is stopped, 
reject messages of the same type
.
If any document is stopped, 
reject specific type of messages
. 
These message types may be added in a comma separated list in the “Custom rules” field.
The 
Rejection rule influences the acknowledgement generation
.
Rejection Rules
Reject related Documents/Transaction sets

## Step 23: X12

![Slide 23](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-23.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 24: In case an acknowledgement is expected:

![Slide 24](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-24.jpg)

On the enveloping tab of the Outbound Agreement, you can set the Timeout Period, which is the time that you will wait for an Acknowledgement.
When you expect an Acknowledgement, one of three things will happen:
Positive 997 message arrives
Negative 997 message arrives
No 997 message arrives 
within the timeout period
The result of the Acknowledgement processing is available in the 
Message Log
.
Acknowledgements for Outbound X12 Messages

## Step 25: Request Acknowledgement 

![Slide 25](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-25.jpg)

X12
Timeout period
Expect acknowledgement (997). You can’t request acks in X12.

## Step 26: When and how to generate Acknowledgements is defined on the Inbound tab of the Inbound Agreement:

![Slide 26](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-26.jpg)

Rule
: Yes, No, Detail level
Use input 
Interchange for Identifiers
Specify Delivery Exchange
Use alternate Delivery Partner
Use a Service for Acknowledgement 
processing
Agreement for enveloping 
the acknowledgement 
Acknowledgement Processing for Inbound X12 Messages

## Step 27: Criteria is called Generate Acknowledgement Rule.

![Slide 27](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-27.jpg)

The possible values are:
No
 - Don’t generate a Functional Acknowledgement
Yes, detailed 
- Generate a detailed Acknowledgement
Yes, non-detailed 
- Generate a summary Acknowledgement
NOTE:
 Syntax validation is part of executing the map. If there is no map, only the headers ISA-IEA, GS-GE will be validated.
Acknowledgement Generation for X12

## Step 28: Acknowledgement Generation for X12

![Slide 28](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-28.jpg)

Use Inbound identifiers
The Identifiers in the X12 Headers in the Inbound Envelope will be used when enveloping the acknowledgement.
Use Outbound agreement
Specify an outbound agreement used for enveloping of the Acknowledgement.

## Step 29: Acknowledgement Processing for Inbound X12 Messages

![Slide 29](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-29.jpg)

Re-use the identifiers from the Inbound Interchange when enveloping the 997
Send 997 to a different partner
Select agreement to use for enveloping of the 997
Delivery Exchange
Use a Service
Rule

## Step 30: To disable the acknowledgement processing select 

![Slide 30](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-30.jpg)

Bypass EDI processing.
Acknowledgement Processing for Inbound X12 Messages

## Step 31: Message that originates in the TE can be monitored in the Message Tracker.

![Slide 31](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-31.jpg)

For 
incoming messages
,
 
the status is “Delivered to Processing”.
For the 
outgoing messages
,
 
the status is “Delivered”.
Monitor Acknowledgements
Monitoring in the Message Tracker, Outbound X12
In-house from Backend
X12 850 to Trading Partner
X12 997 from Trading Partner

## Step 32: Missing Acknowledgement

![Slide 32](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-32.jpg)

Monitor Acknowledgements

## Step 33: Monitor Acknowledgements

![Slide 33](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-33.jpg)

   Monitoring in the Message Tracker, Outbound X12.
X12 850 from Partner
997 to Partner
In-house to Backend

## Step 34: In the Message Log there is detailed tracking of the Hierarchy of each message. You can see the 

![Slide 34](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-34.jpg)

Incoming message
, the resulting 
outgoing message
, the 
Acknowledgement
, and all the 
intermediate messages
.
Monitor Acknowledgements

## Step 35: For outbound X12, the Transaction Sets and the Functional Group remains in 

![Slide 35](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-35.jpg)

Active
 state 
until B2Bi receives the acknowledgement
.
If the acknowledgement does not arrive within the configured timeout period, the Transaction Sets and the Functional Group event change severity to 
ERROR
.
Monitor Acknowledgements

## Step 36: Related Documents or Transactions sets from the same Interchange can be rejected based on several criteria:

![Slide 36](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-36.jpg)

None
 – Don’t reject any correct Documents or Transaction sets
If any document is stopped, 
reject entire Interchange
.
If any document is stopped, r
eject messages of the same type
.
If any document is stopped, 
reject specific type of messages
. 
These message types are a comma separated “Custom rules field.
The Rejection rules influences the acknowledgement generation. 
Rejection Rules
Reject related Documents/Transaction sets

## Step 37: EDI Splitting

![Slide 37](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-37.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 38: EDI Structure

![Slide 38](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-38.jpg)

Interchange
, containing:
partner’s unique identification ID data
reference number to identify the envelope
date at which the message has been sent
Interchange
Functional Group
Functional Group
Transaction
Transaction
Transaction
Transaction
Transaction
Transaction
Functional Groups 
(not mandatory in EDIFACT), containing:
partners unique identification ID data
reference number to identify the functional groups
data information (e.g.: type of message available in the functional groups)
Transaction
, containing: 
reference numbers to identify the transaction
‘real’ business data

## Step 39: As part of the processing in B2Bi, EDI files are being split into Interchanges, Functional Groups and Transactions Sets.

![Slide 39](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-39.jpg)

This split logic is completely automatic and hidden for the user – the only thing the user has to worry about is the specific processing settings (parameters) that need to apply for a certain partner / set of partners.
EDI Splitting

## Step 40: Bypass EDI Processing

![Slide 40](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-40.jpg)

B2Bi Basics: Message Processing Part 5
B2Bi Basics

## Step 41: For both EDIFACT and X12, there is the option in B2Bi to bypass the standard  EDI processing – this can be set in the “inbound tab” of the Inbound Agreement.

![Slide 41](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-41.jpg)

If selected, 
EDI structures are handled as “non-EDI”
.
This implies that the 
message will not be split but sent as a whole
 through the service (including the envelope).
As only the beginning of the file is scanned for pattern recognition– if more than one transaction set type is sent in a single envelope, only that first type will be recognized.
No acknowledgement (997/CONTRL) will be generated.
Bypass EDI Processing

## Step 42: 

![Slide 42](master-24-b2bi-basics-message-processing-part-5-updated/images/slide-42.jpg)


