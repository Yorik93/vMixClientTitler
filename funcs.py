import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import json
from io import BytesIO
from datetime import datetime


# Функция для чтения файла конфигурации
def read_config(config_path):
    tree = ET.parse(config_path)
    root = tree.getroot()
    config = {}
    for child in root:
        if child.tag == "channels":
            channels = []
            for channel in child:
                channel_config = {}
                for param in channel:
                    channel_config[param.tag] = param.text
                channels.append(channel_config)
            config["channels"] = channels
        else:
            config[child.tag] = child.text
    return config


# Функция для записи файла конфигурации
def write_config(config_path, config):
    root = ET.Element("configuration")
    for key, value in config.items():
        if key == "channels":
            channels_element = ET.Element("channels")
            for channel in value:
                channel_element = ET.Element("channel")
                for param_name, param_value in channel.items():
                    param_element = ET.Element(param_name)
                    param_element.text = param_value
                    channel_element.append(param_element)
                channels_element.append(channel_element)
            root.append(channels_element)
        else:
            element = ET.Element(key)
            element.text = value
            root.append(element)
    tree = ET.ElementTree(root)
    tree.write(config_path)


video_mode_list = [
    "PAL",
    "NTSC",
    "576p2500",
    "720p2398",
    "720p2400",
    "720p2500",
    "720p5000",
    "720p2997",
    "720p5994",
    "720p3000",
    "720p6000",
    "1080p2398",
    "1080p2400",
    "1080i5000",
    "1080i5994",
    "1080i6000",
    "1080p2500",
    "1080p2997",
    "1080p3000",
    "1080p5000",
    "1080p5994",
    "1080p6000",
    "1556p2398",
    "1556p2400",
    "1556p2500",
    "dci1080p2398",
    "dci1080p2400",
    "dci1080p2500",
    "2160p2398",
    "2160p2400",
    "2160p2500",
    "2160p2997",
    "2160p3000",
    "2160p5000",
    "2160p5994",
    "2160p6000",
    "dci2160p2398",
    "dci2160p2400",
    "dci2160p2500",
]


@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df


def load_json_data(data_json):
    with open(data_json, "r", encoding="utf-8") as file:
        temp_json = json.load(file)
    return temp_json


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
