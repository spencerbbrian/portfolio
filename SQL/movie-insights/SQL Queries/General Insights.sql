-- What are the the top 10 highest-grossing movies?
SELECT 
    movie_id, movie_name, gross
FROM 
    movie_insights.movies
ORDER BY 
    gross DESC
LIMIT 
    10;

-- Which movies have the highest budget, and how much did they gross?
SELECT 
    movie_name, budget, gross
FROM 
    movie_insights.movies
ORDER BY 
    budget DESC
LIMIT 10;

-- Which movie has the highest score and how many votes did it receive?
SELECT 
    movie_name, score, votes
FROM 
    movie_insights.movies
ORDER BY 
    score DESC
LIMIT 1;

-- What is the average runtime of all movies in the dataset?
SELECT 
    ROUND(avg(runtime),2) AS average_runtime_mins
FROM 
    movie_insights.movies;

-- What is the total number of movies released in each year?
SELECT
    year, COUNT(DISTINCT movie_id) AS movies_released
FROM 
    movie_insights.movies
GROUP BY
    year
ORDER BY
    movies_released;