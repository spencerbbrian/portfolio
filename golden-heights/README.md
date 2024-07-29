# GOLDEN HEIGHTS DATABASE
This is a database project for a university Golden Heights located in Boston, Massachusetts. The entire database is fictitious and has not relation to any real world University or person(s). The estimated build time for this project from planning to final push/deployment for version 1 is 1 month and 3 weeks for a beginner data engineer/intermediate data analyst. This database will be have three versions with the version showing what has been added to the database or any new functionalities.Only a maximum of 4 years is covered in this project which will be adjusted after its success. ie. No student at the moment can be in fifth year because of a trail,fail or resit.

## Version 1
Version 1 will have the student table, courses table, department table, housing table, lecturer's table as well as an advisors table with over 25000 data points for students alone across multiple disciplines.

## Tables & Column Descriptions
These descriptions are genuinely to help me code faster and work faster after deciding what tools will be used as well as the level of detail required for every column and table.

### Student Table
- First Name
- Last Name
- Gender (Uses the top 4 genders by numbers in the world: Male, Female, Transgender, Non-Binary)
- Age (Between 16 and 35 to allow for postgraduates and masters.)
- Department (64 departments grouped into 4 colleges)
- Email (Uniquely generated email for every student. Eg: bai.spen@golheights.com)
- College
- Country (Start dataset has only 123 countries listed.)
- Enrollment year(2020- 2024 only for this first try)
- Student id (uniquely generated student id based on department,enrollmentyear, and a random)
- Campus (The university has 4 campuses: Evergreen Heights, Summit Valley, Lakesdie Vista & Golden Grove). I know, very fictitious.

### Courses Table
- Course Name / Title
- Course Code (Department-Year-Number)
- Department
- Credits
- Instructor / Lecturer
- Semester (Which semester is this course taught. Winter, Spring, Fall etc)
- Year (This refers to the intended year for the course, year 1, year 2 etc)

### Lecturer Table
- First Name
- Last Name
- Employee ID
- Lecturer ID
- Department
- Position (To introduce some politics later)
- Date of hire
- Courses taught 
- Salary details

### Advisors Table
- First Name
- Last Name
- Employee ID
- Students assigned (Use IDs only to keep confidential)

### Housing Table
- Hall / Dormitory Name
- Housing Type
- Capacity
- Move in year
- Move in semester
- Students (This will be a list of students per room/studio etc)
- Rent per student

## Version 2 
Version 2 will include the grades table and enrollment table.

## Tables & Column Descriptions
### Grade Table
- Student id
- Course Code
- Grade
- Academic Year
- Semester

### Enrollment Table
- Course ID
- Student ID
- Enrollment Date
- Enrollment status (Feature will be added that will allow to check a student's balance before moving from applied, procession to enrolled. For now, it's just a reminder and will say enrolled for all)

## Version 3
The final (for now) version will include a financial aid and accounts table to take profitability the project to the next level. Later to be linked to a similar project with banks that will allow direct account balance changes from bank payments. And yes, it's still just a project.

## Tables & Column Descriptions
### Financial Aid Table
- Financial aid name
- Amount
- Student (Also a list incase its a big scholarship for more than 1 student)

### Accounts
- Student id
- Total Tuition Due
- Balance