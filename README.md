# envault

> CLI tool for managing and encrypting `.env` files across multiple projects with team sharing support.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended):

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**
```bash
envault init
```

**Encrypt your `.env` file:**
```bash
envault lock --file .env
```

**Decrypt and load secrets:**
```bash
envault unlock --file .env.vault
```

**Share secrets with your team:**
```bash
envault share --file .env.vault --key team-shared-key
```

**Pull secrets in CI/CD or a teammate's machine:**
```bash
envault pull --project my-app
```

---

## Features

- 🔐 AES-256 encryption for `.env` files
- 👥 Team sharing via shared keys or key registry
- 🗂️ Multi-project support from a single CLI
- 🔄 Simple encrypt/decrypt workflow
- 🛠️ Easy CI/CD integration

---

## License

[MIT](LICENSE) © envault contributors