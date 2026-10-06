import os
from pipeline import DataPipeline


DATA_PATH = os.path.join(
    os.path.dirname(__file__), "data", "messy_employee_survey.csv"
)


def main():
    """Run the employee survey data pipeline and print a short summary."""
    print("=" * 60)
    print("Employee Survey Data Pipeline")
    print("=" * 60)

    pipeline = DataPipeline(DATA_PATH)
    results = pipeline.run()

    if not results:
        return

    print("\n=== Analysis Results ===")
    print("Average salary by department:")
    print(results["avg_salary_by_dept"])

    print("\nAverage satisfaction by department:")
    print(results["avg_satisfaction_by_dept"])

    print("\nHeadcount by location:")
    print(results["headcount_by_location"])

    print(
        "\nExperience/salary correlation:",
        results["experience_salary_correlation"],
    )

    print("\nAverage satisfaction by location:")
    print(results["avg_satisfaction_by_location"])


if __name__ == "__main__":
    main()
