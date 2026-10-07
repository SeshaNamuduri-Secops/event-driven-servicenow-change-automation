# Event-Driven ServiceNow Change Automation

An event-driven AWS integration that converts qualifying infrastructure events into governed ServiceNow Change Requests.

## Architecture

GitHub Actions / Infrastructure Event
        ↓
AWS API Gateway
        ↓
AWS Lambda
        ↓
Validation + Risk Classification + Idempotency
        ↓
AWS Secrets Manager
        ↓
ServiceNow REST API
        ↓
ServiceNow Change Request
        ↓
Amazon CloudWatch

## Technology Stack

- AWS API Gateway
- AWS Lambda
- AWS IAM
- AWS Secrets Manager
- Amazon CloudWatch
- ServiceNow REST API
- Python
- GitHub Actions

## Project Status

In development.
