# System Architecture

The following diagram shows how data moves through the Multi-Supplier Product Integration Pipeline.

```mermaid
flowchart TD
    A[Supplier A - CSV]
    B[Supplier B - CSV]
    C[Supplier C - JSON]

    A --> D[Data Ingestion]
    B --> D
    C --> D

    D --> E[Data Validation]
    E -->|Invalid Records| F[Rejected Records]
    E -->|Valid Records| G[Data Transformation]

    G --> H[Conflict Resolution]
    H --> I[Product Publishing]

    I --> J[(MySQL Database)]

    J --> K[FastAPI]
    K --> L[Web Dashboard]

    L --> M[Products and Metrics]
    L --> N[Pipeline Run History]
    L --> O[Rejected Records]
```

## Main Components

- **Supplier Feeds:** Product data comes from three different suppliers.
- **Ingestion:** Reads CSV and JSON files.
- **Validation:** Checks whether required product information is available.
- **Transformation:** Converts supplier data into a common format.
- **Conflict Resolution:** Selects preferred product values based on supplier priority.
- **Publishing:** Saves standardized products and source details in MySQL.
- **FastAPI:** Provides APIs to access pipeline data.
- **Dashboard:** Displays products, metrics, pipeline runs, and rejected records.