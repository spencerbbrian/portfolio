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
1. What fraction of employees that left the company are women? Are men?
```
SELECT SUM(CASE WHEN gender = 'Female' THEN 1 ELSE 0 END) * 1.0/ COUNT(*) AS Percentage_Female_Attrition FROM attrition_main WHERE attrition = 'Yes';

```

2. What effect does your maritalk status have on income? 
3. Is there a correlation between the number of years worked and the last promotion?
4. What job levels have regular overtime hours?
5. What is the age distribution of the company by Gender?
6. Do younger people have a higher tendency to stay in the company?
