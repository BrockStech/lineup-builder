import pandas as pd
import csv


def merge():
    dk_salaries = load("input/DKSalaries.csv")
    of_model = load("input/OFModel.csv")
    return dk_salaries.merge(of_model[["Name", "DK OF"]], on="Name", how="left")


def load(filepath):
    return pd.read_csv(filepath)


def save(header, lineups, filepath):
    with open(filepath, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(lineups)
    print("Saved lineups for upload to: {}".format(filepath))
