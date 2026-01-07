## Setup the env

```bash
cp .env.example .env
```

## install libs

```bash
pip install -r requirements.txt
```

## Get airflow token
```bash
curl -X POST "http://localhost:8080/auth/token" -H "Content-Type: application/json" -d '{"username":"airflow","password":"airflow"}'
```