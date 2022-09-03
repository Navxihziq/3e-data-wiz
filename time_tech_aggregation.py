import pandas as pd
import matplotlib.pyplot as plt


class Data:
    def __init__(self, first_path, second_path, ref_path, columns=None):
        if columns is None:
            columns = ['年份', '省份', '技术', '星期', '时刻', 'Level']

        self.first_path = first_path
        self.second_path = second_path
        self.ref_path = ref_path
        self.ref_dataframe = pd.read_excel(self.ref_path)
        self.columns = columns
        self.dataframe = self.__get_dataframe()
        self.aggregated_dataframe = self.__aggregate()
        self.stack_order = self.__get_stack_order(self.aggregated_dataframe)
        self.color_scheme = self.__get_color_scheme()

    def __get_color_scheme(self):
        return dict(self.ref_dataframe[['Fuel_Group', "HEX"]].dropna(how="all").values)

    def __get_tech_group_dict(self):
        return dict(self.ref_dataframe[['Tech', 'Fuel_Group']].values)

    def __get_dataframe(self):
        # read the files
        first_dataframe = pd.read_excel(self.first_path)
        second_dataframe = pd.read_excel(self.second_path)

        # keep the first 5 columns
        first_dataframe = first_dataframe.iloc[:, :6]
        second_dataframe = second_dataframe.iloc[:, :6]

        # reset the names of the columns
        first_dataframe.columns = self.columns
        second_dataframe.columns = self.columns

        # concat the 2 dataframes together
        dataframe = pd.concat(objs=[first_dataframe, second_dataframe], axis='index', join='inner', ignore_index=True)

        # convert tech to tech group and add to the end of the file
        dataframe['Tech_Group'] = dataframe['技术'].map(self.__get_tech_group_dict()).fillna('其他')

        return dataframe

    def __aggregate(self) -> pd.DataFrame:
        return self.dataframe.groupby(['星期', '时刻', '省份', 'Tech_Group']).sum().reset_index().pivot(index=['星期', '时刻', '省份'], columns='Tech_Group', values=['Level'])
        # ['Level']

    def __get_stack_order(self, dataframe):
        # get the designed stack order
        stack_order = self.ref_dataframe.dropna().sort_values(by='Order', ascending=True)[
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

        # specifying the order of the tech groups
        self.aggregated_dataframe.columns = self.stack_order + ['其他']

        # plot the graph
        self.aggregated_dataframe.plot.area(figsize=(20, 9), color=[self.color_scheme.get(x, '#111111') for x in self.aggregated_dataframe.columns], ax=ax)
