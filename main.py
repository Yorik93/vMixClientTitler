import os
import json
import requests
import xmltodict
import funcs as fs
import pandas as pd
import importlib.util
import streamlit as st
from datetime import datetime
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

# import streamlit.components.v1 as components


st.set_page_config(
    page_title="vMix",
    page_icon="📠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "версия 2023.06 от 14.06.2023"},
)


def post_url(btn, path):
    scenario_json = scenario_get_json(path)
    data = None
    key = None
    number = None
    for i in scenario_json:
        if i["@title"] == btn:
            data = i["data"]
            key = i["@key"]
            number = i["@number"]
    new_data = {}
    for i in data:
        i["@name"] = f'txt{i["@name"]}'
        new_data[i["@name"]] = i["#text"]
    new_data["Update"] = "Update"
    print(f"http://127.0.0.1:8088/titles/?key={key}", new_data)
    requests.post(f"http://127.0.0.1:8088/titles/?key={key}", data=new_data)
    # requests.get(f"http://127.0.0.1:8088/api/?function=PreviewInput&input={number}")
    # requests.get(f"http://127.0.0.1:8088/api/?function=PreviewOverlayInput1&input={1}")
    # requests.get(f"http://127.0.0.1:8088/api/?function=CutDirect&input={number}")


def on_efir():
    requests.get(f"http://127.0.0.1:8088/api/?function=OverlayInput4")


def connect_vmix(tab_titles):
    with tab_titles:
        titles_col1, titles_col2 = st.columns((1.5, 8.5))
        try:
            url_api = "http://127.0.0.1:8088/api"
            response = requests.get(url_api)
            data_dict = xmltodict.parse(response.text)
            with open("vMixClientTitler\\api.json", "w", encoding="utf-8") as outfile:
                json.dump(data_dict, outfile, ensure_ascii=False, indent=4)

            temp_path = data_dict["vmix"]["preset"].split("\\")
            temp_name = temp_path[-1].replace(".vmix", "")
            path_to_folder = "\\".join(temp_path[:-1]) + "\\python\\"

            path_scenario_json = f"{path_to_folder}\\{temp_name}.json"
            scenario_json = scenario_get_json(path_scenario_json)
            inputs = data_dict["vmix"]["inputs"]["input"]

            temp_data_input = []
            for i in inputs:
                key_input = i["@key"]
                name_input = i["#text"]
                number_input = i["@number"]
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
                if scenario_json != []:
                    for scen_i in scenario_json:
                        if scen_i["@key"] == key_input:
                            text_input = scen_i["data"]
                temp_data_input.append(
                    {
                        "@key": key_input,
                        "@number": number_input,
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
            save_change_data = titles_col1.button("Сохранить изменения")
            new_categories = [i for i in st.session_state["data"]]
            for i in temp_data_input:
                if i["#text"] == select_title:
                    if i["data"][0] != None:
                        df_2 = pd.json_normalize(i["data"][0])
                        if "Переменная" not in df_2:
                            df_2["Переменная"] = None

            with titles_col2:
                if "@index" in df_2:
                    df_2 = df_2.drop("@index", axis=1)
                if len(df_2.columns) > 1:
                    df_3 = st.data_editor(
                        df_2,
                        column_config={
                            "@name": st.column_config.Column(
                                width="medium",
                            ),
                            "#text": st.column_config.Column(
                                width="large",
                            ),
                            "Переменная": st.column_config.SelectboxColumn(
                                width="large",
                                options=new_categories,
                            ),
                        },
                        height=None
                        if len(df_2.values) <= 10
                        else 39 * len(df_2.values),
                        use_container_width=True,
                    )
                else:
                    st.info("Изменяемых данных нет")

            if save_change_data:
                try:
                    json_change = df_3.to_json(orient="records")
                    json_change = json.loads(json_change)

                    for i in scenario_json:
                        if i["@key"] == selected_row["@key"].values[0]:
                            i["data"] = json_change
                            break
                    else:
                        scenario_json.append(
                            {
                                "@key": selected_row["@key"].values[0],
                                "@title": selected_row["#text"].values[0],
                                "data": json_change,
                                "@number": selected_row["@number"].values[0],
                            }
                        )

                    with open(path_scenario_json, "w", encoding="utf-8") as outfile:
                        json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
                    titles_col1.success("Данные сохранены")
                except UnboundLocalError:
                    titles_col1.error("Нельзя сохранить")

        except requests.exceptions.ConnectionError:
            st.error("Не включен vMix")
        except KeyError:
            st.error("Не загружен проект vMix")


def connect_vmix_2():
    try:
        url_api = "http://127.0.0.1:8088/api"
        response = requests.get(url_api)
        data_dict = xmltodict.parse(response.text)

        temp_name = data_dict["vmix"]["preset"].split("\\")
        path_to_folder = "\\".join(temp_name[:-1]) + "\\python\\"
        if os.path.exists(path_to_folder):
            files = os.listdir(path_to_folder)
            if files:
                for file in files:
                    file_temp = file.split(".")
                    file_extn = file_temp[-1]
                    file_name = file_temp[0]
                    if file_extn == "py":
                        module_name = file_name
                        spec = importlib.util.spec_from_file_location(
                            module_name, os.path.join(path_to_folder, file)
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return module, path_to_folder
    except requests.exceptions.ConnectionError:
        pass


def scenario_get_json(path_scenario_json):
    if os.path.exists(path_scenario_json):
        scenario_json = fs.load_json_data(path_scenario_json)
    else:
        scenario_json = []
        with open(path_scenario_json, "w", encoding="utf-8") as outfile:
            json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
    return scenario_json


def on_key_press(event):
    st.write(f"Нажата клавиша: {event.name}")


def main():
    variable_json = ""
    st.session_state["data"] = None

    st.button("выдать", on_click=on_efir)

    placeholder = st.empty()
    c = placeholder.container()

    existing_tabs = [
        "✏️Редактор",
        "📝Переменные",
        "🗄️Кэш-данные",
        "📝Список титров и кнопок",
    ]
    try:
        module, path_to_folder = connect_vmix_2()
        if module:
            variable_json = path_to_folder + "variables.json"
            if module.NAME:
                existing_tabs.append(module.NAME)
    except Exception:
        pass

    t_ = c.tabs(existing_tabs)

    with t_[0]:
        ed_editor_col1, ed_editor_col2 = st.columns((5, 5))
        with ed_editor_col1:
            with st.expander("📁Загрузка файла"):
                uploaded_file = st.file_uploader(
                    "Выбрать Excel файл",
                    type=["xlsx", "csv"],
                    accept_multiple_files=False,
                )
        with ed_editor_col2:
            with st.expander("🔠Название колонок Excel, если нету файла"):
                count_columns = st.number_input("Кол-во колонок", min_value=1, value=1)
                temp_columns = {}
                for i in range(count_columns):
                    temp_col = st.text_input(f"Колонка {i+1}")
                    temp_columns[temp_col] = None

        if uploaded_file is not None:
            if uploaded_file.name.split(".")[1] == "xlsx":
                df = fs.load_data(uploaded_file)
            else:
                # df = pd.read_csv(uploaded_file, sep=";", header=None, names=columns)
                df = pd.read_csv(uploaded_file)

        else:
            df = pd.DataFrame([temp_columns])
        temp_data = {}
        for i in df.columns:
            if not (i in ["Выбрать", ""]):
                temp_data[i] = None
        st.session_state["data"] = temp_data

        new_columns = []
        # pinned_row_data = [None]
        new_columns_2 = [i for i in list(df.columns)]
        for i in list(df.columns):
            new_columns.append(
                {
                    "field": i,
                    "filter": "agSetColumnFilter",
                    "filterParams": "filterParams",
                }
            )
        grid_options = {
            "columnDefs": new_columns,
            "defaultColDef": {
                "sortable": True,
                "resizable": True,
                "enableRowGroup": True,
                "flex": 1,
                "floatingFilter": True,
                "editable": True,
            },
            "sideBar": {
                "toolPanels": ["columns"],
            },
            "rowDragManaged": True,
            "rowDragEntireRow": True,
            "rowDragMultiRow": True,
            "rowSelection": "multiple",
            "animateRows": True,
            "rowGroupPanelShow": "always",
            "pagination": True,
            "paginationPageSize": 15,
            "headerHeight": 50,
            "floatingFiltersHeight": 50,
            "pivotHeaderHeight": 50,
        }
        custom_css = {}
        grid_table = AgGrid(
            df,
            grid_options,
            custom_css=custom_css,
        )
        data = grid_table["selected_rows"]
        if data:
            del data[0]["_selectedRowNodeInfo"]
            st.session_state["data"] = data[0]

    with t_[1]:
        with st.expander("🔣Примеры"):
            code_example = "'НиЧеГо' if 'имя' not in d$ else d$['имя'].split() if ' ' in d$['имя'] else d$['имя']"
            st.write(
                "Пример: пишем слово 'НиЧеГо' если такой переменной в нашем массиве данных нет. Далее мы делаем сплит по пробелу, если пробел в ключе существует. И последний else - в любом другом случае, например, будет одно слово в переменной"
            )
            st.code(code_example, language="python")
        variable_col1, variable_col2 = st.columns((2, 8))
        variable_add_button = variable_col1.button("💾Сохранить изменения")
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
        var_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        var_json = var_df.to_json(orient="records")
        var_json = json.loads(var_json)
        if variable_add_button:
            var_json = fs.data_cash(var_json)
            with open(
                variable_json,
                "w",
                encoding="utf-8",
            ) as outfile:
                json.dump(var_json, outfile, ensure_ascii=False, indent=4)

    with t_[2]:
        if os.path.exists(variable_json):
            var_json = fs.load_json_data(variable_json)
        try:
            var_json = fs.data_cash(var_json)
        except KeyError:
            pass
        st.session_state

    connect_vmix(t_[3])

    module.main(t_[-1], path_to_folder)
    # except Exception:
    #     pass


if __name__ == "__main__":
    main()
