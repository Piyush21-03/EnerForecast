EnerForecast ⚡

Energy Consumption Forecasting & Analytics

EnerForecast is an end-to-end machine learning application for forecasting electricity consumption from historical energy usage data. The system combines time-series feature engineering, LightGBM forecasting, FastAPI, PostgreSQL, and a React dashboard to provide a production-oriented forecasting workflow.

🚀 Features

📊 Historical energy consumption analysis

🔮 24-hour energy consumption forecasting

🤖 LightGBM-based machine learning model

🧠 Time-series lag and rolling-window features

📅 Calendar and cyclical time features

⚡ FastAPI REST API for predictions

🗄️ PostgreSQL database integration

💻 React + Tailwind CSS dashboard

🧪 Automated backend testing with Pytest

🐳 Docker-ready architecture

📈 Forecast and historical consumption visualization

🏗️ System Architecture

                    ┌─────────────────────┐
                    │   Energy Dataset    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Data Processing &    │
                    │ Feature Engineering  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ LightGBM Forecasting│
                    │       Model         │
                    └──────────┬──────────┘
                               │
                         Model Artifact
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │    Backend API      │
                    └───────┬─────┬───────┘
                            │     │
                 ┌──────────┘     └──────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │   PostgreSQL    │        │ React Dashboard │
        │    Database     │        │  + Tailwind CSS │
        └─────────────────┘        └─────────────────┘

🛠️ Tech Stack

Machine Learning

Python

Pandas

NumPy

Scikit-learn

LightGBM

Joblib

SHAP

Backend

FastAPI

Pydantic

SQLAlchemy

Alembic

PostgreSQL

Frontend

React

Vite

Tailwind CSS

Axios

Recharts

Development & Deployment

Git

GitHub

Docker

Pytest

MLflow

📂 Project Structure

energy-forecasting/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── services/
│   ├── artifacts/
│   ├── models/
│   ├── tests/
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── data/
├── notebooks/
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

📊 Dataset

The project is based on the UCI Individual Household Electric Power Consumption dataset.

The forecasting pipeline is designed to:

Validate the input data

Handle missing values and data-quality issues

Convert high-frequency observations into the required forecasting frequency

Generate time-series features

Train and evaluate forecasting models

Export the selected model as a production artifact

The production application does not retrain the model for every prediction request. The trained model artifact is loaded by the FastAPI service.

🔮 Forecasting Approach

The model uses historical consumption patterns and time-based features such as:

Lag features

Rolling statistics

Hour of day

Day of week

Month

Weekend indicators

Cyclical time features

The project uses chronological time-series validation rather than random train/test splitting to reduce temporal leakage.

Forecast Horizon

Primary: 24 hours

Extended: 168 hours / 7 days

⚙️ Local Setup

1. Clone the Repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd energy-forecasting

2. Create a Python Virtual Environment

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

3. Install Backend Dependencies

cd backend
pip install -r requirements.txt

4. Configure Environment Variables

From the project root:

Copy-Item .env.example .env

Update the PostgreSQL credentials in .env.

5. Run Database Migrations

From the backend directory:

alembic upgrade head

6. Start the FastAPI Backend

Make sure you are inside the backend directory:

uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/health

7. Start the Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173

🧪 Testing

Run backend tests from the backend directory:

pytest

The project includes tests for:

Application startup

Configuration

Database

Repositories

Feature engineering

Model service

Forecast service

API endpoints

Integration pipeline

📈 Model Evaluation

The forecasting workflow evaluates models using time-series validation and metrics including:

MAE

RMSE

sMAPE

MAPE

R²

Baseline models such as seasonal naive forecasting are used for comparison before selecting a production model.

🔐 Production Design

The application separates model training from model serving.

Google Colab
     │
     ├── Data Processing
     ├── Feature Engineering
     ├── Model Training
     ├── Model Evaluation
     └── Model Export
             │
             ▼
      Model Artifacts
             │
             ▼
        FastAPI Backend
             │
             ├── Forecast API
             ├── PostgreSQL
             └── React Dashboard

The FastAPI service loads the trained model artifact during application startup instead of retraining the model during API requests.

🗺️ Development Roadmap

Project structure

Backend configuration

Database architecture

FastAPI foundation

Forecast service architecture

React frontend foundation

Tailwind CSS setup

Final model artifact integration

Complete dashboard integration

Docker deployment

MLflow experiment tracking

Production deployment

Monitoring and retraining workflow

🔮 Future Scope

7-day forecasting

Weather-based forecasting features

Anomaly detection

SHAP-based explainability dashboard

Model drift monitoring

Automated model retraining

Cloud deployment

Real-time smart-meter integration

Support for multiple households and buildings

👨‍💻 Project

EnerForecast — Energy Consumption Forecasting & Analytics

Built using Python, LightGBM, FastAPI, PostgreSQL, React, and Tailwind CSS.

⭐ Support

If you find this project useful, consider giving the repository a ⭐.
