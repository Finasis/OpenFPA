# 📊 OpenFP&A — Open-Source Financial Planning & Analysis Platform

**OpenFP&A** is an open-source platform designed to automate **Financial Planning & Analysis (FP&A)** workflows for **SMEs, consultants, and finance professionals**.

No expensive software. No SaaS lock-ins. Just transparent, modular tools you control — built for real-world business needs.

---

## ✨ Key Features

### Phase 1 MVP (Current)

- **Multiple Data Source Connections** (PostgreSQL, MySQL, SQL Server, Oracle, SQLite)
- **Flexible Reporting & Data Model** with REST API
- **Advanced Analytics Engine** powered by Pandas
  - Pivot tables and cross-tabulation
  - Slice & dice operations
  - Statistical analysis and aggregations
- **Excel Export/Import** for end-users who prefer spreadsheets
- **Docker-based deployment** for easy setup
- **Modern Tech Stack**: FastAPI backend with comprehensive API documentation

### Phase 2 & Beyond (Roadmap)

- Budgeting & Forecasting modules
- Workflow support for closing/budgeting cycles
- Manual journal entries and adjustments
- Advanced Excel integration (MDX connectors)
- ClickHouse/OLAP engine integration for performance
- Real-time dashboards and visualizations

---

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (primary), Redis (caching)
- **Data Processing**: Pandas, NumPy
- **Containerization**: Docker & Docker Compose
- **API Documentation**: Auto-generated Swagger/OpenAPI

---

## 📂 Project Structure

```
fpa-platform/
├── docker-compose.yml          # Docker orchestration
├── .env.example               # Environment variables template
├── README.md                  # This file
├── backend/                   # FastAPI backend application
│   ├── Dockerfile            # Backend container definition
│   ├── requirements.txt      # Python dependencies
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── core/            # Core functionality
│   │   │   ├── config.py    # Application configuration
│   │   │   ├── database.py  # Database connection management
│   │   │   └── security.py  # Authentication & authorization
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/   # API endpoints
│   │   │           ├── health.py        # Health checks
│   │   ├── models/          # SQLAlchemy ORM models - TODO
│   │   ├── schemas/         # Pydantic validation schemas - TODO
│   │   ├── services/        # Business logic layer - TODO
│   │   └── utils/           # Utility functions
│   └── tests/               # Test suite
└── migrations/              # Database migrations (Alembic)
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- Python 3.11+ (for local development)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Finasis/OpenFPA.git
   cd OpenFPA
   ```

2. **Create environment file**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the platform**:

   ```bash
   docker-compose up -d
   ```

4. **Check service health**:

   ```bash
   # API Health check
   curl http://localhost:8000/api/v1/health/

   # Readiness check (database & redis)
   curl http://localhost:8000/api/v1/health/ready
   ```

5. **Access the platform**:
   - API Documentation: http://localhost:8000/docs
   - API Base URL: http://localhost:8000/api/v1

---

## 📋 API Endpoints

### ALL ENDPOINTS ARE TODO

### Data Sources

- `GET /api/v1/data-sources` - List all data sources
- `POST /api/v1/data-sources` - Create new data source
- `GET /api/v1/data-sources/{id}` - Get specific data source
- `PUT /api/v1/data-sources/{id}` - Update data source
- `DELETE /api/v1/data-sources/{id}` - Delete data source
- `POST /api/v1/data-sources/{id}/test` - Test connection
- `POST /api/v1/data-sources/{id}/query` - Execute query
- `GET /api/v1/data-sources/{id}/tables` - List tables

### Analytics

- `POST /api/v1/analytics/pivot` - Create pivot table
- `POST /api/v1/analytics/analyze` - Perform data analysis
- `POST /api/v1/analytics/slice-dice` - Slice and dice operations
- `POST /api/v1/analytics/export/excel` - Export to Excel
- `POST /api/v1/analytics/upload/csv` - Analyze CSV upload
- `GET /api/v1/analytics/functions` - List available functions

### Reports

- `GET /api/v1/reports` - List all reports
- `POST /api/v1/reports` - Create new report
- `GET /api/v1/reports/{id}` - Get specific report
- `POST /api/v1/reports/{id}/execute` - Execute report
- `POST /api/v1/reports/{id}/schedule` - Schedule report

### Health & Monitoring

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

---

## 🔧 Development

### Local Development Setup

1. **Create Python virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

3. **Run locally** (requires PostgreSQL and Redis running):
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Running Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

---

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes (data)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# Access backend container
docker exec -it fpa_backend bash

# Access database
docker exec -it fpa_postgres psql -U fpa_user -d fpa_db
```

---

## 🔒 Security Considerations

- Change default passwords in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement proper authentication (JWT tokens ready)
- Encrypt database passwords
- Regular security updates

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for the FP&A community
- Inspired by the need for accessible financial tools
- Powered by open-source technologies

---

## 📧 Contact

- Project Link: [https://github.com/Finasis/OpenFPA](https://github.com/Finasis/OpenFPA)
- Issues: [https://github.com/Finasis/OpenFPA/issues](https://github.com/Finasis/OpenFPA/issues)

---
