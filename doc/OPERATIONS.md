# Operations & Deployment Strategy (OPERATIONS.md)

## 1. Introduction & DevOps Philosophy

Due to Aether's strictly decentralized Peer-to-Peer (P2P) architecture and its reliance on the Tor network for routing, the application does not require centralized backend servers, relay nodes, or external databases. Consequently, classical IT operations and server maintenance are not applicable.

In the context of Aether, "Operations" encompasses the automated Quality Assurance (CI/CD pipeline), the secure compilation and distribution of the software to the end-user (Release Management), and the lifecycle management of the product (End-of-Life planning). Our operational processes are designed to uphold the project's core principle of "Security by Design".

## 2. Continuous Integration (CI) & Supply Chain Security

To prevent human error and ensure that every commit meets our strict security and quality standards, we utilize **GitHub Actions** as our centralized CI/CD platform.

### 2.1 Quality Gates and Automated Testing

Every accepted Pull Request to the `main` branch triggers a comprehensive CI pipeline. Code is only eligible for merging if it passes the following automated quality gates:

* **Linting & Formatting:** Enforced via `Pylint` (Backend) and `ESLint`/`Prettier` (Frontend) to maintain clean code standards.
* **Test Execution:** Execution of the `pytest` and `Jest` suites. The pipeline fails if the backend test coverage drops below **70%**.
* **Static Application Security Testing (SAST):** `SonarQube` scans the codebase. The pipeline immediately halts if any critical or high-severity vulnerabilities are detected.

### 2.2 Supply Chain Security

Given the severe threat model of our target audience (e.g., investigative journalists), securing third-party dependencies is paramount. We employ **Dependabot** to continuously monitor all `npm` and `pip` dependencies for known vulnerabilities (CVEs). Vulnerable dependencies automatically trigger a security alert and generate a PR for dependency patching.

## 3. Continuous Deployment (CD) & Release Management

The build and distribution processes are entirely automated to ensure reproducible builds and eliminate manual tampering risks during the compilation phase.

### 3.1 Automated Build Process

Aether's primary target environments are security- and privacy-focused operating systems (e.g., Tails OS, Whonix). Therefore, official binary releases are exclusively built for **GNU/Linux**.

The automated CD pipeline is triggered when a developer pushes a new version tag (e.g., `v1.0.0`) to the `main` branch:

1. **Backend Bundling:** `PyInstaller` bundles the Python/Flask middleware, Tor wrappers and all dependencies into a standalone executable, freezing the Python environment.
2. **Frontend Packaging:** `electron-builder` packages the Electron frontend and the bundled backend.
3. **Artifact Generation:** The pipeline outputs a self-contained `.AppImage` file, ensuring out-of-the-box compatibility across major GNU/Linux distributions.

### 3.2 Cryptographic Signing Strategy

To protect users against supply-chain attacks (e.g., compromised GitHub servers), all releases are cryptographically signed.

* **Current Automation (Beta Phase):** During the current project phase, the CI/CD pipeline automatically signs the release tags and the generated `.AppImage` binaries using a dedicated GPG key stored in GitHub Secrets.
* **Future Transition (Production Maturity):** As the project matures and reaches a larger user base, the signing process will transition to an "offline signing" model. Automated CI/CD signing will be disabled, and core maintainers will download the reproducible builds, verify them, and sign the release archives locally to futher increase security.

## 4. Delivery and Update Procedure

Standard automatic background updates are considered a security risk in high-threat environments, as they can be exploited to silently push malicious payloads to targeted users.

### 4.1 Update Checks via Tor

Aether **does not** feature silent auto-updates. Instead, the application implements a privacy-preserving update notification system:

1. Upon application startup, the software queries the GitHub Releases API for new version tags.
2. **Crucial Security Constraint:** To strictly prevent IP leaks (NFR-01), the Electron frontend does *not* make this HTTP request directly. The request is routed through the local Flask backend, which tunnels the API call exclusively through the local Tor SOCKS5 proxy.
3. If a new version is found, a non-intrusive banner appears in the GUI informing the user. The user is instructed to download the new `.AppImage` and manually verify its GPG signature before execution.

## 5. Build from Source (Developer & Tech Enthusiast Experience)

For users who want to verify and compile the software themselves, we provide full access to the source code alongside a streamlined setup process.

To prevent cumbersome manual setups of virtual environments and node modules, we provide a cross-platform **Makefile**. Users can simply clone the repository and execute:

* `make install`: Automatically sets up the Python `venv`, installs `pip` requirements, and runs `npm install`.
* `make run`: Boots the local Tor mock, starts the Flask backend, and launches the Electron GUI in development mode.

Additionally, for those who want to prefer a fully manual installation, we provide step-by-step instructions in our README.

## 6. End-of-Life (EOL) & Sunset Strategy

A decentralized application poses a unique challenge: there are no central servers to shut down. Even if active development ceases, users could theoretically continue using Aether indefinitely. However, unpatched cryptographic libraries or outdated Tor daemons eventually become critical security vulnerabilities.

To responsibly manage the project's End-of-Life, the following Sunset Strategy is defined:

1. **Repository Archiving:** The GitHub repository will be set to "Read-Only / Archived", and the `README.md` will be updated with a prominent "ABANDONED / EOL" security warning.
2. **Final Sunset Release:** A final update will be published. This version will hardcode a permanent, un-dismissible warning banner in the Graphical User Interface: *"Software EOL: This software no longer receives security updates. Continued use poses a severe security risk."*
3. **Data Offboarding:** The final release notes and documentation will guide users to utilize the **Export Encrypted Backup (UC-10)** feature. This allows users to securely extract their cryptographic identity and contact lists before permanently deleting the Aether client from their machines.
