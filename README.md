# NexoLocal

> **A unified business management platform for local companies — inventory, sales, finance, and compliance in one place.**

---

## 🚀 Overview

**NexoLocal** is a proprietary platform designed to solve the fragmented and inefficient way local businesses manage sales, inventory, expenses, cash flow, and operational data.

Many existing solutions are either too complex, too expensive, or not adapted to real local business workflows and regulations, forcing owners to rely on disconnected tools or manual processes.

NexoLocal is built for **small and medium local businesses**, shop owners, service providers, and growing teams that need a **practical, integrated, and scalable system** to operate with clarity, control, and confidence. It is built with scalability, security, and long‑term growth in mind.

This repository contains the **core codebase** and internal tooling. It is **not open‑source**.

---

## ✨ Key Features

* 🔐 Secure authentication & role‑based permissions
* 🧠 Modular architecture (API / services / frontend)
* 📊 Business‑ready logic (finance, inventory, analytics)
* 🌍 Designed for multi‑tenant and future multi‑country expansion
* ⚡ Modern stack with performance and maintainability in mind

---

## 🧱 Tech Stack

**Backend**

* Python / FastAPI
* PostgreSQL + SQLAlchemy
* Alembic migrations

**Frontend**

* Node.js
* Nunjucks + Tailwind CSS

**Infrastructure**

* Docker
* Linux (Arch / Ubuntu)

---

## 🛠️ Development Status

🚧 **Active development**

This project is under heavy iteration. APIs, schemas, and internal logic may change without notice.

---

## 🔒 License & Usage

⚠️ **This project is NOT open‑source.**

Unauthorized copying, redistribution, modification, or commercial use of this code is strictly prohibited.

See the full license below.

---

## 📄 LICENSE

```
Copyright (c) 2026 Novus0x

All Rights Reserved.

This software and associated documentation files (the "Software") are the
exclusive property of the copyright holder.

Permission is NOT granted to use, copy, modify, merge, publish, distribute,
sublicense, or sell copies of the Software, in whole or in part, for any purpose,
without explicit written permission from the copyright holder.

The copyright holder explicitly reserves all rights, including the right to:
- Modify the Software at any time
- Change licensing terms in future versions
- Grant or revoke permissions at their sole discretion

Any attempt to reverse engineer, decompile, sublicense, offer as a service (SaaS),
or derive competing products from the Software is strictly prohibited.

Collaboration, contributions, or commercial usage are only permitted through
direct written agreement with the copyright holder.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE, AND NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDER
BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

## 📬 Contact

For licensing, partnerships, or commercial inquiries:

**Novus0x**
Founder & Developer

---

# Personal Note

env.py (migrations - alembic)

```
import db.model
from db.database import Base
target_metadata = Base.metadata
```
