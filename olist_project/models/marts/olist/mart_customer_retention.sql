with orders as (
    select * from {{ ref('stg_olist__orders') }}
),

customers as (
    select * from {{ ref('stg_olist__customers') }}
),

customer_orders as (
    select
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        count(distinct o.order_id) as total_orders,
        min(o.order_purchase_timestamp) as first_order_date,
        max(o.order_purchase_timestamp) as last_order_date,
        countif(o.order_status = 'delivered') as delivered_orders,
        countif(o.order_status = 'cancelled') as cancelled_orders,
        round(
            date_diff(
                max(date(o.order_purchase_timestamp)),
                min(date(o.order_purchase_timestamp)),
                day
            ), 0
        ) as days_as_customer
    from customers c
    left join orders o on c.customer_id = o.customer_id
    group by 1, 2, 3
),

final as (
    select
        customer_unique_id,
        customer_city,
        customer_state,
        total_orders,
        first_order_date,
        last_order_date,
        delivered_orders,
        cancelled_orders,
        days_as_customer,
        case
            when total_orders = 1 then 'one_time'
            when total_orders between 2 and 3 then 'occasional'
            when total_orders > 3 then 'loyal'
        end as customer_segment
    from customer_orders
)

select * from final