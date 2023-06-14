import json
import base64
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime


@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df


def load_json_data(data_json):
    with open(data_json, "r", encoding="utf-8") as file:
        temp_json = json.load(file)
    return temp_json


def save_to_json(path_to_file, block, df_edit):
    try:
        temp_json = df_edit.to_json(orient="records")
        temp_json = json.loads(temp_json)

        for item in temp_json:
            if "Дата" in item:
                item["Дата"] = datetime.fromtimestamp(
                    (item["Дата"] - 10800000) / 1000
                ).strftime("%Y-%m-%dT%H:%M:%S")
    except AttributeError:
        temp_json = df_edit

    data_json = load_json_data(path_to_file)
    data_json[block] = temp_json
    with open(path_to_file, "w", encoding="utf-8") as outfile:
        json.dump(data_json, outfile, ensure_ascii=False, indent=4)


def data_cash(var_json):
    if var_json != []:
        for i in var_json:
            if i == {"Переменная": "", "Текст": ""}:
                continue
            if "d$" in i["Текст"]:
                i["Текст"] = i["Текст"].replace("d$", "st.session_state['data']")

            temp_txt = (
                i["Текст"].replace("st.session_state['data']['", "").split("']")[0]
            )
            if f"_{temp_txt}" in st.session_state["data"]:
                i["Текст"] = (
                    f"st.session_state['data']['_{temp_txt}']"
                    + i["Текст"].split("['data']")[1].split("['")[1].split("']")[1]
                )
            try:
                st.session_state["data"]["_" + i["Переменная"]] = eval(i["Текст"])
            except AttributeError:
                i["Текст"] = i["Текст"].split("'].")[0] + "']"
                st.session_state["data"]["_" + i["Переменная"]] = eval(i["Текст"])
    return var_json


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Sheet1")
    workbook = writer.book
    worksheet = writer.sheets["Sheet1"]
    format1 = workbook.add_format({"num_format": "0.00"})
    worksheet.set_column("A:A", None, format1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def ReadPictureFile(path_file):
    try:
        return base64.b64encode(open(path_file, "rb").read()).decode()
    except:
        return ""
