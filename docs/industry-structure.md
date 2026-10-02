# Industry-Standard Project Structure

This repository is structured into three clear layers:

project-root/
  frontend/
    README.md
    app/
    dashboard/
    assets/

  backend/
    README.md
    app/
    api/
    auth/
    services/
    models/
    config/

  data/
    README.md
    raw/
    processed/
    pipelines/
    db/
    ml/
    scripts/

  docs/
    architecture.md

  requirements.txt
  docker-compose.yml
  README.md

This layout keeps responsibilities clean:
- frontend: UI and dashboard
- backend: APIs, auth, business logic, agent orchestration
- data: ingestion, pipelines, ML, storage, transformations
