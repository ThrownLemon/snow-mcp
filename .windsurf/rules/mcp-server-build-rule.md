---
trigger: always_on
---

Rule number 1: THIS IS VERY IMPORTANT!!! I will follow the build-test-workflow.md workflow whenever we need to build and run the MCP server after making code changes.

AI Coding Agent Guidelines for Building MCP Integration with ServiceNow (Key Points)
1. Clarify Purpose and Context:
The MCP (Message Consumer and Processor) server integration facilitates secure, efficient, fault-tolerant communication between ServiceNow and MID servers, optimizing message consumption and processing to support incident, task, and external interactions.
2. Coding Best Practices:
Write clearly structured, readable, modular, well-commented code.
Favor small functions and reusable components.
Use clean naming conventions consistently.
Include organized code documentation and comments explaining logic.
3. Robust Architectural Design:
Clearly separate "Listener," "Queue management," "Consumer Workers/Processor," and "ServiceNow API integration."
Ensure modular design where each component has a clearly defined single responsibility.
Prefer REST-based APIs and HTTPS/TLS secured communication.
4. Message Queueing and Handling:
Use reliable MQ solutions (e.g., RabbitMQ, Kafka, AWS SQS) or ServiceNow built-ins as required.
Ensure fault tolerance: message queues with durable messages, acknowledgment mechanisms, retry strategies, and dead-letter queues (DLQs).
5. ServiceNow API Integration:
Interact strictly through authorized ServiceNow REST APIs (e.g., Table API, Web Services, Scripted REST APIs).
Implement retry logic with exponential backoff, rate-limiting compliance, pagination optimization, and authentication refreshing.
6. Security and Compliance:
Follow OWASP best practices.
Secure all communication via HTTPS/TLS.
Store sensitive credentials safely (ServiceNow Credential Stores, Azure Key Vault, AWS Secrets Manager, or Vault).
Implement strong authentication/token validation mechanisms before processing requests.
7. Scalability and Performance:
Implement asynchronous task handling, threading, or worker pools.
Optimize all interactions: batch requests, caching, and efficient data processing methods.
Clearly define target scalability metrics (e.g., requests per second) and optimize accordingly.
8. Error Handling & Resiliency:
Clearly handle expected ServiceNow-related and network/timeout errors gracefully.
Log structured, context-rich errors using clearly identifiable tracing IDs.
Include retry patterns, circuit-breaker logic, or graceful degradation approaches when ServiceNow or queues are unreachable.
9. Automated Testing & QA:
Provide comprehensive and automated unit tests, integration tests, and maintain a coverage metric (75-90% recommended).
Utilize CI/CD automation to validate code frequently.
10. Documentation & Knowledge Sharing:
Short, structured installation/readme documentation.
Include troubleshooting steps, deployment tips, and API interaction guidelines clearly outlined.
Update documentation regularly alongside codebase.
11. Use of IDE and Agent Optimization:
Leverage IDE-integrated AI code-assistants/snippets for repetitive structures, formatting, linting, and security checking.
Provide clear IDE debugging configurations (launch,json, test runners, and log analyzers).

