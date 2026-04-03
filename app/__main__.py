# -*- coding: utf-8 -*-
import schedule
import pandas as pd
import traceback
import logging

import config as cfg

from datetime import datetime
from time import sleep
from ssh import RunCommand
from multiprocessing import Process, get_logger
from queue import Queue, Empty
from threading import Thread

from cli import AlcatelTableCLI
from file import delete_file, create_path, save_txt


# планировщик задач по таймингу
def run_schedule(type_network_element: list) -> None:
    """Запускает планировщик задач."""
    schedule.every().day.at(cfg.SCHEDULE_TIME).do(create_process, type_network_element)
    # schedule.every().minutes.do()
    # schedule.every().hour.do()
    while True:
        schedule.run_pending()
        sleep(1)


# создание процессов для ssh сессии / форматирование таблиц csv
def create_process(type_network_element: list) -> None:
    """Создает процессы для SSH сессий и форматирования таблиц CSV."""
    name_base_dir = list(cfg.NAME_AND_COLUMNS_FOR_CSV_TABLE.keys())[0]
    delete_file(f"data/{name_base_dir}")
    base_path = create_path(name_base_dir)
    if base_path:
        for name_csv_file, columns in cfg.NAME_AND_COLUMNS_FOR_CSV_TABLE[
            "all_command"
        ].items():
            dataframe = pd.DataFrame(columns=columns.split())
            dataframe.to_csv(base_path + f"{name_csv_file}.csv", index=False)

    list_process = []
    for name in type_network_element:  # создание процесса по типу устройства
        process = Process(
            target=create_threads, args=[cfg.NUMBER_THREADS, name], daemon=False
        )
        list_process.append(process)
        process.start()
    for process in list_process:  # ожидание завершения процессов
        process.join()


# создание потоков
def create_threads(number_threads: int, type_network_element: str) -> None:
    """Создает потоки для обработки сетевых элементов."""
    alcatel_network_elements = pd.DataFrame(
        pd.read_csv(cfg.PATH_ALCATEL_NETWORK_ELEMENTS)
    )
    alcatel_network_elements.drop_duplicates(keep=False)  # False : Drop all duplicates.

    list_ip_address = []
    for row, _ in alcatel_network_elements.iterrows():
        # поиск всех ip адресов с указанным типом устройства
        if type_network_element in alcatel_network_elements["type_ne"][row]:
            list_ip_address.append(alcatel_network_elements["ip_address"][row])

    que = Queue(maxsize=0)
    for ip_address in list_ip_address:  # формирование очереди
        que.put(ip_address)
    for _ in range(number_threads):  # создание потока
        stream = Thread(target=run_ssh, args=[type_network_element, que], daemon=False)
        stream.start()
    que.join()  # ставим блокировку до тех пор пока не будут выполнены все задания


# подключение к сетевым устройствам
def run_ssh(type_network_element: str, que: Queue) -> None:
    """Подключается к сетевым устройствам через SSH и выполняет команды."""
    decrypted_ssh_login = cfg.SSH_CONNECTION["login"]
    decrypted_ssh_pass = cfg.SSH_CONNECTION["password"]

    ssh_session = RunCommand(format=AlcatelTableCLI())
    # вытаскиваем из que (очереди) все ip адреса до того, пока он не пуст (вызов исключения Queue.Empty)
    while True:
        try:
            ip_address = que.get_nowait()  # берем из очереди ip_address
            status_connection_ssh = ssh_session.connect(
                ip_address,
                decrypted_ssh_login,
                decrypted_ssh_pass,
                cfg.SSH_CONNECTION["auth_timeout"],
            )
            if status_connection_ssh:
                ssh_session.execute(cfg.SSH_COMMANDS)
            que.task_done()
        except Empty:  # ловим исключение, которое сигнализирует о пустой очереди
            break
        except Exception:
            que.task_done()
            save_txt(
                "Exceptions",
                f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] '
                f"- [run_ssh]\n{traceback.format_exc()}\n",
            )


if __name__ == "__main__":

    logger = get_logger()  # наследуем логер, который описан в multiprocessing
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s/%(processName)s] - %(message)s"
    )
    handler = logging.FileHandler(filename="app.log", mode="a")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    run_schedule(["7210", "7250", "7705", "7750"])