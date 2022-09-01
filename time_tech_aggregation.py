import pandas as pd


class Data:
    def __init__(self, first_path, second_path, ref_path, columns=None):
        if columns is None:
            columns = ['省份', '技术', '星期', '时刻', 'Level']

        self.first_path = first_path
        self.second_path = second_path
        self.ref_path = ref_path
        self.columns = columns
        self.dataframe = self.get_dataframe()

    def get_tech_group_dict(self):
        # read the reference excel
        dataframe = pd.read_excel(self.ref_path)
        return dict(dataframe[['Tech', 'Fuel_Group']].values)

    def get_dataframe(self):
        # read the files
        first_dataframe = pd.read_excel(self.first_path)
        second_dataframe = pd.read_excel(self.second_path)

        # keep the first 5 columns
        first_dataframe = first_dataframe.iloc[:, :5]
        second_dataframe = second_dataframe.iloc[:, :5]

        # reset the names of the columns
        first_dataframe.columns = self.columns
        second_dataframe.columns = self.columns

        # concat the 2 dataframes together
        dataframe = pd.concat(objs=[first_dataframe, second_dataframe], axis='index', join='inner', ignore_index=True)

        # convert tech to tech group and add to the end of the file
        dataframe['Tech_Group'] = dataframe['技术'].map(self.get_tech_group_dict())

        return dataframe

    def aggregate(self) -> pd.DataFrame:
        return self.dataframe.groupby(['星期', '时刻', 'Tech_Group']).sum().reset_index().pivot(index=['星期', '时刻'], columns='Tech_Group')
