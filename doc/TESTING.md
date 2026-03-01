# Quality Assurance & Testing Strategy (TESTING.md)

## 1. Introduction and Objectives

This document outlines the quality assurance and testing strategy for the **Aether** project. As Aether is a highly sensitive communication platform whose primary goal is the strict avoidance of metadata and IP leaks, our quality assurance efforts are heavily focused on the principle of **Security by Design**.

## 2. Testing Strategy and Test Levels

We pursue a risk-based testing approach, divided into several levels to balance between execution speed and system coverage.

### 2.1 Unit Tests (Focus: High)

Unit tests form the foundation of our quality assurance, testing isolated components without external dependencies.

* **Backend (Python/Flask):** We use `pytest` for testing the middleware and cryptography modules. The focus is on verifying encryption and decryption routines, as well as the correct processing of SQLite database operations.
* **Frontend (JavaScript/Electron):** We use `Jest` for testing the frontend logic and state management, independent of the user interface and inter-process communication (IPC).

### 2.2 Integration Tests (Focus: Medium)

Integration tests verify the interaction between individual modules.

* **Backend & Database:** Verifying that the Flask REST API correctly writes data to and reads data from the SQLite database.
* **Tor Network Mocks:** Since real Tor connections are too unstable and slow for automated CI/CD pipelines, we use **pure software mocks** within the Python code to simulate the Tor daemon. This allows us to deterministically test the application's behavior under simulated latencies and network conditions.

### 2.3 System & UI Tests (Focus: Selective)

* **Frontend E2E:** We rely on **manual end-to-end (E2E) testing** for the Electron app. These manual test cycles ensure that user interactions in the GUI (e.g., adding a contact, initiating a call) trigger the correct API calls to the middleware and that the overall user experience meets our quality standards.

## 3. Security-Critical and Complex Test Cases

To address Aether's specific architectural risks, the following mission-critical test cases have been defined and must be verified with every code change:

* **Test Case 1: Zero IP Leaks (NFR-01)**
  * *Description:* An integration test mocks the network module and blocks the SOCKS5 proxy.
  * *Expected Behavior:* The application strictly applies the fail-closed principle. The system must actively block any outgoing request that attempts to bypass the SOCKS5 proxy. This ensures that no fallback to direct HTTP/UDP requests (clearnet) is possible, thereby protecting the user's identity.
* **Test Case 2: Tor Latency and Queuing (FR-06 & NFR-08)**
  * *Description:* Using software mocks, extreme network latency (> 2000ms) and a temporary connection drop to the remote peer are simulated.
  * *Expected Behavior:* Outgoing messages are not discarded but marked as "Queued" in the local SQLite database. They are automatically resent as soon as the Tor mock signals reachability again.
* **Test Case 3: Post-Compromise Security Handshake (FR-04)**
  * *Description:* Simulation of a connection establishment between two peers for cryptographic key generation.
  * *Expected Behavior:* Verification that temporary session keys are generated for each new session and are securely wiped from memory immediately after the session concludes (Perfect Forward Secrecy).
* **Test Case 4: Data-at-Rest Encryption (NFR-04)**
  * *Description:* The backend tests initialize a temporary SQLite database.
  * *Expected Behavior:* The test verifies at the file-system level that the generated `.db` file cannot be read without the correct symmetric key (AES-256).

## 4. CI/CD Pipeline and DevOps

Our Continuous Integration pipeline is automated via **GitHub Actions** and runs on every push to a feature branch as well as on every Pull Request.

### Pipeline Flow & Tools

1. **Linting & Formatting:** Code inspection using `Pylint` (Python), alongside `ESLint` and `Prettier` (JS).
2. **Security Scans (SonarQube):** All code is analyzed by SonarQube to detect static security vulnerabilities, hardcoded secrets, or code smells early in the development lifecycle.
3. **Automated Testing:** Execution of all `pytest` and `Jest` test suites.

### Quality Gates

A Pull Request can only be merged into the `main` branch if the following conditions are met:

* **Code Coverage:** The test coverage measured by `pytest-cov` must be at least **70%**.
* **Security:** SonarQube reports **0 critical and 0 high vulnerabilities**.
* **Four-Eyes Principle:** At least one other developer has reviewed and approved the code.

## 5. Instructions for Local Test Execution

Before code is committed, all tests must run successfully in the local development environment.

**Prerequisites:** Python 3.x, Node.js, and an active Virtual Environment (`venv`).

* **Run Backend Tests (Python):**

  ```bash
  # In the project root directory
  pytest
  ```

* **Generate Backend Coverage Report:**

  ```bash
  # Checks if the 70% Quality Gate is met
  pytest --cov=src --cov-report=term-missing
  ```

* **Run Frontend Tests (JavaScript/Electron):**

  ```bash
  # Inside the /src-frontend directory
  npm run test
  ```

## 6. Quality Assurance and Bug Tracking

Our team places great emphasis on systematic bug resolution to prevent technical debt.

* **Issue Tracking:** Every identified bug must be logged as a GitHub Issue with the `bug` label.
* **Report Structure:** A valid bug report mandatorily includes:
  1. *Steps to reproduce*
  2. *Expected behavior*
  3. *Actual behavior*
* **Regression Testing:** When a bug is fixed (using the branch prefix `bugfix/`), an accompanying unit or integration test **must** be written. This test ensures that the exact same error will be immediately caught by the CI/CD pipeline if the code is altered again in the future.
