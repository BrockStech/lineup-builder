from config import *
import pandas as pd
import pulp
from tqdm import tqdm


class Optimizer:
    def __init__(self, data):
        self.data = data
        self.cpt_df = self.get_position('CPT')
        self.flex_df = self.get_position('FLEX')
        self.len_cpt = len(self.cpt_df.index)
        self.len_flex = len(self.flex_df.index)
        self.cpt_index = self.cpt_df.index
        self.flex_index = self.flex_df.index
        self.corresponding_flex = self.get_corresponding_flex()
        self.solver = pulp.PULP_CBC_CMD(msg=False)
        self.set_cpt_value()

    def get_position(self, position):
        return self.data.loc[(self.data['Roster Position'] == position)
                             & (pd.notna(self.data['DK OF']))].copy(deep=True)

    def set_cpt_value(self):
        self.cpt_df.loc[:, 'DK OF'] *= 1.5

    def get_corresponding_flex(self):
        corresponding_flex = []
        for player_opp in self.flex_df.loc[:, 'Name']:
            corresponding_flex.append([1 if player_opp == team else 0 for team in self.cpt_df.loc[:, 'Name']])
        return corresponding_flex

    def optimize(self, lineups):
        prob = pulp.LpProblem('NFL', pulp.LpMaximize)

        # define the player and goalie variables
        cpt_lineup = [pulp.LpVariable("cpt_{}".format(i), cat="Binary") for i in self.cpt_index]
        flex_lineup = [pulp.LpVariable("flex_{}".format(i), cat="Binary") for i in self.flex_index]

        # add the max player constraints
        prob += (pulp.lpSum(cpt_lineup[i] for i in range(self.len_cpt)) == cpt_roster_spots)
        prob += (pulp.lpSum(flex_lineup[i] for i in range(self.len_flex)) == flex_roster_spots)

        prob += ((pulp.lpSum(self.cpt_df.loc[self.cpt_index[i], 'Salary'] * cpt_lineup[i]
                             for i in range(self.len_cpt))
                  +
                  pulp.lpSum(self.flex_df.loc[self.flex_index[i], 'Salary'] * flex_lineup[i]
                             for i in range(self.len_flex)))
                 <= salary_cap)

        prob += ((pulp.lpSum(self.cpt_df.loc[self.cpt_index[i], 'Salary'] * cpt_lineup[i]
                             for i in range(self.len_cpt))
                  +
                  pulp.lpSum(self.flex_df.loc[self.flex_index[i], 'Salary'] * flex_lineup[i]
                             for i in range(self.len_flex)))
                 >= salary_min)

        for i in range(self.len_cpt):
            prob += (flex_roster_spots * cpt_lineup[i] + pulp.lpSum(self.corresponding_flex[k][i] * flex_lineup[k]
                                                                    for k in range(self.len_flex)) <= flex_roster_spots)

        for i in range(len(lineups)):
            prob += ((pulp.lpSum(lineups[i][k] * cpt_lineup[k]
                                 for k in range(self.len_cpt))
                      +
                      pulp.lpSum(lineups[i][self.len_cpt + k] * flex_lineup[k]
                                 for k in range(self.len_flex)))
                     <= 5)

        prob += pulp.lpSum((pulp.lpSum(self.cpt_df.loc[self.cpt_index[i], 'DK OF'] * cpt_lineup[i]
                                       for i in range(self.len_cpt))
                            +
                            pulp.lpSum(self.flex_df.loc[self.flex_index[i], 'DK OF'] * flex_lineup[i]
                                       for i in range(self.len_flex))))

        status = prob.solve(self.solver)

        if status != pulp.LpStatusOptimal:
            print('Not enough feasible lineups produced/n')
            return None

        # Puts the output of one lineup into a format that will be used later
        lineup_copy = []
        for i in range(self.len_cpt):
            if cpt_lineup[i].varValue == 1:
                lineup_copy.append(1)
            else:
                lineup_copy.append(0)
        for i in range(self.len_flex):
            if flex_lineup[i].varValue == 1:
                lineup_copy.append(1)
            else:
                lineup_copy.append(0)
        return lineup_copy

    def generate(self, formula):
        lineups = []
        for _ in tqdm(range(max_lineups)):
            lineup = formula(lineups)
            if lineup:
                lineups.append(lineup)
            else:
                break
        return lineups

    def fill(self, lineups):
        filled_lineups = []
        for lineup in lineups:
            lineup_pos = 0
            expected_of = 0
            total_salary = 0
            new_lineup = ["", "", "", "", "", "", "", ""]
            for i in range(self.len_cpt + self.len_flex):
                if lineup[i] == 1:
                    if lineup_pos == 0:
                        new_lineup[lineup_pos] = self.cpt_df.loc[self.cpt_index[i], 'Name + ID']
                        expected_of += self.cpt_df.loc[self.cpt_index[i], 'DK OF']
                        total_salary += self.cpt_df.loc[self.cpt_index[i], 'Salary']
                        lineup_pos += 1
                    else:
                        new_lineup[lineup_pos] = self.flex_df.loc[self.flex_index[i - self.len_cpt], 'Name + ID']
                        expected_of += self.flex_df.loc[self.flex_index[i - self.len_cpt], 'DK OF']
                        total_salary += self.flex_df.loc[self.flex_index[i - self.len_cpt], 'Salary']
                        lineup_pos += 1
            new_lineup[lineup_pos] = round(expected_of, 2)
            lineup_pos += 1
            new_lineup[lineup_pos] = total_salary
            filled_lineups.append(new_lineup)
        filled_lineups.sort(key=lambda x: x[6], reverse=True)
        return filled_lineups
