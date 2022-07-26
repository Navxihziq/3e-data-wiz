import pandas as pd

# the default first 5 indexes of headers
header_first_5 = ['nonsense', '年份', '电网区域', '省份', '省下区域', 'Tech']


class RefData:
    def __init__(self, path_to_ref):
        self.dataframe = pd.read_excel(path_to_ref)
        self.color_scheme = self.__read_color_scheme()
        self.tech_fuel_group_dict = self.__read_tech_fuel_group_dict()
        self.order_list = self.__read_order_list()

    def __read_color_scheme(self):
        return dict(self.dataframe[['Fuel_Group', "HEX"]].values)

    def __read_tech_fuel_group_dict(self):
        return dict(self.dataframe[['Tech', 'Fuel_Group']].values)

    def __read_order_list(self):
        return self.dataframe.dropna().sort_values(by='Order', ascending=True)['Fuel_Group'].unique().tolist()

    def get_stack_order(self, fuel_group: list):
        ls = []
        for group in fuel_group:
            if group in self.order_list:
                ls = ls.append(group)

        return ls


class WorkingData:
    def __init__(self, file_info: list, ref: RefData):
        self.working_df = None
        self.ref = ref
        self.dataframe = self.init_dataframe(file_info)

    def init_dataframe(self, file_info: list) -> pd.DataFrame:
        # read the files
        file_1 = pd.read_excel(file_index_list[0]['path'])
        file_2 = pd.read_excel(file_index_list[1]['path'])

        file_1.columns = header_first_5 + file_index_list[0]['columns']
        file_1 = file_1[header_first_5 + [file_index_list[0]['focused_index']]]
        file_2.columns = header_first_5 + file_index_list[1]['columns']
        file_2 = file_2[header_first_5 + [file_index_list[1]['focused_index']]]

        # join the second dataframe to the first one
        dataframe = file_1.merge(file_2, how="outer", on=header_first_5)

        # map the fuel group value from tech column
        dataframe['Fuel_Group'] = dataframe['Tech'].map(self.ref.tech_fuel_group_dict)

        return dataframe

    def rule_out(self, regional_agg_level: str, selected_region=None, select_reverse=True):
        working_df = self.dataframe.copy()

        if selected_region is None:
            selected_region = []

        if regional_agg_level == "全国":
            working_df = working_df.groupby(by=['年份', 'Fuel_Group']).sum().reset_index()
        else:
            working_df = working_df.groupby(by=['年份', 'Fuel_Group', regional_agg_level]).sum().reset_index()
            if select_reverse:
                working_df = working_df[~working_df[regional_agg_level].isin(selected_region)]
            else:
                working_df = working_df[working_df[regional_agg_level].isin(selected_region)]

        self.working_df = working_df
        return working_df


file_index_list = [
    {
        "path": "/Users/zhixuan/PycharmProjects/3e-data-wiz/example-files/情景1产能.xlsx",
        "focused_index": "Installed Power Capacity (MW)",
        "columns": ["Installed Power Capacity (MW)", "Installed Heat Capacity (MW)", "Installed Hydrogen Production Capacity (MW)"]
    },
    {
        "path": "/Users/zhixuan/PycharmProjects/3e-data-wiz/example-files/情景1产量.xlsx",
        "focused_index": "Electricity Generation (GWh)",
        "columns": ["Electricity Generation (GWh)", "Planned Curtailment (GWh)", "Hydrogen Production (MWh)", "Hydrogen Production (10000 Ton)", "Heat Generation (TJ)"]
    }
]

ref = RefData("/Users/zhixuan/PycharmProjects/3e-data-wiz/example-files/color_index.xlsx")
data = WorkingData(file_index_list, ref)
print(data.rule_out("省份").info())
