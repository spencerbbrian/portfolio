## Table of Contents
* [Datasets](#dataset)
* [Exploratory Data Analysis](#eda)
* [Questions](#questions)
* [Relational Database](#relational-database)

## Datasets
The project utilised just one dataset further split for normalization purposes.
The dataset was downloaded from Kaggle. The link to that dataset can be found [here](https://www.kaggle.com/datasets/shilongzhuang/pizza-sales). :point_left:

### NORMALIZED DATASETS
- Orders Table: A table for every order placed, the time it was placed, the kind of pizza and any other pizza or user purchase detail.
- Pizza :pizza: Table: A table for all pizzas created by the pizza place, its details and category.
- Categories Table: A table for all the various pizza categories.

## Exploratory Data Analysis
### Steps
- Import libraries and datasets.
- Check for missing or null values.
- Check datatypes for each attribute.
- 

## Relational Database 
To reduce the effect of data redundancy, the entire dataset was split into 3 with orders as the facts table and the pizzas and categories table used for normalization purposes.
The relational database diagram for this project can be found below using [Quick DB](https://www.quickdatabasediagrams.com/)

![Pizza Sales Relational Database Diagram](./table%20schema.png)