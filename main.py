# import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

areas = ["SBL", "SC", "ST"]
teeth = ["7D", "7M", "6D", "6M"]
tooth_side = ["DX", "SX"]
divergencies = ["IPERDIVERGENTE", "IPODIVERGENTE", "NORMODIVERGENTE"]

def create_new_columns(start_df: pd.DataFrame) -> pd.DataFrame:
    new_df = pd.DataFrame()
    is_first = True
    for area in areas:
        for tooth in teeth:
            for side in tooth_side:
                filtered_df = start_df[(start_df["SIDE"] == side) & (start_df["DENTE"] == tooth)]
                filtered_df.reset_index(inplace=True)

                col1 = f"{area}_{tooth}_6mm_{side}"
                col2 = f"{area}_{tooth}_4mm_{side}"

                new_df.insert(0, col1, filtered_df[f"{area}_6mm"])
                new_df.insert(1, col2, filtered_df[f"{area}_4mm"])

                if is_first:
                    new_df.insert(2, 'divergencies', filtered_df['DIVERGENZA'].apply(lambda x: x.strip()))
                    is_first = False

    return new_df
                

def main():
    measures = pd.read_excel("./misure_pazienti.xlsx", decimal=",")
    measures_prettified = create_new_columns(measures)

    index = 0
    ttest_df = pd.DataFrame(columns=['name', 'right', 'left', 'p-value'])
    for area in areas:
        for tooth in teeth:
            for mm in ["6mm", "4mm"]:
                name = f'{area}_{tooth}_{mm}'

                # data precision fourth decimal
                std_dx = round(measures_prettified[f'{name}_DX'].std(), 4)
                std_sx = round(measures_prettified[f'{name}_SX'].std(), 4)
                mean_dx = round(measures_prettified[f'{name}_DX'].mean(), 4)
                mean_sx = round(measures_prettified[f'{name}_SX'].mean(), 4)

                _, p_value = stats.ttest_ind(
                    measures_prettified[f'{name}_SX'],
                    measures_prettified[f'{name}_DX']
                )

                ttest_df.loc[index] = [
                    name,
                    f'{mean_sx} ± {std_sx}',
                    f'{mean_dx} ± {std_dx}',
                    p_value
                ]
                index += 1

    ttest_df.to_excel("output1.xlsx",
            sheet_name='T-test', index=False)  

    ratio = measures_prettified.groupby('divergencies').std().max() / measures_prettified.groupby('divergencies').std().min()
    print(ratio)
    ratio.to_excel("output2.xlsx",
             sheet_name='Homogeneity of variance') 


    anova_df = pd.DataFrame(columns=['name', 'ipo', 'iper', 'normo', 'p-value'])
    index = 0
    for area in areas:
        for tooth in teeth:
            for mm in ["6mm", "4mm"]:
                for side in tooth_side:
                    name = f'{area}_{tooth}_{mm}_{side}'
                    sample_df = measures_prettified[[name, 'divergencies']]

                    x_bar = sample_df[name].mean()
                    SSTR = sample_df.groupby('divergencies').count() * (sample_df.groupby('divergencies').mean() - x_bar)**2
                    SSE = (sample_df.groupby('divergencies').count() - 1) * sample_df.groupby('divergencies').std()**2

                    SS = SSTR[name].sum() + SSE[name].sum()

                    DF_betweengroups = sample_df['divergencies'].nunique() - 1
                    DF_withingroups = sample_df.shape[0] - sample_df['divergencies'].nunique()

                    MS_betweengroups = SS / DF_betweengroups 
                    MS_withingroups = SS / DF_withingroups

                    F = MS_betweengroups / MS_withingroups

                    pvalue = 1 - stats.f.cdf(F, DF_betweengroups, DF_withingroups)

                    stds = []
                    means = []
                    for divergency in divergencies:
                        stds.append(
                            sample_df[measures_prettified['divergencies'] == divergency][name].std()
                        )
                        means.append(
                            sample_df[measures_prettified['divergencies'] == divergency][name].mean()
                        )

                    anova_df.loc[index] = [
                        name,
                        f'{means[0]} ± {stds[0]}',
                        f'{means[1]} ± {stds[1]}',
                        f'{means[2]} ± {stds[2]}',
                        pvalue
                    ]
                    index += 1
                    

    print(anova_df)
    
    
    

if __name__ == "__main__":
    main()