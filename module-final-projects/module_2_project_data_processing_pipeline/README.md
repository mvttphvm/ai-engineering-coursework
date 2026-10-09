# Module 2 Project: Employee Survey Data Pipeline

# Overview

This project uses Python, pandas, regular expressions, object-oriented programming, and matplotlib to clean and analyze a messy employee survey dataset.
The pipeline loads the raw CSV, removes duplicate employees, standardizes inconsistent text, fixes invalid numeric values, handles missing data, parses multiple date formats, calculates summary statistics, creates charts, and exports a cleaned CSV.

# Project Structure

```text
module_02_project/
├── data/
│   └── messy_employee_survey.csv
├── output/
│   ├── charts.png
│   └── clean_data.csv
├── pipeline.py
├── main.py
├── requirements.txt
└── README.md
```

# Setup

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the project:

```bash
python main.py
```

# Cleaning Strategy

The `DataPipeline.clean()` method handles the dataset one column at a time.

- `employee_id`: duplicate IDs are removed, keeping the first occurrence. Rows without an ID are dropped because the employee cannot be uniquely identified.
- `name`: whitespace is removed and names are converted to title case.
- `department`: whitespace/casing differences and abbreviations such as `Eng`, `ENGINEERING`, `Mktg`, and `Fin` are mapped to standard department names.
- `office_location`: values such as `NYC`, `new york`, `ATX`, and `work from home` are normalized.
- `salary`: `$` signs and commas are removed with regex, values are converted to numbers, and negative salaries are treated as missing.
- `years_experience`: values are converted to numeric. Values below 0 or above 50 are treated as invalid.
- `satisfaction_score`: values are converted to numeric. Scores outside the valid 1-10 range are treated as invalid.
- `survey_date`: three formats are supported: `MM/DD/YYYY`, `YYYY-MM-DD`, and `DD-MM-YYYY`.
- `comments`: missing comments become `No comment provided`.

For missing numeric values, I fill with the median for that employee's department first. If a department has no valid values for that column, I use the overall median instead. This keeps the employee row while avoiding a single extreme value having too much influence on the replacement value.
If a survey date cannot be parsed, the median valid survey date is used. Missing text categories become `Unknown`.

# Analysis

The project calculates:

1. Average salary by department
2. Average satisfaction score by department
3. Headcount by office location
4. Pearson correlation between years of experience and salary
5. Average satisfaction score by office location

# Visualizations

`output/charts.png` contains:

- Average salary by department bar chart
- Satisfaction score histogram
- Headcount by office location horizontal bar chart

# Dataset Results

The raw dataset contains 200 rows. Cleaning removes 10 duplicate employee IDs, leaving 190 employees.
In this dataset, 10 negative salary values are treated as invalid and repaired through the missing-value strategy. There are also invalid satisfaction scores outside the 1-10 range.
One useful result from the analysis is that the correlation between years of experience and salary is very close to zero in this fictional dataset, so more experience does not appear strongly associated with higher salary here.

# Error Handling

The pipeline uses `try/except` around file loading and output operations. Numeric conversions use safe conversion logic so unexpected strings become missing values instead of crashing the program. The pipeline also checks whether data loaded successfully before cleaning, analyzing, visualizing, or exporting.
