# Module 2 Project — 5-Minute Presentation Notes

These notes are for you to read from while presenting. Instructions in brackets are actions, not words to say aloud.

## 0:00-1:30 — Raw Data vs. Clean Data

[SHOW: the raw `data/messy_employee_survey.csv` file. Find employee_id 28 if possible.]

SAY:

Hi, this is my Module 2 employee survey data pipeline. The goal of the project was to take a messy CSV file, clean it, analyze it, create visualizations, and export a cleaned version.

One example of the messy data is employee 28. In the raw file, the department is written as `Eng`, the office location is lowercase `seattle`, and the salary is stored as the string `$86,963.55`.

[SHOW: `output/clean_data.csv`, employee_id 28.]

SAY:

After the cleaning pipeline runs, `Eng` becomes `Engineering`, `seattle` becomes `Seattle`, and the salary becomes a numeric value that pandas can actually analyze.

The pipeline also removes duplicate employee IDs, handles missing values, fixes negative salaries, checks satisfaction scores are between 1 and 10, and parses the different survey date formats.

[DO NOT SAY: every single cleaning rule unless the instructor asks.]

## 1:30-2:45 — Design Decision

[SHOW: `pipeline.py`. Scroll to the `DataPipeline` class and then the `clean()` method.]

SAY:

I organized the project into a `DataPipeline` class because each stage has a separate responsibility. The constructor loads the data, `clean` fixes it, `analyze` calculates the results, `visualize` creates the charts, and `export` saves the cleaned CSV. Then `run` executes those stages in order.

One design decision I made was how to handle missing numeric values. I didn't want to automatically delete an entire employee row just because salary, experience, or satisfaction was missing. Instead, I use the median for that employee's department first, and then the overall median as a fallback.

I chose the median instead of the mean because the median is less affected by unusually high or low values.

[DO NOT SAY: "AI told me to use the median." Just explain the reasoning above.]

## 2:45-4:15 — Visualization and Insight

[SHOW: `output/charts.png`. Point to the average salary chart first.]

SAY:

This file contains the visualizations created by the pipeline. The first chart compares average salary by department. In the cleaned data, HR and Marketing have some of the highest average salaries, while Finance is lower.

[POINT TO: satisfaction distribution or headcount chart.]

SAY:

I also created a histogram of satisfaction scores and a headcount chart by office location. Austin has the highest headcount in this dataset.

One result that surprised me was the correlation between years of experience and salary. The correlation is only about 0.03, which is very close to zero. In this fictional dataset, years of experience does not have a strong linear relationship with salary.

## 4:15-5:00 — Wrap-Up

[SHOW: terminal after running `python main.py`, or leave `charts.png` visible.]

SAY:

The biggest challenge was deciding how to handle bad data without losing too many rows. For example, a negative salary is clearly invalid, but deleting that employee would also throw away all of their other valid survey information.

My solution was to convert invalid values to missing values and then use a consistent replacement strategy. I also used safe numeric conversion and try-except blocks so unexpected input would not crash the entire pipeline.

Overall, this project helped me connect pandas cleaning and analysis with OOP and visualization in one reusable pipeline.

[STOP. Do not pad the presentation if you are already near five minutes.]
