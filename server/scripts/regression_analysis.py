#!/usr/bin/env python3
"""
GOSA Socioeconomic & GMAS Regression Analysis Engine
Calculates Ordinary Least Squares (OLS) linear regression between % Economically Disadvantaged
Students (Direct Certification) and GMAS EOG / EOC Proficiency Scores across Georgia Schools.
"""

import os
import json
import math

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gosa"))
OUTPUT_FILE = os.path.join(DATA_DIR, "regression_results.json")

# Sample Georgia Schools & Districts Regression Master Data Generator / Parser
def generate_regression_dataset():
    # Primary Subjects Analyzed
    subjects = [
        {"id": "g3_ela", "name": "Grade 3 English Language Arts (EOG)", "type": "EOG", "grade": "Grade 3"},
        {"id": "g5_math", "name": "Grade 5 Mathematics (EOG)", "type": "EOG", "grade": "Grade 5"},
        {"id": "g8_sci", "name": "Grade 8 Science (EOG)", "type": "EOG", "grade": "Grade 8"},
        {"id": "alg1_eoc", "name": "Algebra I (End of Course EOC)", "type": "EOC", "grade": "High School"},
        {"id": "bio_eoc", "name": "Biology (End of Course EOC)", "type": "EOC", "grade": "High School"}
    ]

    # Georgia School Sample Population (Representing diverse urban, suburban, and rural districts)
    schools = [
        # Columbia County Schools (Suburban Augusta / CSRA)
        {"id": "sch_636_101", "name": "Greenbrier High School", "district": "Columbia County", "districtCode": "COLCS", "ecoDisadvPct": 18.2, "g3_ela": 78.5, "g5_math": 81.2, "g8_sci": 74.6, "alg1_eoc": 82.4, "bio_eoc": 79.1},
        {"id": "sch_636_102", "name": "Lakeside High School", "district": "Columbia County", "districtCode": "COLCS", "ecoDisadvPct": 22.4, "g3_ela": 75.2, "g5_math": 78.9, "g8_sci": 71.0, "alg1_eoc": 79.8, "bio_eoc": 75.4},
        {"id": "sch_636_103", "name": "Evans High School", "district": "Columbia County", "districtCode": "COLCS", "ecoDisadvPct": 29.5, "g3_ela": 71.8, "g5_math": 74.5, "g8_sci": 67.2, "alg1_eoc": 75.1, "bio_eoc": 71.8},
        {"id": "sch_636_104", "name": "Grovetown High School", "district": "Columbia County", "districtCode": "COLCS", "ecoDisadvPct": 38.1, "g3_ela": 66.4, "g5_math": 68.2, "g8_sci": 62.5, "alg1_eoc": 69.4, "bio_eoc": 65.2},
        {"id": "sch_636_201", "name": "Riverside Middle School", "district": "Columbia County", "districtCode": "COLCS", "ecoDisadvPct": 24.1, "g3_ela": 74.1, "g5_math": 77.4, "g8_sci": 70.8, "alg1_eoc": 78.2, "bio_eoc": 73.9},

        # Richmond County Schools (Urban Augusta)
        {"id": "sch_721_101", "name": "Davidson Fine Arts Magnet", "district": "Richmond County", "districtCode": "RICH", "ecoDisadvPct": 32.0, "g3_ela": 88.4, "g5_math": 89.1, "g8_sci": 84.5, "alg1_eoc": 91.2, "bio_eoc": 88.7}, # Outperforming / Beating Odds
        {"id": "sch_721_102", "name": "Academy of Richmond County", "district": "Richmond County", "districtCode": "RICH", "ecoDisadvPct": 64.5, "g3_ela": 38.2, "g5_math": 36.4, "g8_sci": 33.1, "alg1_eoc": 41.5, "bio_eoc": 37.8},
        {"id": "sch_721_103", "name": "Lucy C. Laney High School", "district": "Richmond County", "districtCode": "RICH", "ecoDisadvPct": 78.2, "g3_ela": 26.4, "g5_math": 24.1, "g8_sci": 22.8, "alg1_eoc": 29.5, "bio_eoc": 25.4},
        {"id": "sch_721_104", "name": "Westside High School", "district": "Richmond County", "districtCode": "RICH", "ecoDisadvPct": 58.4, "g3_ela": 42.1, "g5_math": 40.5, "g8_sci": 38.2, "alg1_eoc": 46.8, "bio_eoc": 41.2},

        # Fulton County & Atlanta Metro
        {"id": "sch_660_101", "name": "Northview High School", "district": "Fulton County", "districtCode": "FULT", "ecoDisadvPct": 8.5, "g3_ela": 86.2, "g5_math": 88.9, "g8_sci": 82.1, "alg1_eoc": 89.5, "bio_eoc": 86.4},
        {"id": "sch_660_102", "name": "Chattahoochee High School", "district": "Fulton County", "districtCode": "FULT", "ecoDisadvPct": 12.1, "g3_ela": 82.5, "g5_math": 84.8, "g8_sci": 79.4, "alg1_eoc": 85.1, "bio_eoc": 82.0},
        {"id": "sch_660_103", "name": "Banneker High School", "district": "Fulton County", "districtCode": "FULT", "ecoDisadvPct": 72.4, "g3_ela": 31.5, "g5_math": 29.8, "g8_sci": 27.4, "alg1_eoc": 34.2, "bio_eoc": 30.1},

        # Gwinnett County
        {"id": "sch_667_101", "name": "GSMST (Gwinnett Math & Tech)", "district": "Gwinnett County", "districtCode": "GWIN", "ecoDisadvPct": 21.0, "g3_ela": 94.2, "g5_math": 96.8, "g8_sci": 92.4, "alg1_eoc": 97.5, "bio_eoc": 95.1}, # High Outlier
        {"id": "sch_667_102", "name": "Brookwood High School", "district": "Gwinnett County", "districtCode": "GWIN", "ecoDisadvPct": 26.8, "g3_ela": 72.4, "g5_math": 75.1, "g8_sci": 68.9, "alg1_eoc": 76.4, "bio_eoc": 73.2},
        {"id": "sch_667_103", "name": "Norcross High School", "district": "Gwinnett County", "districtCode": "GWIN", "ecoDisadvPct": 56.2, "g3_ela": 45.8, "g5_math": 47.2, "g8_sci": 42.1, "alg1_eoc": 50.4, "bio_eoc": 46.5},

        # Rural Georgia Districts
        {"id": "sch_601_101", "name": "Appling County High School", "district": "Appling County", "districtCode": "APPL", "ecoDisadvPct": 52.1, "g3_ela": 49.2, "g5_math": 51.4, "g8_sci": 46.8, "alg1_eoc": 53.2, "bio_eoc": 48.9},
        {"id": "sch_723_101", "name": "Savannah Arts Academy", "district": "Savannah-Chatham", "districtCode": "SAV", "ecoDisadvPct": 25.4, "g3_ela": 84.1, "g5_math": 86.2, "g8_sci": 80.5, "alg1_eoc": 87.4, "bio_eoc": 83.9}
    ]

    regression_results = {}

    for sub in subjects:
        sub_id = sub["id"]
        x_vals = [] # ecoDisadvPct
        y_vals = [] # score

        data_points = []

        for sch in schools:
            x = sch["ecoDisadvPct"]
            y = sch[sub_id]
            x_vals.append(x)
            y_vals.append(y)
            data_points.append({
                "schoolId": sch["id"],
                "schoolName": sch["name"],
                "district": sch["district"],
                "districtCode": sch["districtCode"],
                "ecoDisadvPct": x,
                "score": y
            })

        # Calculate Ordinary Least Squares (OLS) Linear Regression Parameters
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x ** 2 for x in x_vals)
        sum_y2 = sum(y ** 2 for y in y_vals)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n

        # Correlation R and R^2
        numerator = (n * sum_xy - sum_x * sum_y)
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        r = numerator / denominator if denominator != 0 else 0
        r_squared = r ** 2

        # Compute Residuals & Beating the Odds Status
        processed_points = []
        for pt in data_points:
            x = pt["ecoDisadvPct"]
            y = pt["score"]
            predicted = slope * x + intercept
            residual = y - predicted # Residual = Actual - Predicted

            status = "On Par"
            if residual >= 10.0:
                status = "Significantly Outperforming (Beating Odds ★)"
            elif residual >= 4.0:
                status = "Above Expected"
            elif residual <= -10.0:
                status = "Significantly Underperforming"
            elif residual <= -4.0:
                status = "Below Expected"

            processed_points.append({
                **pt,
                "predictedScore": round(predicted, 1),
                "residual": round(residual, 1),
                "performanceStatus": status
            })

        # Sort processed points by residual descending
        processed_points.sort(key=lambda item: item["residual"], reverse=True)

        regression_results[sub_id] = {
            "subjectId": sub_id,
            "subjectName": sub["name"],
            "category": sub["type"],
            "gradeLevel": sub["grade"],
            "ols": {
                "slope": round(slope, 3),
                "intercept": round(intercept, 2),
                "rSquared": round(r_squared, 3),
                "r": round(r, 3),
                "equation": f"Predicted Score = {round(intercept, 1)} + ({round(slope, 2)} × % Economically Disadvantaged)"
            },
            "dataPoints": processed_points
        }

    output = {
        "generatedAt": "2026-07-27T23:27:00Z",
        "subjects": subjects,
        "results": regression_results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"Regression analysis generated successfully for {len(subjects)} subjects across {len(schools)} Georgia schools.")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_regression_dataset()
