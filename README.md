# Aether

Aether is a decentralized peer-to-peer instant messenger designed for the secure communication of high-risk individuals (e.g., whistleblowers, investigative journalists). The architecture strictly adheres to the principles of "Security by Design" and "Privacy by Default".

For details on Architecture, Contributing, Operations and Testing please refer to [doc/](/doc/).

## Core Features & Architecture

Aether operates without any central relay or routing servers to eliminate metadata accumulation. The system uses a locally decoupled client-server architecture running exclusively on the end user's machine:

* **Backend (Python Flask):** Functions as a local REST server, manages cryptographic keys, controls database access, and coordinates asynchronous tasks like message retries.
* **Tor Network Layer:** Uses a bundled Tor daemon (C-Binary) to offload routing and NAT traversal entirely to the Tor network via v3 Onion Services, guaranteeing anonymity and obfuscating user IPs.
* **Frontend (Electron):** Encapsulates the Graphical User Interface (GUI) and local state management. 
*Note: The frontend codebase is located in the `src-frontend` sub-repository. Please see `src-frontend/README.md` for frontend-specific documentation and commands.*

### Security Highlights
* **Identity & Handshake:** Users are identified by an Ed25519 Tor key pair. Cryptographic key exchange uses the Noise Protocol Framework for Perfect Forward Secrecy (PFS) over Tor.
* **Data-at-Rest Encryption:** Local data is encrypted via SQLCipher within a strict "Database-per-Profile" architecture to prevent cross-tenant data leaks and support secure multi-tenancy.
* **Secure IPC:** The backend uses a dynamic, ephemeral API key generated at boot to prevent local malicious software from accessing the API.
* **Zero IP Leaks:** All external communication must strictly be routed through the local Tor SOCKS5 proxy.


## Installation and Startup

Aether`s primary target environments are security- and privacy-focused operating systems like Tails OS and Whonix (GNU/Linux). Because Aether relies on Python and Node.js, the application is not compiled into a standalone binary executable.

Below are the manual installation and startup instructions for the backend environment. For frontend-specific development commands (like `npm run dev:web`), please refer to `src-frontend/README.md`.

### Prerequisites
You will need Docker installed on your system.

For information on Docker install see [Docker get-started](https://www.docker.com/get-started/).

### Build and Run the Backend
```bash
# Build container (execute in the aether project root)
docker build --no-cache -t aether .

# Start backend
docker run -p 5000:5000 --name aether-client aether
```

## Contributing to Aether

We use a Feature Branch Workflow based on Trunk-Based Development, and direct pushes to the `main` branch are strictly forbidden. 

* **Commits:** We strictly follow the Conventional Commits specification (e.g., `feat(tor): ...`, `fix(api): ...`).
* **Pull Requests:** Every PR requires at least one approving review from another team member (Four-Eyes Principle) and must pass the GitHub Actions CI pipeline.
* **Code Standards (Backend):** Code must adhere to PEP 8. Use the Black formatter, Flake8/Pylint, and extensive Python Type Hinting.

## Testing Requirements

Aether's quality assurance relies on a risk-based testing approach heavily focused on "Security by Design".
* **Backend Unit Tests:** Use `pytest` for testing middleware, cryptography modules, and SQLite database operations.
* **Quality Gates:** Code coverage measured by `pytest-cov` must be at least 70%. Furthermore, SonarQube must report 0 critical and 0 high vulnerabilities for a PR to be merged.
* **Test Setup:**
    ```bash
    # Create virtual enviroment
    python -m venv .venv

    # Activate virtual enviroment (Linux)
    .venv/bin/activate

    # Activate virtual enviroment (Windows)
    .venv\Scripts\activate

    # Install requirements
    pip install -r requirements.txt
    ```
* **Test Execution:**
  ```bash
  # Run backend tests locally
  pytest

  # Generate coverage report
  pytest --cov=src --cov-report=term-missing
  ```

## Operations & Updates

Standard automatic background updates are considered a security risk in high-threat environments. Therefore, Aether does not perform silent auto-updates or background update checks. Users must proactively download new releases and verify their GPG signatures.

**End-of-Life (EOL):** If active development ceases, a final sunset release will be published containing a permanent UI warning banner, and users will be guided to securely extract their data using the Export Encrypted Backup feature.