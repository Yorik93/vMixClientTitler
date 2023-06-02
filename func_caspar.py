from amcp_pylib.core import Client
import streamlit as st
from amcp_pylib.module.query import BYE, KILL
from amcp_pylib.module.template import CG_ADD, CG_STOP, CG_CLEAR


# Инициализируем клиент CasparCG
@st.cache_resource
def initialize_client(ip, port):
    client = Client()
    client.connect(ip, port)
    st.session_state["client"] = client


# Функция для закрытия соединения
def close_connection():
    client = st.session_state["client"]
    client.send(BYE())
    st.session_state["client"] = None


def kill_server():
    client = st.session_state["client"]
    client.send(KILL())
    st.session_state["client"] = None


def play_template(template_name, data=None):
    # создаем экземпляр класса CasparCG
    client = st.session_state["client"]
    print(data)
    # создаем команду для воспроизведения шаблона
    command = CG_ADD(
        video_channel=1,
        layer=20,
        cg_layer=1,
        template=template_name,
        play_on_load=1,
        data=data,
    )
    # отправляем команду на сервер
    response = client.send(command)
    # возвращаем ответ
    return response


def stop_template():
    # создаем экземпляр класса CasparCG
    client = st.session_state["client"]
    # создаем команду для воспроизведения шаблона
    command = CG_STOP(
        video_channel=1,
        layer=20,
        cg_layer=1,
    )
    # отправляем команду на сервер
    response = client.send(command)
    # возвращаем ответ
    return response


def clear_channel():
    # создаем экземпляр класса CasparCG
    client = st.session_state["client"]
    # создаем команду для воспроизведения шаблона
    command = CG_CLEAR(
        video_channel=1,
        layer=20,
    )
    # отправляем команду на сервер
    response = client.send(command)
    # возвращаем ответ
    return response
