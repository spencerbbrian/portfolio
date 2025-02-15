-- How has the average score of movies changed over time (year by year)?
SELECT year, ROUND(AVG(score),2) AS average_score
FROM movie_insights.movies
GROUP BY 1
ORDER BY 1;


-- What is the average gross of movies released in each decade?
SELECT FLOOR(year / 10) * 10 AS  decade, ROUND(AVG(gross),2) AS avg_gross
FROM movie_insights.movies
GROUP BY decade
ORDER BY decade;

-- How does runtime vary across different decades?
SELECT FLOOR(year / 10) * 10 AS  decade, ROUND(AVG(runtime),2) AS avg_runtime
FROM movie_insights.movies
GROUP BY 1
ORDER BY 1;


-- What is the trend of average budget over the years?
SELECT year, ROUND(AVG(budget),2) AS avg_budget
FROM movie_insights.movies
GROUP BY 1
ORDER BY 1;


-- Which year had the highest total number of votes across all movies?
SELECT year, SUM(votes) AS highest_votes
FROM movie_insights.movies
GROUP BY 1
ORDER BY 2 DESC
LIMIT 1;