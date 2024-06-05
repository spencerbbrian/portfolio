--Average Sales per Customer Segment
select 
c."Customer Segment",
round(avg(o."Sales")) as "avg segment sales"
from customers c 
right join orders o 
on c."Order Id" = o."Order Id" 
group by c."Customer Segment"  

--Late Deliveries vs Customer Segment
select
count(o."Order Id") as "total orders",
COUNT(CASE WHEN s."Late_delivery_risk" = 1 THEN s."Late_delivery_risk" END) AS count_ldr_1,
c."Customer Segment",
round(avg(s."Late_delivery_risk"),3)
from customers c 
right join shipment s 
on c."Order Id" = s."Order Id" 
right join orders o 
on c."Order Id"  = o."Order Id" 
group by c."Customer Segment" 

--Late Deliveries vs Customer Segment vs Customer Location
select
o."Market",
c."Customer Segment",
count(o."Order Id"),
count(case when s."Late_delivery_risk"= 1 then s."Late_delivery_risk" END) as count_ldr_1,
round(avg(s."Late_delivery_risk"),3)
from customers c 
right join shipment s 
on c."Order Id" = s."Order Id" 
right join orders o 
on c."Order Id" = o."Order Id" 
group by c."Customer Segment",O."Market" 
order by count_ldr_1 desc
limit 10

select *
from shipment s 

select *
from departments d 

select *
from customers c 

select *
from orders o 