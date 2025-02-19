import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def remove_year(row: pd.Series):
    return row['技术'][:-5]


class Data:
    def __init__(self, first_path, second_path, marginal_path, cref_path, pref_path=None, columns=None, province=None):
        if columns is None:
            columns = ['年份', '省份', '技术', '星期', '时刻', 'Level']

        self.first_path = first_path
        self.second_path = second_path
        self.marginal_path = marginal_path

        self.cref_path = cref_path
        self.pref_path = pref_path
        self.cref_dataframe = pd.read_excel(self.cref_path)

        self.columns = columns
        self.province = province
        self.dataframe = self.__get_dataframe()
        # todo: remove after
        self.dataframe['年份'] = 2050

        self.marginal_dataframe = self.__get_marginal_dataframe()
        self.aggregated_dataframe = self.__aggregate()
        self.stack_order = self.__get_stack_order(self.aggregated_dataframe)
        self.color_scheme = self.__get_color_scheme()

        try:
            self.aggregated_dataframe = self.aggregated_dataframe[self.stack_order + ['其他']]
        except KeyError:
            self.aggregated_dataframe = self.aggregated_dataframe[self.stack_order]

    def __get_marginal_dataframe(self) -> pd.DataFrame:
        dataframe = pd.read_excel(self.marginal_path).iloc[:, :5]
        dataframe.columns = ['年份', '省份', '星期', '时刻', 'Marginal']

        if self.province is not None:
            dataframe = dataframe[dataframe['省份'] == self.province]

        return dataframe.set_index(keys=['年份', '省份', '星期', '时刻'])

    def __get_color_scheme(self):
        return dict(self.cref_dataframe[['Fuel_Group', "HEX"]].dropna(how="all").values)

    def __get_tech_group_dict(self):
        return dict(self.cref_dataframe[['Tech', 'Fuel_Group']].values)

    def __get_province_dict(self):
        dict = {}
        df = pd.read_excel(self.pref_path)
        for _index, row in df.iterrows():
            ls = row['Subprovince'].split(",")
            for subprovince in ls:
                dict[subprovince] = row['Province'].strip()

        return dict

    def __get_dataframe(self):
        # read the files
        first_dataframe = pd.read_excel(self.first_path)
        second_dataframe = pd.read_excel(self.second_path)

        # keep the first 6 columns
        first_dataframe = first_dataframe.iloc[:, :6]
        second_dataframe = second_dataframe.iloc[:, :6]

        # reset the names of the columns
        first_dataframe.columns = self.columns
        second_dataframe.columns = self.columns

        # concat the 2 dataframes together
        dataframe = pd.concat(objs=[first_dataframe, second_dataframe], axis='index', join='inner', ignore_index=True)

        # todo: remove after debugging
        dataframe['技术'] = dataframe.apply(remove_year, axis=1)

        # convert tech to tech group and add to the end of the file
        dataframe['Tech_Group'] = dataframe['技术'].map(self.__get_tech_group_dict()).fillna('其他')

        if self.pref_path is not None:
            # add a province column for each sub-province regions
            dataframe['省份'] = dataframe['省份'].map(self.__get_province_dict()).fillna('其他')

        if self.province is not None:
            dataframe = dataframe[dataframe['省份'] == self.province]

        return dataframe

    def __aggregate(self) -> pd.DataFrame:
        dataframe = self.dataframe.groupby(by=['年份', '省份', '星期', '时刻', 'Tech_Group']).sum().reset_index().pivot(
            columns=['Tech_Group'], index=['年份', '省份', '星期', '时刻'])['Level']
        # get rid of the all-zero columns
        return dataframe.loc[:, (dataframe != 0).any(axis=0)]

    def __get_stack_order(self, dataframe):
        # get the designed stack order
        stack_order = self.cref_dataframe.dropna().sort_values(by='Order', ascending=True)[
            'Fuel_Group'].unique().tolist()

        # get every tech group appeared in dataframe
        group_in_df = dataframe.columns.to_list()

        # conjunction of the apropos 2 sets
        ls = []
        for tech in stack_order:
            if tech in group_in_df:
                ls.append(tech)

        return ls

    def stack_plot(self):
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 20), dpi=300)
        ax2 = ax.twinx()

        # plot the graph
        self.aggregated_dataframe.plot.area(figsize=(20, 9), color=[self.color_scheme.get(x, '#111111') for x in
                                                                    self.aggregated_dataframe.columns], ax=ax)
        # sns.stripplot(data=self.marginal_dataframe, ax=ax2, dodge=True)
        plt.show()
        fig.savefig("./checking/tta_area_plot.png")

    def bar_plot(self, detailed_labels=False):
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 20), dpi=410)
        if detailed_labels:
            data_2_plt = self.aggregated_dataframe
        else:
            data_2_plt = self.aggregated_dataframe.reset_index().drop(axis=1, labels=['年份', '省份']).set_index(['星期', '时刻'])
        # plot the bar plot this time
        data_2_plt.plot(kind='bar', width=1.0, stacked=True, ax=ax, figsize=(20, 9),
                                         color=[self.color_scheme.get(x, '#111111') for x in self.aggregated_dataframe.columns])
        # positioning the legend
        ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc='lower left', mode='expand')
        # remove the grid
        plt.grid(None)
        plt.show()
        fig.savefig("./checking/tta_bar_plot.png")
