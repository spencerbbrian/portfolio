-- What is the average score of movies for each genre?
SELECT 
    g.genre,
    count(distinct(m.movie_id)) AS number_of_movies,
    round(avg(m.score)) AS avg_genre_score
FROM 
    movie_insights.movies m
LEFT JOIN 
    movie_insights.genres_movies_relations gmr
ON m.movie_id = gmr.movie_id
JOIN movie_insights.genres g
ON gmr.genre_id = g.genre_id
GROUP BY g.genre
ORDER BY avg_genre_score DESC;

-- What genre has the highest average gross?
SELECT 
    g.genre, round(avg(m.gross),2) as average_gross
FROM 
    movie_insights.movies m
JOIN
    movie_insights.genres_movies_relations gmr
using(movie_id)
JOIN 
    movie_insights.genres g  
USING(genre_id)
GROUP BY g.genre
ORDER BY average_gross DESC;

-- What is the distribution of movies across different rating?
SELECT rating, COUNT(DISTINCT movie_name) as movie_count
FROM movie_insights.movies
GROUP BY rating
ORDER BY movie_count DESC;

-- How many movies of each genre were released in the 1980s?
SELECT 
    g.genre,
    COUNT(m.movie_id) AS number_of_movies
FROM 
    movie_insights.movies m
JOIN 
    movie_insights.genres_movies_relations gmr ON m.movie_id = gmr.movie_id
JOIN 
    movie_insights.genres g ON gmr.genre_id = g.genre_id
WHERE 
    m.year BETWEEN 1980 AND 1989
GROUP BY 
    g.genre
ORDER BY 
    number_of_movies DESC;

-- Which genre had the most votes in total?
SELECT 
    g.genre, SUM(m.votes) AS total_votes
FROM 
    movie_insights.movies m
JOIN
    movie_insights.genres_movies_relations gmr
using(movie_id)
JOIN 
    movie_insights.genres g  
USING(genre_id)
GROUP BY g.genre
ORDER BY total_votes DESC;