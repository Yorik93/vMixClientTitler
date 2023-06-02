import streamlit as st
import pandas as pd
import requests
import os
import json
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from bs4 import BeautifulSoup
import xmltodict
from concurrent.futures import ThreadPoolExecutor

import func_caspar as fc
import funcs as fs

# from streamlit_extras.add_vertical_space import add_vertical_space


st.set_page_config(
    page_title="vMix Titler Not 3D",
    page_icon="📠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "версия 2023.05 от 31.05.2023"},
)

columns = [
    "Start NR",
    "Primary score",
    "Match shot",
    "Firingpoint",
    "Secondarv score",
    "DivisionS",
    "Time",
    "Innerten",
    "X",
    "Y",
    "Intime",
    "Time since change",
    "Sween direction",
    "Demonstration",
    "Shoot",
    "Practice",
    "InsDel",
    "Totalkind",
    "Group",
    "Firekind",
    "Logevent",
    "Logtype",
    "Time_1",
    "Relay",
    "Weapon",
    "Position",
    "TargetID",
    "External number",
]


# Функция для отправки команды к vMix по API
def send_command(command):
    # Здесь необходимо заменить <VMIX_IP> на IP-адрес вашего vMix
    url = f"http://127.0.0.1:8088/API/?Function={command}"
    response = requests.get(url)
    if response.status_code == 200:
        st.success(f"Команда '{command}' отправлена успешно!")
    else:
        st.error(f"Ошибка при отправке команды '{command}'.")


def post_url(i):
    requests.post(
        f"http://10.10.0.149:8088/titles/?key={i['@key']}",
        data={f'txt{i["@name"]}': i["#text"], "Update": "Update"},
    )
    print(
        f"http://10.10.0.149:8088/titles/?key={i['@key']}",
        {f'txt{i["@name"]}': i["#text"], "Update": "Update"},
    )


def update_data(upd_data):
    # with ThreadPoolExecutor() as pool:
    #     [pool.submit(post_url, i) for i in upd_data]
    for i in upd_data:
        post_url(i)
        print(i)

    # url = f"http://10.10.0.149:8088/titles/?key={i['@key']}"

    # res = requests.post(
    #     url, data={f'txt{upd_data["@name"]}': upd_data["#text"], "Update": "Update"}
    # )
    # print(res)


def connect_vmix():
    url_api = "http://10.10.0.149:8088/api"
    response = requests.get(url_api)
    data_dict = xmltodict.parse(response.text)
    with open("preset.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)
    return data_dict


def scenario_get_json(path_scenario_json):
    if os.path.exists(path_scenario_json):
        scenario_json = fs.load_json_data(path_scenario_json)
    else:
        scenario_json = [{"@key": None, "@title": None, "data": []}]
        with open(path_scenario_json, "w", encoding="utf-8") as outfile:
            json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
    return scenario_json


def main():
    variable_json = "vMixClientTitler/variables.json"
    path_scenario_json = "vMixClientTitler/scenario.json"
    st.session_state["data"] = None

    placeholder = st.empty()
    c = placeholder.container()
    tab_editor, tab_variable, tab_cash, tab_titles = c.tabs(
        [
            "Редактор",
            "Переменные",
            "Кэш-данные",
            "Список титров",
        ]
    )

    with tab_editor:
        ed_editor_col1, ed_editor_col2 = st.columns((5, 5))
        with ed_editor_col1:
            with st.expander("Загрузка файла"):
                uploaded_file = st.file_uploader(
                    "Choose a Excel file", type=["xlsx", "csv"], accept_multiple_files=False
                )
        with ed_editor_col2:
            with st.expander("Название колонок Excel, если нету файла"):
                count_columns = st.number_input("Кол-во колонок", min_value=1, value=1)
                temp_columns = {}
                for i in range(count_columns):
                    temp_col = st.text_input(f"Колонка {i+1}")
                    temp_columns[temp_col] = None

        if uploaded_file is not None:
            if uploaded_file.name.split('.')[1] == "xlsx":
                df = fs.load_data(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file, sep=";", header=None, names=columns)
            
        else:
            df = pd.DataFrame([temp_columns])
        temp_data = {}
        for i in df.columns:
            if not (i in ["Выбрать", ""]):
                temp_data[i] = None
        st.session_state["data"] = temp_data

        gd = GridOptionsBuilder.from_dataframe(df)
        gd.configure_selection(selection_mode="multiple")
        gd.configure_default_column(editable=True, groupable=True)
        gd.configure_pagination(enabled=True)
        gridoptions = gd.build()

        grid_table = AgGrid(
            df,
            gridOptions=gridoptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
        )
        data = grid_table["selected_rows"]
        if data:
            del data[0]["_selectedRowNodeInfo"]
            st.session_state["data"] = data[0]

    with tab_variable:
        with st.expander("Примеры"):
            code_example = "'НиЧеГо' if 'имя' not in d$ else d$['имя'].split() if ' ' in d$['имя'] else d$['имя']"
            st.write(
                "Пример: пишем слово 'НиЧеГо' если такой переменной в нашем массиве данных нет. Далее мы делаем сплит по пробелу, если пробел в ключе существует. И последний else - в любом другом случае, например, будет одно слово в переменной"
            )
            st.code(code_example, language="python")
        variable_col1, variable_col2 = st.columns((2, 8))
        variable_add_button = variable_col1.button("Добавить запись")
        variable_col2.markdown(
            "Чтобы использовать переменную, созданную в Кэш-данных или с помощью ручных переменных достаточно написать в формате: **:green[d$['здесь пишем полностью название переменной']]** "
        )
        if os.path.exists(variable_json):
            json_temp = fs.load_json_data(variable_json)
            df = pd.DataFrame(json_temp)
        else:
            df = pd.DataFrame(
                [
                    {"Переменная": "", "Текст": ""},
                ]
            )
        var_df = st.experimental_data_editor(
            df, num_rows="dynamic", use_container_width=True
        )
        var_json = var_df.to_json(orient="records")
        var_json = json.loads(var_json)
        if variable_add_button:
            var_json = fs.data_cash(var_json)
            with open(
                "vMixClientTitler/variables.json",
                "w",
                encoding="utf-8",
            ) as outfile:
                json.dump(var_json, outfile, ensure_ascii=False, indent=4)

    with tab_cash:
        if os.path.exists(variable_json):
            var_json = fs.load_json_data(variable_json)
        var_json = fs.data_cash(var_json)
        st.session_state

    with tab_titles:
        titles_col1, titles_col2 = st.columns((1.5, 8.5))
        data_dict = connect_vmix()

        # if os.path.exists(path_scenario_json):
        #     scenario_json = fs.load_json_data(path_scenario_json)
        # else:
        #     scenario_json = {"@key": None, "@title": None, "data": []}
        #     with open(path_scenario_json, "w", encoding="utf-8") as outfile:
        #         json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)

        inputs = data_dict["vmix"]["inputs"]["input"]
        temp_data_input = []
        for i in inputs:
            key_input = i["@key"]
            name_input = i["#text"]
            text_input = (
                [None]
                if "text" not in i
                else i["text"]
                if type(i["text"]) is list
                else [i["text"]]
            )
            image_input = (
                [None]
                if "image" not in i
                else i["image"]
                if type(i["image"]) is list
                else [i["image"]]
            )
            temp_data_input.append(
                {
                    "@key": key_input,
                    "#text": name_input,
                    "data": [
                        text_input if len(text_input) > 0 else None,
                        image_input if len(image_input) > 0 else None,
                    ],
                }
            )
        df_1 = pd.json_normalize(temp_data_input)
        select_title = titles_col1.selectbox("Список титров:", df_1["#text"])
        selected_row = df_1.loc[df_1["#text"] == select_title]
        # print(selected_row["@key"].values[0])
        save_change_data = titles_col1.button("Сохранить изменения")
        new_categories = [i for i in st.session_state["data"]]
        for i in temp_data_input:
            if i["#text"] == select_title:
                df_2 = pd.json_normalize(i["data"][0])
                df_2["Переменная"] = ""
                df_2["Переменная"] = df_2["Переменная"].astype("category")
                df_2["Переменная"] = pd.Categorical(
                    df_2["Переменная"], categories=new_categories
                )

        with titles_col2:
            df_2 = df_2.drop("@index", axis=1)
            df_3 = st.experimental_data_editor(
                df_2, use_container_width=True, height=700
            )

        if save_change_data:
            scenario_json = scenario_get_json(path_scenario_json)
            json_change = df_3.to_json(orient="records")
            json_change = json.loads(json_change)
            # print(scenario_json)
            print("="*100)
            print(selected_row["@key"].values[0])
            print(scenario_json)
            for i in scenario_json:
                if i["@key"] == selected_row["@key"].values[0]:
                    i["data"] = json_change
                    print("Ключ есть такой")
                    break
                # else:
                #     scenario_json.append(
                #         {
                #             "@key": selected_row["@key"].values[0],
                #             "@title": selected_row["#text"].values[0],
                #             "data": json_change,
                #         }
                #     )                    
                #     print(i["@key"], "ключа такого нет")
                #     break
            with open(path_scenario_json, "w", encoding="utf-8") as outfile:
                json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
            # print(scenario_json[0].get(selected_row["@key"].values[0]))
            
            # for i in scenario_json:
            #     if i["@key"] == selected_row["@key"].values[0]:
            #         i["data"] = json_change
            #         break
            #     else:
            #         scenario_json.append(
            #             {
            #                 "@key": selected_row["@key"].values[0],
            #                 "@title": selected_row["#text"].values[0],
            #                 "data": json_change,
            #             }
            #         )
            # if selected_row["@key"].values[0] in scenario_json:
            #     print("TCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")

            # for i in scenario_json:
            #     # print(i, "====================================")
            #     print(i["@key"], selected_row["@key"].values[0], "====================================")
            #     if i["@key"] == selected_row["@key"].values[0]:
            #         i["data"] = json_change
            #         continue
            #     else:
            #         scenario_json.append(
            #             {
            #                 "@key": selected_row["@key"].values[0],
            #                 "@title": selected_row["#text"].values[0],
            #                 "data": json_change,
            #             }
            #         )
            #         continue
            #         # scenario_json["@key"] = selected_row["@key"].values[0]
            #         # scenario_json["@title"] = selected_row["#text"].values[0]
            #         # scenario_json["data"] = json_change

            # print(scenario_json, "++++++++++++++++++++++++++")

            # print()
            # print(scenario_json)
            # print()
            # print(json_change)

    #     df_1 = pd.json_normalize(rows)

    #     df_1["Переменная"] = df_1["Переменная"].astype("category")
    #     df_1["Переменная"] = pd.Categorical(
    #         df_1["Переменная"], categories=new_categories
    #     )

    #     # gd = GridOptionsBuilder.from_dataframe(df_1)

    #     # gridoptions = {
    #     #     "columnDefs": [
    #     #         {"field": "@title", "rowGroup": True, "hide": True},
    #     #         {"field": "@name"},
    #     #         {"field": "#text", "editable": True},
    #     #         {
    #     #             "field": "Переменная",
    #     #             "editable": True,
    #     #             "cellEditor": "agSelectCellEditor",
    #     #             "cellEditorParams": {"values": new_categories},
    #     #         },
    #     #         {"field": "@key", "hide": True},
    #     #     ]
    #     # }

    #     # new_data_api = AgGrid(
    #     #     df_1,
    #     #     gridOptions=gridoptions,
    #     #     columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    #     # )
    #     if save_button_data_api:
    #         new_json = new_data_api.to_json(orient="records")
    #         # new_json = new_data_api.data.to_json(orient="records")
    #         new_json = json.loads(new_json)

    #         temp_cash_data = st.session_state["data"]
    #         for i in new_json:
    #             for j in temp_cash_data:
    #                 if i["Переменная"] == j:
    #                     print(["Переменная"], j, '++++++++++++++++++++++++++++++++++++')
    #                     i["#text"] = temp_cash_data[j]
    #         with open(
    #             "vMixClientTitler/test_json.json",
    #             "w",
    #             encoding="utf-8",
    #         ) as outfile:
    #             json.dump(new_json, outfile, ensure_ascii=False, indent=4)

    #         update_data(new_json)
    #         print("все готово11111111122222222222111")


if __name__ == "__main__":
    main()
