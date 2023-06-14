import funcs as fs
import pandas as pd
import streamlit as st
from datetime import datetime
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode

NAME = "🔫Стрельба"


def main(tab, path_to_folder):
    path_to_file = path_to_folder + "\\shooting.json"
    json_temp = fs.load_json_data(path_to_file)

    tabs_editor, tabs_test = tab.tabs(["✏️Редактор", "Основная"])

    with tabs_editor:
        regions = json_temp["regions"]
        region_dict = []
        for i in regions:
            region_dict.append(i["name_rus"])
            for j in json_temp["players"]:
                if i["id"] == j["region_id"]:
                    j["region_id"] = i["name_rus"]

        competitions = json_temp["competitions"]
        comp_dict = []
        for i in competitions:
            comp_dict.append(i["name_rus"])
            for j in json_temp["events"]:
                if i["id"] == j["competition_id"]:
                    j["competition_id"] = i["name_rus"]

        rounds = json_temp["rounds"]
        round_dict = []
        for i in rounds:
            round_dict.append(i["name_rus"])
            for j in json_temp["events"]:
                if j:
                    if i["id"] == j["round_id"]:
                        j["round_id"] = i["name_rus"]

        genders = json_temp["genders"]
        gender_dict = []
        for i in genders:
            gender_dict.append(i["name_rus"])
            for j in json_temp["events"]:
                if j:
                    if i["id"] == j["gender_id"]:
                        j["gender_id"] = i["name_rus"]

        col1, col2 = st.columns((1.5, 7.5))
        select_dict = []
        for i in json_temp:
            select_dict.append(i)
        selected = col1.selectbox("Выбор справочника", select_dict)
        save_data = col1.button("Сохранить изменения", key="save_json_dict")
        for i in json_temp["events"]:
            if i["date"]:
                i["date"] = datetime.strptime(i["date"], "%Y-%m-%dT%H:%M:%S.%f")
        column_config = {
            "id": st.column_config.NumberColumn(),
            "year_birth": st.column_config.NumberColumn(format="%d"),
            "region_id": st.column_config.SelectboxColumn(
                options=region_dict, width="large"
            ),
            "competition_id": st.column_config.SelectboxColumn(options=comp_dict),
            "round_id": st.column_config.SelectboxColumn(
                options=round_dict, width="large"
            ),
            "gender_id": st.column_config.SelectboxColumn(options=gender_dict),
            "name_rus": st.column_config.TextColumn(width="large"),
            "name_eng": st.column_config.TextColumn(width="large"),
            "date": st.column_config.DatetimeColumn(format="DD.MM.YYYY HH:mm"),
        }
        df = pd.DataFrame([json_temp])
        df_edit = col2.data_editor(
            df[selected][0], num_rows="dynamic", column_config=column_config
        )
        if save_data:
            if selected == "players":
                for i in df_edit:
                    for j in regions:
                        if i["region_id"] == j["name_rus"]:
                            i["region_id"] = j["id"]
            elif selected == "events":
                for i in df_edit:
                    for j in competitions:
                        if i["competition_id"] == j["name_rus"]:
                            i["competition_id"] = j["id"]
                    for j in rounds:
                        if i["round_id"] == j["name_rus"]:
                            i["round_id"] = j["id"]
                    for j in genders:
                        if i["gender_id"] == j["name_rus"]:
                            i["gender_id"] = j["id"]
            fs.save_to_json(path_to_file, selected, df_edit)
            col1.success("Данные сохранены")


if __name__ == "__main__":
    main(tab, path_to_folder)
