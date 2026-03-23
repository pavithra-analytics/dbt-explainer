# dbt-explainer

A production-grade dbt project modeling Olist Brazilian e-commerce data with full test coverage and documentation.

## What this project does

This project transforms raw Olist e-commerce data into analytics-ready models that answer three core business questions:

1. **How are sellers performing?** Revenue, order volume, and delivery rates by seller
2. **Are customers coming back?** Retention segmentation across one-time, occasional, and loyal customers
3. **Are orders being fulfilled on time?** End-to-end fulfillment tracking with on-time vs late delivery classification

## Project structure
```
olist_project/
├── models/
│   ├── staging/
│   │   └── olist/
│   │       ├── stg_olist__orders.sql
│   │       ├── stg_olist__customers.sql
│   │       ├── stg_olist__order_items.sql
│   │       ├── stg_olist__sellers.sql
│   │       └── _stg_olist__models.yml
│   └── marts/
│       └── olist/
│           ├── mart_seller_performance.sql
│           ├── mart_customer_retention.sql
│           ├── mart_order_fulfillment.sql
│           └── _mart_olist__models.yml
```

## Tech stack

- dbt Core 1.11.7
- Google BigQuery
- Python 3.12
- Source data: Olist Brazilian E-Commerce Dataset

## Models

### Staging
| Model | Description |
|-------|-------------|
| stg_olist__orders | Cleaned and renamed orders data |
| stg_olist__customers | Cleaned and renamed customers data |
| stg_olist__order_items | Cleaned and renamed order items data |
| stg_olist__sellers | Cleaned and renamed sellers data |

### Marts
| Model | Description |
|-------|-------------|
| mart_seller_performance | Seller revenue, order volume, and delivery rates |
| mart_customer_retention | Customer segmentation by purchase frequency |
| mart_order_fulfillment | Order delivery timing and on-time performance |

## Tests

19 data tests covering uniqueness, not-null constraints, and accepted values across all models. All tests passing.

## How to run

Install dependencies:
pip install dbt-bigquery

Test connection:
dbt debug

Run all models:
dbt run

Run tests:
dbt test

## About

Built by Pavithra Ramesh — Analytics Engineer with 8 years experience at Amazon, Chubb, and Berkshire Hathaway. 

LinkedIn: linkedin.com/in/pavithraramesh12