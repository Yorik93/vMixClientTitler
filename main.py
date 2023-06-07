import streamlit as st
import pandas as pd
import requests
import os
import json
from st_aggrid import AgGrid, GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import xmltodict
import funcs as fs
from datetime import datetime


st.set_page_config(
    page_title="vMix Titler Not 3D",
    page_icon="📠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "версия 2023.06 от 05.06.2023"},
)


# Функция для отправки команды к vMix по API
def send_command(command):
    # Здесь необходимо заменить <VMIX_IP> на IP-адрес вашего vMix
    url = f"http://127.0.0.1:8088/API/?Function={command}"
    response = requests.get(url)
    if response.status_code == 200:
        st.success(f"Команда '{command}' отправлена успешно!")
    else:
        st.error(f"Ошибка при отправке команды '{command}'.")


def post_url(btn, path):
    scenario_json = scenario_get_json(path)
    data = None
    key = None
    for i in scenario_json:
        if i["@title"] == btn:
            data = i["data"]
            key = i["@key"]
    new_data = {}
    for i in data:
        i["@name"] = f'txt{i["@name"]}'
        new_data[i["@name"]] = i["#text"]
    new_data["Update"] = "Update"
    print(f"http://127.0.0.1:8088/titles/?key={key}", new_data)
    result = requests.post(
        f"http://127.0.0.1:8088/titles/?key={key}",
        data=new_data,
        # data={"Дата.Text": "111111111111111123sad"},
    )
    # print(result.text)


def update_data(upd_data):
    for i in upd_data:
        post_url(i)
        print(i)

    # url = f"http://127.0.0.1:8088/titles/?key={i['@key']}"

    # res = requests.post(
    #     url, data={f'txt{upd_data["@name"]}': upd_data["#text"], "Update": "Update"}
    # )
    # print(res)


def connect_vmix(tab_titles):
    with tab_titles:
        # if st.button("Подключиться к vMix"):
        titles_col1, titles_col2 = st.columns((1.5, 8.5))
        try:
            url_api = "http://127.0.0.1:8088/api"
            response = requests.get(url_api)
            data_dict = xmltodict.parse(response.text)
            # with open("vMixClientTitler/preset.json", "w", encoding="utf-8") as f:
            #     json.dump(data_dict, f, ensure_ascii=False, indent=4)

            temp_name = data_dict["vmix"]["preset"].split("\\")[-1].replace(".vmix", "")
            path_scenario_json = f"vMixClientTitler/scenario_{temp_name}.json"

            scenario_json = scenario_get_json(path_scenario_json)
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
                if scenario_json != []:
                    for scen_i in scenario_json:
                        if scen_i["@key"] == key_input:
                            text_input = scen_i["data"]
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
            save_change_data = titles_col1.button("Сохранить изменения")
            new_categories = [i for i in st.session_state["data"]]
            for i in temp_data_input:
                if i["#text"] == select_title:
                    if i["data"][0] != None:
                        df_2 = pd.json_normalize(i["data"][0])
                        if "Переменная" not in df_2:
                            df_2["Переменная"] = None
                        # df_2["Переменная"] = df_2["Переменная"].astype("category")
                        # df_2["Переменная"] = pd.Categorical(
                        #     df_2["Переменная"], categories=new_categories
                        # )

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
                            }
                        )

                    with open(path_scenario_json, "w", encoding="utf-8") as outfile:
                        json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
                    titles_col1.success("Данные сохранены")
                except UnboundLocalError:
                    titles_col1.error("Нельзя сохранить")

        except requests.exceptions.ConnectionError:
            st.error("Не включен vMix")
    return path_scenario_json


def scenario_get_json(path_scenario_json):
    if os.path.exists(path_scenario_json):
        scenario_json = fs.load_json_data(path_scenario_json)
    else:
        scenario_json = []
        with open(path_scenario_json, "w", encoding="utf-8") as outfile:
            json.dump(scenario_json, outfile, ensure_ascii=False, indent=4)
    return scenario_json


def main():
    variable_json = "vMixClientTitler/variables.json"
    st.session_state["data"] = None

    placeholder = st.empty()
    # c = placeholder.container()
    (
        tab_editor,
        tab_variable,
        tab_cash,
        tab_titles,
        tab_nard,
    ) = placeholder.tabs(
        [
            "✏️Редактор",
            "📝Переменные",
            "🗄️Кэш-данные",
            "📝Список титров и кнопок",
            "🎲🟢🟡Нарды",
        ]
    )

    with tab_editor:
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
                "vMixClientTitler/variables.json",
                "w",
                encoding="utf-8",
            ) as outfile:
                json.dump(var_json, outfile, ensure_ascii=False, indent=4)

    with tab_cash:
        if os.path.exists(variable_json):
            var_json = fs.load_json_data(variable_json)
        try:
            var_json = fs.data_cash(var_json)
        except KeyError:
            pass
        st.session_state

    path_scenario_json = connect_vmix(tab_titles)

    with tab_nard:
        nard_path = "vMixClientTitler/nard.json"
        data_json = fs.load_json_data(nard_path)
        with st.sidebar:
            st.checkbox("Сегодня", value=True, key="Today")
            df_temp = pd.json_normalize(data_json["schedule"])
            if st.session_state["Today"] is True:
                df_temp = df_temp.loc[
                    df_temp["Дата"].str[:10] == str(datetime.now())[:10]
                ]
            name_selectbox = (
                df_temp["Игрок1"]
                + " — "
                + df_temp["Игрок2"]
                + " ["
                + df_temp["Дата"].str.replace("T", " ").str[:16]
                + "]"
            )
            select_row = st.selectbox("Выбор матча", name_selectbox)

        tab_nard_1, tab_nard_2 = tab_nard.tabs(["✏️Редактор", "📇Основная"])
        with tab_nard_1:
            nard_list = {
                "Игроки": "players",
                "Расписание": "schedule",
                "Игра": "games",
            }
            nard_col1, nard_col2 = st.columns((1.5, 8.5))
            select_box = nard_col1.selectbox("Выбор", list(nard_list.keys()))
            save_change_nard = nard_col1.button("💾Сохранить  изменения")
            selected_row = nard_list[select_box]
            df_data_json = pd.json_normalize(data_json[selected_row])
            name_lastname = []
            for i in data_json["players"]:
                name_lastname.append(f'{i["Имя"].strip()} {i["Фамилия"].strip()}')
            column_config = None
            if select_box == "Расписание":
                df_data_json["Дата"] = pd.to_datetime(
                    df_data_json["Дата"], format="%Y-%m-%dT%H:%M:%S"
                )
                column_config = {
                    "Игрок1": st.column_config.SelectboxColumn(
                        options=name_lastname, width="medium"
                    ),
                    "Игрок2": st.column_config.SelectboxColumn(
                        options=name_lastname, width="medium"
                    ),
                    "Дата": st.column_config.DatetimeColumn(
                        format="DD.MM.YYYY HH:mm", width="medium"
                    ),
                    "Счёт1": st.column_config.NumberColumn(width="small"),
                    "Счёт2": st.column_config.NumberColumn(width="small"),
                }
            elif select_box == "Игроки":
                column_config = {"Фото": st.column_config.ImageColumn()}
                for i, row in df_data_json.iterrows():
                    try:
                        imgExtn = row["Фото"][-4:]
                    except TypeError:
                        imgExtn = "png"
                    row["Фото"] = f"data:image/{imgExtn};base64," + fs.ReadPictureFile(
                        row["Фото"]
                    )

            df_edit = nard_col2.data_editor(
                df_data_json,
                num_rows="dynamic",
                hide_index=False,
                height=None
                if len(df_data_json.values) <= 10
                else 39 * len(df_data_json.values)
                if len(df_data_json.values) <= 20
                else 34 * len(df_data_json.values),
                column_config=column_config,
            )

            if save_change_nard:
                temp_json = df_edit.to_json(orient="records")
                temp_json = json.loads(temp_json)

                for item in temp_json:
                    if "Дата" in item:
                        item["Дата"] = datetime.fromtimestamp(
                            (item["Дата"] - 10800000) / 1000
                        ).strftime("%Y-%m-%dT%H:%M:%S")
                data_json[selected_row] = temp_json
                with open(nard_path, "w", encoding="utf-8") as outfile:
                    json.dump(data_json, outfile, ensure_ascii=False, indent=4)

        with tab_nard_2:
            statistic1 = {
                "Счёт": None,
                "Ошибок (зевков)": None,
                "Эквити ошибок": None,
                "Ошибок удвоений (зевков)": None,
                "Эквити ошибок удвоений": None,
                "Ошибок взятий (зевков)": None,
                "Эквити ошибок взятий": None,
                "Сумма эквити": None,
                "Удача (джокер)": None,
                "Качество игры (PR)": None,
            }
            statistic2 = statistic1
            col_nard2_1, col_nard2_2 = st.columns((3, 7))
            with col_nard2_1:
                columns = list(statistic1.keys())
                val1 = list(statistic1.values())
                val2 = list(statistic2.values())
                df_game = pd.DataFrame(
                    {
                        "Название": columns,
                        "Игрок1": val1,
                        "Игрок2": val2,
                    }
                )
                df_game_2 = col_nard2_1.data_editor(
                    df_game,
                )

                game_json = df_game_2.to_json(orient="index")
                game_json = json.loads(game_json)

                st.session_state["game"] = game_json
                score1 = game_json["0"]["Игрок1"]
                score2 = game_json["0"]["Игрок2"]
                for i in data_json["schedule"]:
                    temp = f'{i["Игрок1"]} — {i["Игрок2"]} [{i["Дата"].replace("T", " ")[:16]}]'
                    if temp == select_row:
                        i["Счёт1"] = score1
                        i["Счёт2"] = score2
                if col_nard2_1.button("💾Сохранить счёт"):
                    with open(nard_path, "w", encoding="utf-8") as outfile:
                        json.dump(data_json, outfile, ensure_ascii=False, indent=4)

            with col_nard2_2:
                btn_ID = st.button(
                    "Игрок1", on_click=post_url("ID", path_scenario_json)
                )


if __name__ == "__main__":
    main()
