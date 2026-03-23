with orders as (
    select * from {{ ref('stg_olist__orders') }}
),

fulfillment as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        date_diff(
            date(order_approved_at),
            date(order_purchase_timestamp),
            day
        ) as days_to_approval,
        date_diff(
            date(order_delivered_customer_date),
            date(order_purchase_timestamp),
            day
        ) as days_to_delivery,
        date_diff(
            date(order_estimated_delivery_date),
            date(order_delivered_customer_date),
            day
        ) as days_early_or_late,
        case
            when order_delivered_customer_date <= order_estimated_delivery_date
                then 'on_time'
            when order_delivered_customer_date > order_estimated_delivery_date
                then 'late'
            else 'pending'
        end as delivery_status
    from orders
)

select * from fulfillment