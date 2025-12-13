---
title: "MASTER 25 - B2Bi Basics - Message Processing Part 6_updated_notes edit"
category: "Imported"
tags: ["imported", "docx"]
creator: "converter"
created: "2025-12-12"
description: "Imported from MASTER 25 - B2Bi Basics - Message Processing Part 6_updated_notes edit.docx"
---

**B2Bi Basics eLearning -- Message Processing Part 6**

**Slide 1: Introduction**

Welcome to Module Six: Message Processing in B2Bi.

------------------------------------------------------------------------

**Slide 2: Learning Objectives & Introduction**

In this chapter, we will review the key items and learning objectives for this module.

------------------------------------------------------------------------

**Slide 3: Message Exchange Part 1 -- Overview**

This module covers Metadata Profiles and Metadata Services.

------------------------------------------------------------------------

**Slide 4: Module Objectives**

After completing this module, you will be able to perform routing and processing based on metadata, rather than message content. The key components required are Metadata Profiles and Metadata Services.

------------------------------------------------------------------------

**Slide 5: Message Flows in B2Bi**

The diagram shows all possible message flows in B2Bi. In this module, we will focus on items 4, 5, and 6: metadata matching, metadata service execution, and subsequent steps such as outbound agreement execution and delivery to an application or partner.

------------------------------------------------------------------------

**Slide 6: Metadata Profiles & Services**

*(No notes)*

------------------------------------------------------------------------

**Slide 7: Message Processing Logic**

B2Bi can process messages using metadata or content-based criteria, such as:

- Message Handling Rules, which was covered in Message Exchange Part 3.

- Partner Services which was covered in Message Processing Part 2.

- And Metadata Services, which is covered in this chapter.

With metadata-based processing, you can perform various operations within a service, specifically a Metadata Service.\
**Example:**\
A Metadata Profile might filter files with the .zip extension, and the corresponding Metadata Service could unzip those files.

------------------------------------------------------------------------

**Slide 8: Context/Metadata-Based Processing**

To use metadata-based processing, you must configure two objects: a Metadata Service and a Metadata Profile.

- The Metadata Profile specifies the criteria for executing the service.

- The Service defines the logic to be executed.

**Tip:**\
Create the service before the profile, as the profile references the service.

**Examples:**

- A profile that filters files with the .zip extension, with a service to decompress them.

- A profile that detects inbound EDIFACT messages from a specific partner (who always adds new lines), with a service to remove those new lines before processing.

------------------------------------------------------------------------

**Slide 9: Metadata Profile Criteria**

When configuring metadata profiles, you can select criteria based on Trading or Integration engine pickup metadata.

- Trading engine criteria are standard.

- Integration engine criteria are available only if the Integration engine pickup is installed.

You can manually extend the list of criteria with custom attributes (e.g., PeSIT details).\
Attributes must be populated at runtime to match during profile selection.

**Default criteria location:**\
\$B2BI_SHARED_LOCAL/config/b2bx/server/metadata_attributes.cfg

To add new metadata, \"pesit.callerId.in\" for example, edit this file. No restart is required, just reselect the profile and reopen the criteria.

------------------------------------------------------------------------

**Slide 10: Metadata Detection -- Evaluation Order & Lookup**

In the B2Bi processing flow, pickups (trading or application) are routed to Metadata Detection, which may trigger metadata processing.\
Subsequent steps can include:

- Transfer to a partner with post-transfer.

- Detection, processing, then transfer and post-transfer.

B2Bi evaluates every message for metadata content. If a message contains an attribute matching a metadata profile, the specified processing is applied.

**Key points:**

- Metadata profiles apply to all messages matching their conditions.

- When using metadata profiles, only metadata attributes are considered---not message content.

- Matching order:

  1.  Number of criteria matched.

  2.  If equal, alphabetical order of profile name.

------------------------------------------------------------------------

**Slide 11: Managing Metadata Services**

To add a metadata service:

1.  Select \"Add a service\" and choose the initiating component (e.g., unzip functionality).

2.  Components must be created before selection.

3.  Define the service output, which can be:

    - Continue to next step (passes output to new detection).

    - Deliver to resolved partner.

    - Synchronously return output to originating party (for Web Service provider mode).

    - Deliver to application.

------------------------------------------------------------------------

**Slide 12: Managing Metadata Profiles**

After creating the metadata service, create the metadata profile:

1.  Go to \"Processing configuration\" and select \"Manage Metadata Profiles.\"

2.  Choose \"Add a metadata profile\" from related tasks.

------------------------------------------------------------------------

**Slide 13: Detection -- Metadata Attributes**

To assign selection criteria in the metadata profile:

- Click the list and browse using the drop-down menu.

- Prefixes indicate which engine (integration or trading) the metadata applies to.

------------------------------------------------------------------------

**Slide 14: Detection -- Output: Deliver to Resolved Partner**

When creating the metadata profile, select one or more metadata elements to match values.\
Possible conditions: equals, not equals, starts with, ends with, contains, matches.

If the service output is \"deliver to resolved partner,\" configure the community, partner, routing ID, and delivery exchange.

------------------------------------------------------------------------

**Slide 15: Detection -- Output: Application Delivery**

If the service output is \"deliver to application,\" you can set the originating community and routing ID.\
For PeSIT transfers, always specify the \"To\" and \"From\" PeSIT Identifiers.

------------------------------------------------------------------------

**Slide 16: Detection -- Output: Continue to Next Step**

If the service output is \"continue to next step,\" the message can undergo further detection (e.g., additional Metadata or Agreement Detection).

**Example:**\
First, detect a zip file and unzip it. Then, detect the sender (e.g., ACME), who uses EBCDIC encoding, and convert to ASCII before Agreement Detection.

------------------------------------------------------------------------

**Slide 17: Detection -- Output: Continue to Next Step (Override Document Detection)**

As an advanced option, you can assign attributes for subsequent detection using \"Override document detection.\"\
Specify values for Document Type, Format, Format Version, Recipient ID, and Sender ID as needed.

------------------------------------------------------------------------

**Slide 18: Adding Custom Metadata Attributes**

You can extend the list of metadata used in profile criteria by editing the metadata_attributes.cfg file in B2B_SHARED_LOCAL/config/b2bx/server.

**Tip:**\
Use the exact names as shown in the metadata tab in Message Tracker, and pay attention to case sensitivity.
