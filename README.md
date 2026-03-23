# dbt-explainer

A production-grade dbt project modeling Olist Brazilian e-commerce data, with an AI-powered chatbot that lets business users ask questions about the data in plain English.

## Live demo

**Chatbot:** https://dbt-chat.streamlit.app
**dbt project:** github.com/pavithra-analytics/dbt-explainer

## What this project does

This project has two parts.

### 1. dbt analytics pipeline
Transforms raw Olist e-commerce data into analytics-ready models that answer three core business questions:
- **Seller performance** — revenue, order volume, and delivery rates by seller
- **Customer retention** — segmentation across one-time, occasional, and loyal customers
- **Order fulfillment** — delivery timing with on-time vs late classification

### 2. dbt Chat — AI data assistant
A Streamlit chatbot powered by Claude API that lets non-technical business users ask questions about the dbt project in plain English. No file uploads, no technical setup for end users — just a URL and a question.

The tech team deploys it once by pointing it at their dbt project. The business team just asks questions.

## Project structure
```
olist_project/          # dbt project
├── models/
│   ├── staging/olist/  # cleaned raw data
│   └── marts/olist/    # business-ready models
app/                    # AI chatbot
├── app.py              # Streamlit application
├── config.toml         # point this at any dbt project
└── requirements.txt
```

## dbt models

| Model | Description |
|-------|-------------|
| stg_olist__orders | Cleaned orders data |
| stg_olist__customers | Cleaned customers data |
| stg_olist__order_items | Cleaned order items data |
| stg_olist__sellers | Cleaned sellers data |
| mart_seller_performance | Revenue, orders, and delivery rates by seller |
| mart_customer_retention | Customer segmentation by purchase frequency |
| mart_order_fulfillment | Delivery timing and on-time performance |

19 data tests — all passing.

## Deploy your own chatbot in 10 minutes

Any team with a dbt project can deploy their own version.

1. Fork this repo
2. Edit `app/config.toml` — change three lines:
```toml
[project]
name = "Your Team Data Assistant"
github_repo = "your-org/your-dbt-repo"
github_path = "your_dbt_project"
```
3. Deploy to [Streamlit Community Cloud](https://share.streamlit.io) — free
4. Add your Claude API key and GitHub token in Streamlit secrets
5. Share the URL with your team

## Tech stack

- dbt Core 1.11.7
- Google BigQuery
- Python 3.12
- Streamlit
- Claude API (Anthropic)
- Source data: Olist Brazilian E-Commerce Dataset

## How to run locally
```bash
# Install dependencies
pip install -r app/requirements.txt

# Add your secrets
cp app/.streamlit/secrets.toml.example app/.streamlit/secrets.toml
# Edit secrets.toml with your API keys

# Run the chatbot
streamlit run app/app.py

# Run dbt models
cd olist_project
dbt run
dbt test
```

## About

Built by Pavithra Ramesh — Analytics Engineer with 8 years experience at Amazon, Chubb, and Berkshire Hathaway. Open to analytics engineering opportunities and H1B sponsorship.

LinkedIn - https://linkedin.com/in/pavithraramesh12

dbt Chat - https://dbt-chat.streamlit.app
