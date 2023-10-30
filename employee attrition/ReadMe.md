# Employee Attrition
This is a personal project to practice my sql, python and visualization skills.

### Project Status - Documenting & Creating Visualizations & Changes in data from 1 to 5.

## Project Intro
The purpose of this project is to uncover some underlying factors that fueld employee attrition in the company XYZ. Another goal was to uncover how successful young people are in this particular company.

### Methods Used
* Exploratory Data Analysis
* Database Design
* Data Visualization & Analysis

### Technologies Used
* Python
* Jupyter Notebook
* PgAdmin
* PostgreSQL
* PowerBi
* Tableau (To be included at the end of the week)

# Datasets
The project dataset was from [Kaggle Employee Attrition](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset)

# Remaining Tasks
* Change data point to actual text from 1 to 5 to Low to High.
* Complete entire documentation.
* Create a PowerBI dashboard.
* Create a tableau dashboard.

## QUESTIONS
1. What fraction of employees that left the company are women?
```
SELECT SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) * 1.0/ COUNT(*) AS Percentage_Female_Attrition FROM attrition_main WHERE attrition = 'Yes';

```
2. Are men?
```
SELECT SUM(CASE WHEN gender = 'Male' THEN 1 ELSE 0 END) * 1.0/ COUNT(*) AS Percentage_Male_Attrition FROM attrition_main WHERE attrition = 'Yes';

```

2. What effect does your marital status have on income? 
```
SELECT f.maritalstatus,
    SUM(
        CASE WHEN b.monthlyincome > 1000 AND b.monthlyincome < 5000 THEN 1 ELSE 0 END) AS less_than_5000,
    SUM(
        CASE WHEN b.monthlyincome > 5000 AND b.monthlyincome < 10000 THEN 1 ELSE 0 END) AS less_than_10000,
    SUM(
        CASE WHEN b.monthlyincome > 1000 AND b.monthlyincome < 5000 THEN 1 ELSE 0 END) AS more_than_enough,
    SUM(
        CASE WHEN b.monthlyincome > 15000 THEN 1 ELSE 0 END)
        AS excess
FROM benefits b
LEFT JOIN family as f
ON b.employeenumber = f.employeenumber
GROUP BY f.maritalstatus;

```

3. Is there a correlation between the number of years worked and the last promotion?

4. What job levels have regular overtime hours?
```
SELECT joblevel, overtime, COUNT(employeenumber)
FROM attrition_main
GROUP BY joblevel, overtime
ORDER BY joblevel, overtime ASC;

```

5. What is the age distribution of the company by Gender?
```
SELECT
ROUND(AVG(CASE WHEN age < 30 THEN 1 ELSE 0 END), 3) AS YoungAdult,
ROUND(AVG(CASE WHEN age >= 30 THEN 1 ELSE 0 END), 3) AS WorkingClass,
ROUND(AVG(CASE WHEN age >= 60 THEN 1 ELSE 0 END), 3) AS Retiring
FROM attrition_main

```

6. Do younger people have a higher tendency to stay in the company?

```
SELECT
ROUND(AVG(CASE WHEN age < 30 AND attrition = 'No'  THEN 1 WHEN age < 30 AND attrition = 'Yes' THEN 0 END), 3) AS YoungAdult
FROM attrition_main

```