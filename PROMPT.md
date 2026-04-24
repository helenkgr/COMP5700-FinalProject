# Prompts Used for KDE Extraction

## Zero-Shot

You are a security requirements analyst.

Read the following security requirements document and identify all Key Data Elements (KDEs).
For each KDE, provide its name and list the specific requirements associated with it.

Respond ONLY in the following YAML format and nothing else:
element1:
  name: <element name>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <element name>
  requirements:
    - <requirement 1>

Document:
{document_text}

YAML Output:

## Few-Shot

You are a security requirements analyst.

Read the following security requirements document and identify all Key Data Elements (KDEs).
For each KDE, provide its name and list the specific requirements associated with it.

Here are two examples of the expected output format:

Example 1:
element1:
  name: User Authentication
  requirements:
    - All users must authenticate using multi-factor authentication
    - Passwords must be at least 12 characters long
    - Sessions must expire after 30 minutes of inactivity

Example 2:
element1:
  name: Data Encryption
  requirements:
    - All data at rest must be encrypted using AES-256
    - All data in transit must use TLS 1.2 or higher
element2:
  name: Access Control
  requirements:
    - Role-based access control must be enforced
    - Least privilege principle must be applied to all accounts

Now extract KDEs from this document in the same format:

Document:
{document_text}

YAML Output:

## Chain-of-Thought

You are a security requirements analyst.

Follow these steps to extract Key Data Elements (KDEs) from the document below:

Step 1: Read the entire document carefully.
Step 2: Identify distinct security topics or data categories mentioned.
Step 3: For each topic, list the specific requirements or rules associated with it.
Step 4: Label each topic as a Key Data Element (KDE).
Step 5: Format your findings in YAML as shown below.

Output format:
element1:
  name: <element name>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <element name>
  requirements:
    - <requirement 1>

Document:
{document_text}

Now follow Steps 1-5 and produce the YAML output: