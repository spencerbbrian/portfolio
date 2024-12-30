-- Real vs Scheduled Shipping Days
select
avg("Days for shipment (scheduled)") as "scheduled days",
avg("Days for shipping (real)") as "real days"
from shipment s 
group by "Days for shipment (scheduled)" 

-- Actual Shipping Dates vs Late Delivery Risk
select 
"Days for shipping (real)",
"Days for shipment (scheduled)",
"Late_delivery_risk",
"Delivery Status"
from shipment s
where "Delivery Status" = 'Late delivery' and "Late_delivery_risk" > 0

--Late Delivery across shipping modes
select
"Shipping Mode",
COUNT("Late_delivery_risk") as "count_ldr",
avg("Late_delivery_risk") as "avg_ldr"
from shipment s
group by "Shipping Mode"
order by COUNT("Late_delivery_risk") desc, avg("Late_delivery_risk")

--Late Deliveries per year, month & week
SELECT
COUNT("Late_delivery_risk") as count_ldr,
TO_CHAR("shipping date (DateOrders)", 'YYYY') AS shipping_year,
EXTRACT(MONTH FROM CAST("shipping date (DateOrders)" AS DATE)) AS shipping_month,
EXTRACT(WEEK FROM CAST("shipping date (DateOrders)" AS DATE)) AS shipping_week
FROM shipment s
where "Late_delivery_risk" > 0
group by shipping_year, shipping_month, shipping_week
order by count_ldr desc

--Delivery Statuses vs Dates
with order_states as (
select 
TO_CHAR("shipping date (DateOrders)", 'YYYY') AS shipping_year,
EXTRACT(MONTH FROM CAST("shipping date (DateOrders)" AS DATE)) AS shipping_month,
EXTRACT(WEEK FROM CAST("shipping date (DateOrders)" AS DATE)) AS shipping_week,
SUM(case when "Delivery Status" = 'Advance shipping' THEN 1 ELSE 0 END) as advanced_cnt,
SUM(case when "Delivery Status" = 'Late delivery' THEN 1 ELSE 0 END) as late_cnt,
SUM(case when "Delivery Status" = 'Shipping on time' THEN 1 ELSE 0 END) as on_time_cnt,
SUM(case when "Delivery Status" = 'Shipping canceled' THEN 1 ELSE 0 END) as canceled_cnt
FROM shipment s
group by shipping_year, shipping_month, shipping_week)
select 
shipping_year, shipping_month, shipping_week, advanced_cnt, late_cnt, on_time_cnt, canceled_cnt
from order_states
order by shipping_year, shipping_month, shipping_week









