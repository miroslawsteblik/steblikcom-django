---
title: "Hexagonal Architecture in Python"
date: 2025-08-16
slug: clean-architecture-python
summary: "Building a market data app with hexagonal architecture in Python. Clean separation of concerns and maintainable code."
card_image: "github_logo.png"
tags: ["python", "clean-architecture", "api"]
draft: false
---

## Table of Contents

- [Introduction](#introduction)
- [Design Principles](#design)
- [Project implementation ](#project-implementation)
- [Prons and Cons](#prons_and_cons)
- [Conclusion](#conclusion)

## Introduction {#introduction}

**Hexagonal Architecture**, also known as **Clean Architecture** or **Ports and Adapters**, is a software design pattern that promotes separation of concerns, testability, and maintainability. This architectural pattern places the business logic at the center (the "hexagon") and isolates it from external dependencies through well-defined interfaces.

### Project Goal: API-to-PostgreSQL Data Integration

This project demonstrates implementing a robust **financial market data pipeline** that fetches data from the AlphaVantage API and stores it in PostgreSQL, while maintaining:

- **Separation of Concerns**: Each layer has a single responsibility
- **Future-Proofing**: Easy to add new data sources or storage backends
- **Data Integrity**: Comprehensive validation ensures data contracts are maintained
- **Testability**: Business logic can be tested independently of external systems
- **Scalability**: Modular design supports growth and evolution

### Why Clean Architecture for Data Integration?

Traditional data pipelines often become tightly coupled monoliths where business logic is mixed with API calls, database queries, and infrastructure concerns. This makes them:

- **Hard to test** (requires real APIs and databases)
- **Difficult to modify** (changing one component affects others)
- **Prone to failures** (external service issues break the entire pipeline)
- **Impossible to scale** (tight coupling prevents horizontal scaling)

Clean Architecture solves these problems by creating **clear boundaries** between different concerns, allowing each component to evolve independently while maintaining system integrity.

## Design Principles {#design}

1. **Port:** Think of a port as a "contract" or interface that defines what your application needs from the outside world, without caring about the specific details of how those needs are met. It's like a USB port on your computer - it defines the shape and electrical specifications, but doesn't care whether you plug in a mouse, keyboard, or external drive.

2. **Adapter:** An adapter is the actual implementation that fulfills the port's contract. It's the specific piece of code that handles the technical details of connecting to databases, web APIs, file systems, or user interfaces. Using the USB analogy, the adapter would be the actual USB cable and device that plugs into the port.

3. The **application** logic is a thin layer that “glues together” other layers. It’s also known as “use cases”. If you read this code and can’t tell what database it uses or what URL it calls, it’s a good sign.
   Sometimes it’s very short, and that’s fine. Think about it as an orchestrator.

4. The **domain** layer contains the core business logic and rules that remain constant regardless of external changes. It includes:
   - **Entities**: Core business objects with identity and lifecycle (e.g., `MarketData`, `ApiLog`)
   - **Value Objects**: Immutable objects defined by their attributes (e.g., `Price`, `Symbol`, `Timestamp`)
   - **Domain Services**: Business logic that doesn't naturally fit in entities (e.g., price validation rules)

5. **Repositories** abstract data persistence, providing a collection-like interface for accessing domain entities. They hide whether data comes from PostgreSQL, MongoDB, or memory.

6. **Services** in the domain layer encapsulate business rules and complex operations that involve multiple entities or external calculations.

7. **Entities vs Value Objects**:
   - Entities have **identity** and **lifecycle** (a MarketData record with ID=123 is the same entity even if price changes)
   - Value Objects are **immutable** and defined by their **attributes** (Price($100) equals any other Price($100))

8. **Dependency Inversion**: High-level modules (domain) should not depend on low-level modules (database). Both should depend on abstractions (interfaces/ports). This enables testing business logic without real databases and swapping implementations without changing core logic.

9. **The Dependency Rule:** Dependencies can only point inward toward the domain. The domain layer knows nothing about the application layer, which knows nothing about the infrastructure layer. This creates a protective boundary around your business logic.

## Project implementation {#project-implementation}

### Prerequisites

- AlphaVantage API key
- Postgres database

### Project structure

```sh
myproject
├── mypackage
│   ├── adapters
│   │   ├── inbound
│   │   │   └── cli
│   │   └── outbound
│   │       ├── external_apis
│   │       ├── messaging
│   │       └── persistence
│   │           ├── file
│   │           └── postgres
│   ├── application
│   │   ├── containers
│   │   └── use_cases
│   ├── domains
│   │   └── market_data
│   │       ├── entities
│   │       ├── service
│   │       └── value_objects
│   ├── infrastructure
│   │   ├── configuration
│   │   ├── database
│   │   │   └── service
│   │   └── logging
│   └── ports
│       └── outbound
├── resources
├── logs
├── main.py
```



#### Example entity - MarketData:

```python
# domains/market_data/entities/market_data.py

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class DataSource(Enum):
    API = "API"
    CSV = "CSV"
    MANUAL = "MANUAL"


class DataStatus(Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    SAVED = "SAVED"


@dataclass
class MarketData:
    """Domain Entity for API market data"""

    id: Optional[int] = None
    symbol: str = ""
    price: Decimal = Decimal("0.00")
    volume: int = 0
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    data_timestamp: Optional[datetime] = None
    source: DataSource = DataSource.API
    status: DataStatus = DataStatus.PENDING
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Business validation rules"""
        errors = []

        if not self.symbol.strip():
            errors.append("Symbol is required")

        if self.price <= 0:
            errors.append("Price must be positive")

        if self.volume < 0:
            errors.append("Volume cannot be negative")

        if self.market_cap is not None and self.market_cap <= 0:
            errors.append("Market cap must be positive if provided")

        if self.pe_ratio is not None and self.pe_ratio <= 0:
            errors.append("PE ratio must be positive if provided")

        if self.data_timestamp is None:
            errors.append("Data timestamp is required")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def mark_as_validated(self) -> None:
        """Business behavior"""
        if self.is_valid():
            self.status = DataStatus.VALIDATED
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Cannot validate: {self.validate()}")

    def mark_as_saved(self) -> None:
        """Business behavior"""
        if self.status == DataStatus.VALIDATED:
            self.status = DataStatus.SAVED
            self.updated_at = datetime.now()
        else:
            raise ValueError("Only validated data can be marked as saved")

```

#### Example Port

```python
from abc import ABC, abstractmethod

from selene.domains.market_data.value_objects.api_response import APIResponse


class MarketDataAPIPort(ABC):
    """Port for market data API operations"""

    @abstractmethod
    def get_market_data(self, symbol: str) -> APIResponse:
        """Fetch market data for a given symbol."""

    @abstractmethod
    def get_bulk_market_data(self, symbols: list[str]) -> APIResponse:
        """Fetch market data for multiple symbols."""
```

#### Example API configuration

```yaml
api:
  name: alphavantage
  description: Alpha Vantage API for financial data
  website: "https://www.alphavantage.co"
  base_url: "https://www.alphavantage.co/query"
  timeout_seconds: 30
  retry_attempts: 3
  rate_limit_per_minute: 60
  default_endpoint: global_quote # Specify which endpoint to use by default
  endpoints:
    - name: global_quote
      method: GET
      params:
        - name: function
          required: true
          type: string
          default: "GLOBAL_QUOTE"
        - name: symbol
          required: true
          type: string
        - name: apikey
          required: true
          type: string
      schema:
        price_path: ["Global Quote", "05. price"]
        volume_path: ["Global Quote", "06. volume"]
        market_cap_path: null
        pe_ratio_path: null
        timestamp_path: ["Global Quote", "07. latest trading day"]
        validation_keys: ["Global Quote"]
  symbols:
    - "AAPL"
    - "GOOGL"
    - "MSFT"
    - "TSLA"

# Database connection settings
database:
  host: localhost
  port: 5432
  database: selene
  user: postgres
  min_connection: 1
  max_connection: 10
```

#### Handle Secrets with `.env`

```bash
# postgres
DB_NAME=my_dbname
DB_USER=my_user
DB_PASSWORD=my_password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer
DB_CONNECT_TIMEOUT=30
APP_NAME=my_app_name

# alpha_vantage
ALPHA_VANTAGE_API_KEY=your_api_key_here

```

## Pros and Cons {#pros_and_cons}

### **Pros: When Clean Architecture Shines**

#### **Large & Long-term Projects**

- **Team Scalability**: Multiple teams can work on different layers independently without conflicts
- **Future-Proofing**: Easy to swap databases (PostgreSQL → MongoDB), APIs (AlphaVantage → IEX Cloud), or use flat files
- **Maintenance**: Clear separation makes debugging and feature additions predictable
- **Testing**: Business logic can be thoroughly tested without external dependencies

#### **Complex Business Logic**

- **Domain Clarity**: Business rules are isolated and easy to understand
- **Data Integrity**: Validation and business rules are enforced at the domain level
- **Compliance**: Audit trails and regulatory requirements are easier to implement

#### **Enterprise Requirements**

- **Integration**: Multiple data sources and destinations can be added without architectural changes
- **Performance**: Can optimize specific layers (caching at repository level, async at service level)
- **Security**: Clear boundaries make it easier to implement security controls

### **Cons: When It Becomes Over-Engineering**

#### **Small & Ad-hoc Projects**

- **Development Overhead**: A simple "fetch API → save to DB" script becomes 15+ files across 5 directories
- **Time to Market**: MVP features take 3-4x longer to implement
- **Learning Curve**: Junior developers need time to understand the architecture before contributing

#### **Rapid Prototyping**

- **Ceremony**: Creating interfaces, entities, and use cases for every small feature slows experimentation
- **Premature Abstraction**: You might abstract things that never actually change
- **YAGNI Violation**: "You Aren't Gonna Need It" - complex architecture for simple requirements

#### **Resource Constraints**

- **Small Teams**: 1-2 developers don't benefit from strict layer separation
- **Limited Scope**: Projects with fixed, unchanging requirements don't need flexibility
- **Technical Debt**: Poorly implemented Clean Architecture is worse than a simple monolith

### **Decision Framework: When to Use Clean Architecture**

#### **✅ Use Clean Architecture When:**

- **Project lifespan > 1 year**
- **Team size > 5 developers**
- **Multiple integrations** (APIs, databases, message queues)
- **Complex business rules** that change frequently
- **Regulatory compliance requirements**
- **Unknown future requirements** (high uncertainty)

#### **❌ Avoid Clean Architecture When:**

- **MVP or proof-of-concept** projects
- **Single developer** or small team
- **Fixed requirements** with no expected changes
- **Simple CRUD operations** with minimal business logic
- **Tight deadlines** with limited scope
- **Learning projects** where architecture is not the focus

## Conclusion

### **Complexity Trade-off**

#### **Simple Script Approach** (50 lines):

```python
import requests
import psycopg2

# Fetch data
response = requests.get(f"https://api.example.com/stock/{symbol}")
data = response.json()

# Save to database
conn = psycopg2.connect("postgresql://...")
cursor.execute("INSERT INTO market_data VALUES (%s, %s)", (symbol, price))
conn.commit()
```

#### **Clean Architecture Approach** (500+ lines):

- 5 layers with clear separation
- Comprehensive error handling
- Full test coverage
- Multiple configuration options
- Extensible for future requirements

**The Trade-off**: 10x more code for 100x more maintainability and flexibility.

## Get the Code

Explore the complete implementation with all the Clean Architecture patterns discussed in this article:

> **Selene - Market Data Pipeline**
>
> Production-ready Python implementation featuring:
>
> - Complete Hexagonal Architecture implementation
> - AlphaVantage API integration with rate limiting
> - PostgreSQL repository with connection pooling
> - Real market data validation and processing
> - CLI interface with dependency injection
>
> **[🔗 View on GitHub →](https://github.com/miroslawsteblik/selene)**

**Quick Start:**

```bash
git clone https://github.com/miroslawsteblik/selene.git
cd selene
pip install .
selene fetch --config resources/fetch_api.yaml
```
