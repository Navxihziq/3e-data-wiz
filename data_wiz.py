import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# the default first 5 indexes of headers
header_first_5 = ['nonsense', '年份', '电网区域', '省份', '省下区域', 'Tech']


class RefData:
    def __init__(self, path_to_ref):
        self.dataframe = pd.read_excel(path_to_ref)
        self.color_scheme = self.__read_color_scheme()
        self.tech_fuel_group_dict = self.__read_tech_fuel_group_dict()
        self.order_list = self.__read_order_list()

    def __read_color_scheme(self):
        return dict(self.dataframe[['Fuel_Group', "HEX"]].dropna(how="all").values)

    def __read_tech_fuel_group_dict(self):
        return dict(self.dataframe[['Tech', 'Fuel_Group']].values)

    def __read_order_list(self):
        return self.dataframe.dropna().sort_values(by='Order', ascending=True)['Fuel_Group'].unique().tolist()

    def get_stack_order(self, fuel_group: list):
        ls = []
        for group in self.order_list:
            if group in fuel_group:
                ls.append(group)

        return ls


class WorkingData:
    def __init__(self, file_info: list, ref: RefData):
        self.tech_specific = None
        self.regional_agg_level = None
        self.working_df = None
        self.ref = ref
        self.dataframe = self.init_dataframe(file_info)

    def init_dataframe(self, file_info: list) -> pd.DataFrame:
        # read the files
        file_1 = pd.read_excel(file_info[0]['path'])
        file_2 = pd.read_excel(file_info[1]['path'])

        file_1.columns = header_first_5 + file_info[0]['columns']
        file_1 = file_1[header_first_5 + [file_info[0]['focused_index']]]
        file_2.columns = header_first_5 + file_info[1]['columns']
        file_2 = file_2[header_first_5 + [file_info[1]['focused_index']]]

        # join the second dataframe to the first one
        dataframe = file_1.merge(file_2, how="outer", on=header_first_5)

        # map the fuel group value from tech column
        dataframe['Fuel_Group'] = dataframe['Tech'].map(self.ref.tech_fuel_group_dict)
        # drop empty and 0 rows
        dataframe = dataframe[~((dataframe[file_info[0]['focused_index']] == 0.0) & (
                dataframe[file_info[1]['focused_index']] == 0.0))].dropna(how="all")

        return dataframe

    def rule_out(self, regional_agg_level: str, selected_tech_group=None, tech_group_select_reverse=True,
                 selected_region=None, region_select_reverse=True):
        # make a copy of the dataframe as working dataframe
        working_df = self.dataframe.copy()

        # choosing specific tech groups
        if selected_tech_group is None:
            selected_tech_group = []

        if tech_group_select_reverse:
            working_df = working_df[~working_df['Fuel_Group'].isin(selected_tech_group)]
        else:
            working_df = working_df[~working_df['Fuel_Group'].isin(selected_tech_group)]

        if selected_region is None:
            selected_region = []

        if regional_agg_level == "全国":
            working_df = working_df.groupby(by=['年份', 'Fuel_Group']).sum().reset_index()
        else:
            working_df = working_df.groupby(by=['年份', 'Fuel_Group', regional_agg_level]).sum().reset_index()
            if region_select_reverse:
                working_df = working_df[~working_df[regional_agg_level].isin(selected_region)]
            else:
                working_df = working_df[working_df[regional_agg_level].isin(selected_region)]

        self.regional_agg_level = regional_agg_level
        self.working_df = working_df
        return working_df

    def calc_complex_index(self, dividend: str, divisor: str, factor=False, tech_specific=False):
        self.tech_specific = tech_specific
        if not tech_specific:
            # create a dict: year -> complex value
            temp = self.working_df.copy()
            temp = temp.groupby(by=['年份']).sum().reset_index()
            temp['Complex'] = temp[dividend] / temp[divisor]

            self.working_df['Complex'] = self.working_df['年份'].map(dict(temp[['年份', 'Complex']].values))
            return self.working_df

        else:
            if not factor:
                self.working_df['Complex'] = self.working_df[dividend] / self.working_df[divisor]
                return self.working_df

            else:
                self.working_df['Complex'] = self.working_df['Complex'] / 8760
            return self.working_df

    def draw(self, focused_index: str, focused_region=None, scatter=False):
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 20), dpi=300)

        ax2 = ax.twinx()

        if focused_region is None and (self.regional_agg_level != "全国"):
            raise Exception

        if self.regional_agg_level == "全国":
            self.working_df = self.working_df.set_index("年份")
        else:
            self.working_df = self.working_df[self.working_df[self.regional_agg_level] == focused_region].drop(
                columns=[self.regional_agg_level]).set_index("年份")

        # transpose the data for plotting
        self.working_df = self.__transpose_dataframe()
        self.working_df.index = self.working_df.index.map(int).map(str)

        # line plot section
        line_df = self.working_df[self.working_df['index'] == "Complex"]

        # bar plot section
        bar_df = self.working_df[self.working_df['index'] != 'Complex']
        bar_df = bar_df[bar_df['index'] == focused_index]  # choose the index to plot in bar plot

        if scatter:
            if self.tech_specific:
                bar_df_long = bar_df.reset_index().drop(columns=['index']).melt(id_vars='年份', value_name='bar_value')
                line_df_long = line_df.reset_index().drop(columns=['index']).melt(id_vars='年份', value_name='复合指标')
                sns.barplot(data=bar_df_long, x='年份', y='bar_value', dodge=True, hue='variable',
                            palette=self.ref.color_scheme, ax=ax)
                sns.stripplot(data=line_df_long, x='年份', y='复合指标', dodge=True, jitter=False, hue='variable',
                              palette=self.ref.color_scheme, edgecolor='white', linewidth=1, ax=ax2)
                ax.set(ylabel=None)
                ax2.set(ylabel=None)

            else:
                line_df = line_df.loc[:, (line_df != 0).any(axis=0)]
                bar_df.plot(kind='bar', stacked=True,
                            color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns], ax=ax)
                sns.scatterplot(data=line_df, ax=ax2)
        else:
            line_df = line_df.loc[:, (line_df != 0).any(axis=0)]
            if self.tech_specific:
                bar_df.plot(kind='bar', color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns], ax=ax)
                line_df = line_df.dropna(axis="columns", how="any").iloc[:, :1]
                sns.lineplot(data=line_df, color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns],
                             marker='o', ax=ax2)

            else:
                bar_df.plot(kind='bar', stacked=True,
                            color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns], ax=ax)
                sns.lineplot(data=line_df, color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns],
                             marker='o', ax=ax2)

        bar_df.to_excel("./checking/bar_plot_sheet.xlsx", encoding='utf-8')  # saving the bar plot data to excel

        ax.legend().remove()  # remove the legend of the bar plot
        ax2.legend().remove()  # remove the legend of line plot

        ax.set_yscale('log')  # set y-axis scale to log
        line_df.to_excel("./checking/line_plot_sheet.xlsx", encoding='utf-8')

        fig.savefig("./checking/checking_graph.png", dpi=300)  # saving the graph to file

        plt.show()

    def __transpose_dataframe(self, working_df=None):
        if working_df is None:
            tech_group_order = self.ref.get_stack_order(self.working_df['Fuel_Group'].unique().tolist())
            # make a new dataframe
            recomb = pd.DataFrame(columns=tech_group_order)

            for idx in set(self.working_df.index):
                temp = self.working_df.loc[[idx]].set_index("Fuel_Group").transpose()
                temp = temp.reset_index()
                temp[self.working_df.index.name] = idx
                recomb = pd.concat([recomb, temp], ignore_index=True)

            recomb = recomb.set_index(self.working_df.index.name)

        else:
            tech_group_order = self.ref.get_stack_order(working_df['Fuel_Group'].unique().tolist())
            # make a new dataframe
            recomb = pd.DataFrame(columns=tech_group_order)

            for idx in set(working_df.index):
                temp = working_df.loc[[idx]].set_index("Fuel_Group").transpose()
                temp = temp.reset_index()
                temp[working_df.index.name] = idx
                recomb = pd.concat([recomb, temp], ignore_index=True)

            recomb = recomb.set_index(working_df.index.name)

        return recomb.sort_index()

    def draw_sub_lineplot(self, focused_index, region, ax):
        ax2 = ax.twinx()
        working_df = self.working_df[self.working_df[self.regional_agg_level] == region].drop(
            columns=[self.regional_agg_level]).set_index("年份")

        # transpose the data for plotting
        working_df = self.__transpose_dataframe(working_df)
        working_df.index = working_df.index.map(int).map(str)

        # line plot section
        line_df = working_df[working_df['index'] == "Complex"]

        # bar plot section
        bar_df = working_df[working_df['index'] != 'Complex']
        bar_df = bar_df[bar_df['index'] == focused_index]  # choose the index to plot in bar plot

        line_df = line_df.loc[:, (line_df != 0).any(axis=0)].iloc[:, :1]

        bar_df.plot(kind='bar', stacked=True,
                    color=[self.ref.color_scheme.get(x, '#111111') for x in bar_df.columns], ax=ax)
        sns.lineplot(data=line_df, marker='o', ax=ax2)

        ax.get_legend().remove()
        ax2.get_legend().remove()
        ax.set_title(str(region))

    def subplot(self, by: str, focused_index: str, scatter=False, ncol=None, nrow=None):
        if not scatter:
            self.working_df = self.working_df.sort_values(by=self.regional_agg_level, ascending=True)
            # make subplots of different areas
            # get the number of different regions available
            # self.tech_specific is expected to be false
            regions = list(self.working_df[self.regional_agg_level].unique())
            len_regions = len(regions)
            if ncol is None and nrow is None:
                ncols = int(np.ceil(np.sqrt(len_regions)))
                nrows = int(np.ceil(len_regions/ncols))

            else:
                # todo: temp logic
                ncols = ncol
                nrows = nrow

            fig, axs = plt.subplots(ncols=ncols, nrows=nrows, sharex=True, sharey=True, figsize=(9, 9), dpi=300)

            for row in range(nrows):
                for col in range(ncols):
                    if row*ncols+col < len_regions:
                        self.draw_sub_lineplot(focused_index=focused_index, region=regions[row*ncols+col], ax=axs[row, col])
                    else:
                        break

            fig.show()
