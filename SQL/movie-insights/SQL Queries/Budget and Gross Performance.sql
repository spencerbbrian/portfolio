-- What is the average gross for movies with a budget over $10 million?
SELECT ROUND(AVG(gross),2)
FROM movie_insights.movies
WHERE budget > 10000000;

-- What is the gross-to-budget ratio to each movie?
SELECT movie_name, ROUND((gross/budget),2) AS gross_budget_ratio
FROM movie_insights.movies
ORDER BY gross_budget_ratio DESC;

-- Which movies had a gross higher than 10 times their budget?
SELECT movie_name, ROUND((gross/budget),2) AS gross_budget_ratio
FROM movie_insights.movies
WHERE ROUND((gross/budget),2) > 10
ORDER BY gross_budget_ratio DESC;

-- What is the correlation between budget and gross revenue?
SELECT ROUND(AVG((gross-budget)/(budget)),2) AS budget_gross_revenue_correlation
FROM movie_insights.movies;

-- What is the total budget and gross for all  movies released in 1980?
SELECT SUM(budget) total_budget, SUM(gross) total_gross
FROM movie_insights.movies
WHERE year = 1980;