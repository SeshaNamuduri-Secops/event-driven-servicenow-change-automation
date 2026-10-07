# Event-Driven ServiceNow Change Automation

An event-driven AWS integration that automatically converts qualifying infrastructure events into governed ServiceNow Change Requests.

The project demonstrates how AWS serverless services can integrate with ServiceNow ITSM to validate infrastructure events, classify change risk, prevent duplicate Change Requests, securely retrieve integration credentials, and create ServiceNow Change Requests through the REST API.

---

## Architecture

```text
Infrastructure Event / HTTP Request
                |
                v
       Amazon API Gateway
                |
                v
        AWS Lambda (Python)
                |
        +-------+-------+
        |       |       |
        v       v       v
    Validation  Risk   Duplicate
               Classification  Detection
                |
                v
       AWS Secrets Manager
                |
                v
       ServiceNow REST API
                |
                v
      ServiceNow Change Request
                |
                v
          CloudWatch Logs
Problem Statement
Infrastructure and application changes often require corresponding ITSM Change Requests for governance, traceability, and operational control.
Manually creating these Change Requests from infrastructure events can introduce delays, inconsistent information, and duplicate records.
This project demonstrates an automated integration where an infrastructure event is validated and evaluated before a ServiceNow Change Request is created.
Key Features
1. Event Validation
The Lambda function validates incoming events and checks for required fields:
- event_id
- source
- environment
- change_type
- short_description
- description
Invalid events are rejected with an HTTP 400 response.
2. Risk Classification
The function determines a risk level based on the environment and change type.
Example logic:
Condition	Risk Level	Recommended Type
Emergency / Critical change	Critical	Emergency
Production change	High	Normal
Staging / UAT / Pre-production	Medium	Normal
Other environments	Low	Standard


3. Duplicate Event Detection
Each event uses a unique event_id.
Before creating a new Change Request, Lambda queries ServiceNow using the event's correlation ID.
If the event has already been processed, the existing Change Request is returned instead of creating a duplicate.
4. Secure Credential Management
ServiceNow credentials are not hardcoded in the Lambda source code.
The Lambda retrieves the credentials from:
AWS Secrets Manager
The Lambda execution role is granted permission to read the required secret.
5. ServiceNow Integration
The integration uses the ServiceNow Table API to create Change Requests containing:
- Short description
- Description
- Comments
- Correlation ID
- Infrastructure source
- Environment
- Risk classification
- Recommended change type
Technology Stack
- AWS Lambda
- Amazon API Gateway
- AWS IAM
- AWS Secrets Manager
- Amazon CloudWatch
- ServiceNow REST API
- Python 3.14
- Git
- GitHub
Example Event
{
  "event_id": "portfolio-test-001",
  "source": "AWS Infrastructure",
  "environment": "production",
  "change_type": "infrastructure",
  "short_description": "Automated infrastructure change",
  "description": "Infrastructure event requiring ITSM change governance."
}

Validation Example
When required fields are missing, the Lambda rejects the request.
Example response:
{
  "error": "Missing required fields: environment, change_type, short_description, description"
}

This prevents incomplete events from reaching ServiceNow.
Duplicate Protection Example
The same event was submitted twice using:
event_id = duplicate-test-001

First request:
{
  "change_number": "CHG0030006",
  "duplicate": false
}

Repeated request:
{
  "message": "Duplicate event detected; existing Change Request returned",
  "change_number": "CHG0030006",
  "duplicate": true
}

This demonstrates idempotent event processing.
ServiceNow Evidence
The implementation generated and verified ServiceNow Change Requests during testing.
Change Request	Purpose
CHG0030003	Initial Lambda → ServiceNow integration
CHG0030004	API Gateway → Lambda → ServiceNow integration test
CHG0030005	Validation and risk classification
CHG0030006	Duplicate event protection


Screenshots documenting the implementation and testing are available in:
documentation/screenshots/

Testing
The implementation was tested for:
- Successful ServiceNow Change Request creation
- Required-field validation
- Risk classification
- Duplicate event detection
- ServiceNow API authentication
- Secrets Manager credential retrieval
- API Gateway integration
- Lambda execution
Security Design
The project follows basic cloud security principles:
ServiceNow Credentials
        |
        v
AWS Secrets Manager
        |
        v
Lambda Execution Role
        |
        v
Secrets Manager Read Access

No ServiceNow passwords or AWS credentials are stored in the source code.
The repository .gitignore excludes:
- .env files
- AWS credential directories
- secrets directories
- Terraform state
- Terraform variable files
- operating-system metadata
Repository Structure
event-driven-servicenow-change-automation/
│
├── lambda/
│   └── handler.py
│
├── documentation/
│   └── screenshots/
│       ├── 01-aws-cli-authenticated.png
│       ├── 02-iam-project-user-created.png
│       ├── 03-iam-access-key-created.png
│       ├── 04-api-gateway-end-to-end-success.png
│       ├── 05-servicenow-change-created-via-api.png
│       ├── 06-risk-classification-success.png
│       ├── 07-validation-test-success.png
│       ├── 08-duplicate-protection-success.png
│       └── 09-final-evidence.png
│
├── requirements.txt
├── .gitignore
└── README.md

Known Limitation
The current Lambda handler expects the event payload in direct event-field format.
The upgraded handler does not yet normalize the JSON payload from the API Gateway HTTP API body wrapper.
Direct Lambda execution and the earlier API Gateway integration test were successfully demonstrated. Payload normalization for the upgraded handler is a planned enhancement.
Future Enhancements
Potential improvements include:
- API Gateway request-schema validation
- API Gateway body normalization
- Automated deployment using CI/CD
- Infrastructure as Code using Terraform or CloudFormation
- ServiceNow approval workflow integration
- Additional change-risk policies
- CloudWatch alarms and operational dashboards
- Automated test execution in CI/CD
Project Outcome
This project demonstrates a practical integration between AWS serverless infrastructure and ServiceNow ITSM.
It combines:
Event-driven architecture + serverless computing + ITSM automation + risk classification + idempotency + secure credential management
to provide a foundation for automated infrastructure-to-ITSM change governance.
Author
Sesha Namuduri
Cloud / IT Operations / ServiceNow Portfolio Project
