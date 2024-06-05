-- Find the category with the highest and lowest orders in every volume category
with cat_group as (
select 
	c."Category Name",
	c."Orders",
	case 
		when c."Orders" > 10000 then 'High-Volume'
		when c."Orders" > 1000 then 'Mid-Volume'
		else 'Regular-Volume'
	end as "Order Volume"
from categories c 
),
high_ranked_categories as (
select 
"Category Name",
"Order Volume",
row_number() over(partition by "Order Volume" order by "Orders" DESC) as category_rank,
"Orders"
from cat_group),
low_ranked_categories as (
select 
"Category Name",
"Order Volume",
row_number() over(partition by "Order Volume" order by "Orders") as category_rank,
"Orders"
from cat_group)
select "Category Name", "Order Volume", "Orders"
from high_ranked_categories
where category_rank = 1
union all 
select "Category Name", "Order Volume", "Orders"
from low_ranked_categories
where category_rank = 1
order by "Order Volume", "Orders" desc


-- Correlation between categories and Shipping Modes (top 2 preferred)
with categories_cte as (
select c."Category Name", s."Shipping Mode", count(s."Order Id") as "orders count"
from categories c 
right join orders o  
on
c."Category Id" = o."Category Id"
right join shipment s 
on
o."Order Id" = s."Order Id"
group by c."Category Name", s."Shipping Mode"
),
category_preferred_shipping as (
select 
"Category Name",
"Shipping Mode",
row_number() over(partition by "Category Name" order by "orders count" desc) as preferred_category_rank,
"orders count"
from categories_cte
)
select * 
from category_preferred_shipping
where preferred_category_rank = 1 or preferred_category_rank = 2


 
