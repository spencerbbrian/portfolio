-- How many movies were released in each country?
SELECT
    release_country, COUNT(DISTINCT movie_name) AS num_movies
FROM 
    movie_insights.movies
GROUP BY 
    release_country
ORDER BY 
    num_movies DESC;

-- Which production company has the highest average gross?
SELECT
    c.company, ROUND(AVG(m.gross),2) AS avg_gross
FROM 
    movie_insights.movies m
JOIN
    movie_insights.companies c
USING(company_id)
GROUP BY 
    c.company
ORDER BY
    avg_gross DESC
LIMIT 1;

-- What is the average budget of movies produced in the United States?
SELECT
    c.country, ROUND(AVG(m.budget),2) AS avg_budget
FROM 
    movie_insights.movies m
JOIN
    movie_insights.countries c
USING(country_id)
WHERE
    c.country = 'United States'
GROUP BY c.country;

-- Which country produced the most movies in the dataset?
SELECT 
    c.country, COUNT(DISTINCT m.movie_name) as movie_count
FROM 
    movie_insights.movies m 
JOIN 
    movie_insights.countries c
using(country_id)
GROUP BY 
    c.country
ORDER BY 
    movie_count DESC
LIMIT 1;

-- Which company produced the most movies in a single year?
SELECT 
    m.year , c.company, COUNT(DISTINCT m.movie_name) as movie_count,  
    RANK() OVER(PARTITION BY m.year ORDER BY COUNT(DISTINCT m.movie_name) DESC) AS prod_rank
FROM 
    movie_insights.movies m
JOIN 
    movie_insights.companies c
USING(company_id)
GROUP BY m.year, c.company
ORDER BY m.year, prod_rank;