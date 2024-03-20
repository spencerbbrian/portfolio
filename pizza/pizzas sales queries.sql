-- Total Revenue
SELECT 
SUM(total_price) AS Total_Revenue 
FROM pizza_sales

-- Average order sale
SELECT 
SUM(total_price)/COUNT(DISTINCT order_id) AS Avg_Order_Value
FROM pizza_sales

-- Total Pizzas Sold
SELECT 
SUM(quantity) AS Total_Pizza_Sold
FROM pizza_sales

-- Total Orders
SELECT
COUNT(DISTINCT order_id) AS Total_Orders
FROM pizza_sales

-- Average Pizzas Per Order
SELECT
CAST(
CAST(SUM(quantity) AS decimal)/
CAST(COUNT(DISTINCT order_id) AS decimal) AS decimal (10,2))
AS Average_Pizzas_Per_Order
FROM pizza_sales

--Hourly Trend For Pizzas Sold
SELECT 
DATEPART(HOUR,order_time) AS order_hour,
SUM(quantity) AS total_pizzas_sold
FROM pizza_sales
GROUP BY DATEPART(HOUR,order_time)
ORDER BY DATEPART(HOUR,order_time)

-- Weekly Trend For Total Orders
SELECT 
DATEPART(ISOWW,order_date) AS week_number,
YEAR(order_date) AS years,
COUNT(DISTINCT order_id) AS total_orders
FROM pizza_sales
GROUP BY DATEPART(ISOWW,order_date), YEAR(order_date)
ORDER BY DATEPART(ISOWW,order_date), YEAR(order_date)

--Percentage of Sales By Pizza Category
SELECT 
pizza_category,
SUM(total_price) * 100 / 
(SELECT sum(total_price) FROM pizza_sales) AS PCT
FROM pizza_sales
GROUP BY pizza_category
ORDER BY PCT

--Percentage of Sales By Pizza size
SELECT 
pizza_size,
SUM(total_price) * 100 / 
(SELECT sum(total_price) FROM pizza_sales) AS PCT
FROM pizza_sales
GROUP BY pizza_size
ORDER BY PCT

-- Top 5 pizzas by sales
SELECT TOP 5 pizza_name,
SUM(quantity) AS total_pizzas_sold
FROM pizza_sales
WHERE MONTH(order_date) = 8
GROUP BY pizza_name
ORDER BY SUM(quantity) DESC