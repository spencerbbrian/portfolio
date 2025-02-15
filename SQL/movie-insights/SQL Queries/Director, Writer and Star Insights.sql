-- Which director has directed the most movies?
WITH director as (
SELECT 
    mr.director_id as director_id, 
    COUNT(m.movie_id) AS movie_count
FROM 
    movie_insights.movies m
LEFT JOIN 
    movie_insights.movie_relations mr
    USING (movie_id)
GROUP BY 
    mr.director_id
ORDER BY
    movie_count DESC
LIMIT 1
)

SELECT d.string_field_1 ,cte.director_id, cte.movie_count
FROM director cte
LEFT JOIN movie_insights.directors d
ON cte.director_id = d.int64_field_0;

-- Who is the most common writer across the dataset?
with writer_movie_count AS(
SELECT 
    w.int64_field_0 writer_id,
    w.string_field_1 writer_name,
    COUNT(m.movie_id) movie_count
FROM 
    movie_insights.writers w
JOIN 
    movie_insights.movie_relations mr
ON 
    w.int64_field_0 = mr.writer_id
RIGHT JOIN 
    movie_insights.movies m
USING(movie_id)
GROUP BY 1,2
)
SELECT writer_id, writer_name, movie_count
FROM writer_movie_count
ORDER BY movie_count DESC
LIMIT 1;

-- Which star appears in the most movies?
with star_movie_count AS (
SELECT 
    s.int64_field_0 star_id,
    s.string_field_1 star_name,
    COUNT(m.movie_id) movie_count,
    RANK() OVER(ORDER BY COUNT(m.movie_id) DESC) AS movies
FROM 
    movie_insights.stars s
JOIN 
    movie_insights.movie_relations mr
ON 
    s.int64_field_0 = mr.star_id
RIGHT JOIN 
    movie_insights.movies m
USING(movie_id)
GROUP BY 1,2
)
SELECT *
FROM star_movie_count
ORDER BY movie_count DESC;

-- What is the average gross for movies directed by a specific director?
SELECT 
    d.int64_field_0 as director_id,
    d.string_field_1 as director,
    ROUND(AVG(m.gross),2) as average_gross
FROM 
    movie_insights.directors d
JOIN 
    movie_insights.movie_relations mr
ON 
    d.int64_field_0 = mr.director_id
RIGHT JOIN 
    movie_insights.movies m
USING(movie_id)
GROUP BY 1,2
ORDER BY 3 DESC;

-- Which director has the highest average score for their movies?
SELECT 
    d.int64_field_0 as director_id,
    d.string_field_1 as director,
    ROUND(AVG(m.score),2) as average_score
FROM 
    movie_insights.directors d
JOIN 
    movie_insights.movie_relations mr
ON 
    d.int64_field_0 = mr.director_id
RIGHT JOIN 
    movie_insights.movies m
USING(movie_id)
GROUP BY 1,2
ORDER BY 3 DESC
LIMIT 1;