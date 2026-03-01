# Contributing to Aether

First off, thank you for contributing to Aether!

Aether is a highly security-sensitive project. Our primary goal is to provide a fully decentralized, metadata-free peer-to-peer communication platform over the Tor network. Because a single IP leak or cryptographic flaw can compromise the physical safety of our users, we adhere to strict "Security by Design" principles.

This document outlines our development methodology, coding conventions, and contribution workflows to ensure we maintain the highest standards of code quality and security.

---

## 1. Branching Strategy & Workflow

We follow a **Feature Branch Workflow** based on Trunk-Based Development. The `main` branch is protected and must always be in a deployable, stable state.

### 1.1 Branch Naming Conventions

Always branch off from `main`. Use the following naming convention for your branches:

* `feature/<issue-number>-<short-description>` (e.g., `feature/12-implement-tor-bootstrap`)
* `bugfix/<issue-number>-<short-description>` (e.g., `bugfix/34-fix-sqlite-lock`)
* `docs/<short-description>` (e.g., `docs/update-architecture-diagram`)
* `refactor/<short-description>` (e.g., `refactor/api-response-models`)

### 1.2 Pull Request (PR) Process

Direct pushes to `main` are strictly forbidden. All changes must be merged via Pull Requests.

1. **Four-Eyes Principle:** Every PR requires at least one approving review from another team member before it can be merged. This is critical for catching potential security flaws.
2. **CI/CD Checks:** The GitHub Actions pipeline must pass completely (linters, unit tests, and security scans) before merging.
3. **PR Description:** Clearly describe *what* was changed, *why* it was changed, and mention any related Issue numbers (e.g., "Resolves #12").

---

## 2. Commit Message Conventions

We strictly follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This ensures a readable project history and enables automated changelog generation.

**Format:**
`<type>(<scope>): <subject>`

**Allowed Types:**

* `feat`: A new feature
* `fix`: A bug fix
* `docs`: Documentation only changes
* `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `test`: Adding missing tests or correcting existing tests
* `chore`: Changes to the build process or auxiliary tools

**Examples:**

* `feat(tor): integrate stem library for hidden service bootstrapping`
* `fix(api): sanitize user input in contact creation endpoint`
* `docs(readme): add local setup instructions for python virtual environment`

---

## 3. Coding Conventions & Clean Code

To satisfy our high code quality requirements, all code must be written in **English** (variables, methods, comments) and adhere to the following standards.

### 3.1 Python (Backend, Controller, REST API)

* **Standard:** Adhere to [PEP 8](https://peps.python.org/pep-0008/).
* **Formatter:** Use `Black` (line length: 88 characters).
* **Linter:** Use `Flake8` or `Pylint` to catch logical errors and enforce style.
* **Typing:** Use Python Type Hinting (e.g., `def get_contact(onion_address: str) -> dict:`) extensively to make the code self-documenting and prevent runtime type errors.
* **API Design:** The Flask REST API must use clear, resource-oriented endpoint naming (e.g., `GET /api/v1/contacts`) and always return proper HTTP status codes.

### 3.2 JavaScript / UI (Electron Frontend)

* **Formatter:** Use `Prettier` for consistent code formatting.
* **Linter:** Use `ESLint` to catch potential JavaScript pitfalls.
* **Modularity:** Keep UI components decoupled from the IPC (Inter-Process Communication) and API calling logic.

### 3.3 Documentation and Comments

* **Self-Documenting Code:** Choose descriptive variable and function names (e.g., `initialize_tor_daemon()` instead of `init_td()`).
* **Why over What:** Comments should explain *why* a specific approach was taken, especially concerning complex cryptographic implementations, Tor latency workarounds, or specific security trade-offs.

---

## 4. Security & Privacy Guidelines (Important)

All code must be evaluated against our threat model.

1. **Zero IP Leaks:** The Electron frontend and Python backend **must never** make direct external HTTP requests to the public internet. All external communication must be routed exclusively through the local Tor SOCKS5 proxy.
2. **Data Minimization & Logging:** Never log sensitive information (e.g., private keys, raw message contents, or plaintext Onion addresses of contacts). If errors occur, log the error types without sensitive context.
3. **Database Security (SQLite):** * Always use parameterized queries or an ORM (like SQLAlchemy) to prevent SQL injection.
   * Ensure that the SQLite database file on the disk is symmetrically encrypted at rest (as per our requirements).

---

## 5. Testing Requirements

Aether's reliability directly impacts user security. Therefore:

* Write **Unit Tests** for all core logic (especially cryptography, Tor interaction, and database queries).
* Write **Integration Tests** for the REST API endpoints.
* Run all tests locally before opening a Pull Request.
