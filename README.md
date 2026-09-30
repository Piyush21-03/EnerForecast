# EnerForecast ⚡

### Energy Consumption Forecasting & Analytics

EnerForecast is an end-to-end machine learning application for forecasting electricity consumption from historical energy usage data. The system combines time-series feature engineering, LightGBM forecasting, FastAPI, PostgreSQL, and a React dashboard to provide a production-oriented forecasting workflow.

## 🚀 Features

- 📊 Historical energy consumption analysis
- 🔮 24-hour energy consumption forecasting
- 🤖 LightGBM-based machine learning model
- 🧠 Time-series lag and rolling-window features
- 📅 Calendar and cyclical time features
- ⚡ FastAPI REST API for predictions
- 🗄️ PostgreSQL database integration
- 💻 React + Tailwind CSS dashboard
- 🧪 Automated backend testing with Pytest
- 🐳 Docker-ready architecture
- 📈 Forecast and historical consumption visualization

## 🏗️ Architecture

```text
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
                    │ LightGBM Forecasting │
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
