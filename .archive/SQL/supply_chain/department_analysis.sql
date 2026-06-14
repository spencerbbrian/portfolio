select COUNT("Order Id")
from departments d 

select distinct(count("Order Id"))
from departments d 

select "Department Name", count("Order Id") as order_count
from departments d 
group by "Department Name" 
order by order_count desc

select * from departments d 