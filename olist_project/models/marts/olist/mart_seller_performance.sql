with orders as (
    select * from {{ ref('stg_olist__orders') }}
),

order_items as (
    select * from {{ ref('stg_olist__order_items') }}
),

sellers as (
    select * from {{ ref('stg_olist__sellers') }}
),

seller_metrics as (
    select
        oi.seller_id,
        s.seller_city,
        s.seller_state,
        count(distinct oi.order_id) as total_orders,
        round(sum(oi.price), 2) as total_revenue,
        round(avg(oi.price), 2) as avg_order_value,
        round(sum(oi.freight_value), 2) as total_freight,
        countif(o.order_status = 'delivered') as delivered_orders,
        countif(o.order_status = 'cancelled') as cancelled_orders,
        round(
            countif(o.order_status = 'delivered') / count(distinct oi.order_id) * 100,
            2
        ) as delivery_rate_pct
    from order_items oi
    left join orders o on oi.order_id = o.order_id
    left join sellers s on oi.seller_id = s.seller_id
    group by 1, 2, 3
)

select * from seller_metrics