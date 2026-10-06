import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


class DataPipeline:
    """A reusable data processing pipeline for employee survey data."""

    DEPT_MAP = {
        "engineering": "Engineering",
        "eng": "Engineering",
        "marketing": "Marketing",
        "mktg": "Marketing",
        "sales": "Sales",
        "hr": "HR",
        "human resources": "HR",
        "h.r.": "HR",
        "finance": "Finance",
        "fin": "Finance",
    }

    LOC_MAP = {
        "new york": "New York",
        "nyc": "New York",
        "chicago": "Chicago",
        "chi": "Chicago",
        "austin": "Austin",
        "austin, tx": "Austin",
        "atx": "Austin",
        "seattle": "Seattle",
        "sea": "Seattle",
        "remote": "Remote",
        "work from home": "Remote",
    }

    def __init__(self, filepath):
        """Load the raw CSV file into a pandas DataFrame."""
        self.filepath = filepath
        self.df = None

        try:
            self.df = pd.read_csv(filepath)
            print(f"Loaded {self.df.shape[0]} rows and {self.df.shape[1]} columns.")
        except FileNotFoundError:
            print(f"Error: could not find file: {filepath}")
        except pd.errors.EmptyDataError:
            print("Error: the CSV file is empty.")
        except Exception as error:
            print(f"Error loading CSV: {error}")

    def clean(self):
        """Run all required cleaning steps and return self for method chaining."""
        if self.df is None:
            print("No data is loaded, so cleaning cannot continue.")
            return self

        df = self.df.copy()
        starting_rows = len(df)

        # employee_id is the unique identifier, so duplicate IDs keep the first row.
        df = df.drop_duplicates(subset=["employee_id"], keep="first").copy()
        duplicates_removed = starting_rows - len(df)

        # Rows without an employee ID cannot be reliably identified, so remove them.
        missing_ids = int(df["employee_id"].isna().sum())
        if missing_ids:
            df = df.dropna(subset=["employee_id"]).copy()

        # Standardize text so the same value is not treated as multiple categories.
        df["name"] = df["name"].astype("string").str.strip().str.title()

        dept_clean = df["department"].astype("string").str.strip().str.lower()
        df["department"] = dept_clean.map(self.DEPT_MAP)
        df["department"] = df["department"].fillna(dept_clean.str.title())

        location_clean = df["office_location"].astype("string").str.strip().str.lower()
        df["office_location"] = location_clean.map(self.LOC_MAP)
        df["office_location"] = df["office_location"].fillna(location_clean.str.title())

        def clean_salary(value):
            """Convert salary strings like '$75,000' to a float."""
            if pd.isna(value):
                return None
            try:
                cleaned = re.sub(r"[$,]", "", str(value)).strip()
                salary = float(cleaned)
                if salary < 0:
                    return None
                return salary
            except (ValueError, TypeError):
                return None

        salary_before = pd.to_numeric(
            df["salary"].astype("string").str.replace(r"[$,]", "", regex=True),
            errors="coerce",
        )
        invalid_salaries = int((salary_before < 0).sum())
        df["salary"] = df["salary"].apply(clean_salary)

        # Experience should be realistic for this dataset: 0 through 50 years.
        df["years_experience"] = pd.to_numeric(df["years_experience"], errors="coerce")
        invalid_experience = int(
            ((df["years_experience"] < 0) | (df["years_experience"] > 50)).sum()
        )
        df.loc[
            (df["years_experience"] < 0) | (df["years_experience"] > 50),
            "years_experience",
        ] = None

        # Satisfaction is defined as a 1-10 score.
        df["satisfaction_score"] = pd.to_numeric(
            df["satisfaction_score"], errors="coerce"
        )
        invalid_satisfaction = int(
            ((df["satisfaction_score"] < 1) | (df["satisfaction_score"] > 10)).sum()
        )
        df.loc[
            (df["satisfaction_score"] < 1) | (df["satisfaction_score"] > 10),
            "satisfaction_score",
        ] = None

        def parse_date(value):
            """Try the three date formats used in the survey file."""
            if pd.isna(value):
                return pd.NaT

            for date_format in ("%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return pd.to_datetime(value, format=date_format)
                except (ValueError, TypeError):
                    continue
            return pd.NaT

        df["survey_date"] = df["survey_date"].apply(parse_date)
        unparsed_dates = int(df["survey_date"].isna().sum())

        missing_before_fill = int(df.isna().sum().sum())

        # Missing text values get a clear placeholder rather than deleting the row.
        df["name"] = df["name"].fillna("Unknown")
        df["department"] = df["department"].fillna("Unknown")
        df["office_location"] = df["office_location"].fillna("Unknown")
        df["comments"] = df["comments"].fillna("No comment provided")
        df["comments"] = df["comments"].astype("string").str.strip()
        df.loc[df["comments"] == "", "comments"] = "No comment provided"

        # Fill numeric values with the department median first, then overall median.
        for column in ["salary", "years_experience", "satisfaction_score"]:
            department_median = df.groupby("department")[column].transform("median")
            df[column] = df[column].fillna(department_median)
            df[column] = df[column].fillna(df[column].median())

        # If a date could not be parsed, use the median valid survey date.
        if df["survey_date"].isna().any() and df["survey_date"].notna().any():
            valid_dates = df["survey_date"].dropna().sort_values().reset_index(drop=True)
            median_date = valid_dates.iloc[len(valid_dates) // 2]
            df["survey_date"] = df["survey_date"].fillna(median_date)

        missing_after_fill = int(df.isna().sum().sum())
        missing_fixed = missing_before_fill - missing_after_fill

        self.df = df

        print("\n=== Cleaning Summary ===")
        print(f"Removed duplicate employee IDs: {duplicates_removed}")
        print(f"Dropped rows missing employee_id: {missing_ids}")
        print(f"Invalid negative salaries fixed: {invalid_salaries}")
        print(f"Invalid experience values fixed: {invalid_experience}")
        print(f"Invalid satisfaction scores fixed: {invalid_satisfaction}")
        print(f"Unparsed/missing survey dates handled: {unparsed_dates}")
        print(f"Missing values filled: {missing_fixed}")
        print(f"Rows after cleaning: {len(df)}")
        print(f"Remaining missing values: {missing_after_fill}")

        return self

    def analyze(self):
        """Calculate and return the required analysis results."""
        if self.df is None:
            print("No data is loaded, so analysis cannot continue.")
            return {}

        df = self.df

        avg_salary_by_dept = df.groupby("department")["salary"].mean().round(2)
        avg_satisfaction_by_dept = (
            df.groupby("department")["satisfaction_score"].mean().round(2)
        )
        headcount_by_location = df["office_location"].value_counts()

        correlation_data = df[["years_experience", "salary"]].dropna()
        if len(correlation_data) >= 2:
            experience_salary_correlation = round(
                correlation_data["years_experience"].corr(correlation_data["salary"]), 3
            )
        else:
            experience_salary_correlation = None

        # Extra insight: compare employee satisfaction across office locations.
        avg_satisfaction_by_location = (
            df.groupby("office_location")["satisfaction_score"].mean().round(2)
        )

        results = {
            "avg_salary_by_dept": avg_salary_by_dept,
            "avg_satisfaction_by_dept": avg_satisfaction_by_dept,
            "headcount_by_location": headcount_by_location,
            "experience_salary_correlation": experience_salary_correlation,
            "avg_satisfaction_by_location": avg_satisfaction_by_location,
        }

        print("\n=== Analysis ===")
        print("\nAverage salary by department:")
        print(avg_salary_by_dept)
        print("\nAverage satisfaction by department:")
        print(avg_satisfaction_by_dept)
        print("\nHeadcount by office location:")
        print(headcount_by_location)
        print(
            "\nYears of experience / salary correlation:",
            experience_salary_correlation,
        )
        print("\nAverage satisfaction by office location:")
        print(avg_satisfaction_by_location)

        return results

    def visualize(self, output_path="output/charts.png"):
        """Create the required charts and save them to one PNG file."""
        if self.df is None:
            print("No data is loaded, so charts cannot be created.")
            return

        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            avg_salary = self.df.groupby("department")["salary"].mean().sort_values()
            headcount = self.df["office_location"].value_counts().sort_values()

            fig, axes = plt.subplots(1, 3, figsize=(16, 5))

            avg_salary.plot(kind="bar", ax=axes[0])
            axes[0].set_title("Average Salary by Department")
            axes[0].set_xlabel("Department")
            axes[0].set_ylabel("Average Salary ($)")
            axes[0].tick_params(axis="x", rotation=45)

            axes[1].hist(
                self.df["satisfaction_score"].dropna(),
                bins=range(1, 12),
                edgecolor="black",
            )
            axes[1].set_title("Satisfaction Score Distribution")
            axes[1].set_xlabel("Satisfaction Score")
            axes[1].set_ylabel("Number of Employees")
            axes[1].set_xticks(range(1, 11))

            headcount.plot(kind="barh", ax=axes[2])
            axes[2].set_title("Headcount by Office Location")
            axes[2].set_xlabel("Employees")
            axes[2].set_ylabel("Office Location")

            plt.tight_layout()
            plt.savefig(output_path, dpi=120, bbox_inches="tight")
            plt.close()

            print(f"\nSaved charts to: {output_path}")
        except Exception as error:
            print(f"Error creating visualizations: {error}")

    def export(self, output_path="output/clean_data.csv"):
        """Export the cleaned DataFrame to a CSV file."""
        if self.df is None:
            print("No data is loaded, so export cannot continue.")
            return

        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            self.df.to_csv(output_path, index=False)
            print(f"Saved cleaned data to: {output_path}")
        except (OSError, PermissionError) as error:
            print(f"Error exporting cleaned data: {error}")

    def run(self):
        """Execute the full pipeline: clean, analyze, visualize, and export."""
        if self.df is None:
            print("Pipeline stopped because the input data could not be loaded.")
            return {}

        output_dir = os.path.join(os.path.dirname(__file__), "output")
        chart_path = os.path.join(output_dir, "charts.png")
        clean_data_path = os.path.join(output_dir, "clean_data.csv")

        self.clean()
        results = self.analyze()
        self.visualize(chart_path)
        self.export(clean_data_path)

        return results
