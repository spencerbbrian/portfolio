--ORDER ACTIVITY
-- Total Sales
-- Total Orders
-- Total Items
-- Average order value
-- Sales by category
-- Top selling pizzas
-- Top selling sizes
-- Orders by month
-- Sales by month
-- Prefferred categories

SELECT o.order_details_id,
o.order_id,
o.pizza_id,
o.quantity,
o.order_date,
o.order_time,
o.category_id,
p.pizza_name,
p.unit_price,
p.pizza_size,
c.pizza_category
FROM orders o
LEFT JOIN pizza p 
ON o.pizza_id = p.pizza_num
LEFT JOIN categories c
ON o.category_id = c.cat_id