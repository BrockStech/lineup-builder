from src.csv import *
from src.optimizer import Optimizer
from config import *


def run():
    data = merge()
    opt = Optimizer(data)
    lineups = opt.generate(formula=opt.optimize)
    filled_lineups = opt.fill(lineups)
    display(filled_lineups)
    save(roster, filled_lineups, "output/view.csv")
    roster.remove('OF')
    roster.remove('SALARY')
    save(roster, [lineup[:-2] for lineup in filled_lineups], "output/upload.csv")


def display(lineups):
    df = pd.DataFrame(lineups)
    print("\nCPT OWNERSHIP:")
    print(df[0].value_counts())
    print("\nFLEX OWNERSHIP:")
    df2 = df[1].append(df[2].append(df[3].append(df[4].append(df[5]))))
    print(df2.value_counts())
    print("\n")
