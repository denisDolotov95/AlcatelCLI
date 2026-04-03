# -*- coding: utf-8 -*-
import os
import traceback
import pandas as pd
import threading

from datetime import datetime
from typing import List, Optional


lock = threading.RLock()  # блокировка


def save_txt(file_name: str, data: str) -> bool:
    """Сохраняет данные в текстовый файл."""
    with lock:
        try:
            log_path = create_path("logs")
            if not log_path:
                return
            with open(log_path + file_name + ".txt", "a", encoding="utf-8") as file:
                file.write(data)

        except Exception:
            print(traceback.format_exc())


def save_table(
    dir_name: str,
    table_name: str,
    data: List[List[str]],
    mode: str,
    columns: Optional[List[str]],
    header: bool,
    create_backup: bool,
) -> bool:
    """Сохраняет таблицу в формат CSV."""
    with lock:
        try:
            dataframe = pd.DataFrame(columns=columns, data=data)
            dataframe.replace("-", "", inplace=True)
            table_path = create_path(dir_name)
            if not table_path:
                return
            dataframe.to_csv(
                table_path + table_name + ".csv", index=False, mode=mode, header=header
            )

            if create_backup:
                backup_path = create_path("backup")
                if backup_path:
                    backup_filename = (
                        datetime.strftime(datetime.now(), "%d.%m.%Y")
                        + "_"
                        + table_name
                        + ".csv"
                    )
                    dataframe.to_csv(
                        backup_path + backup_filename,
                        index=False,
                        mode=mode,
                        header=header,
                    )

        except Exception:
            timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            save_txt(
                "Exceptions",
                f"[{timestamp}] - [save_table]\n{traceback.format_exc()}\n",
            )


def create_path(dir_name: str) -> Optional[str]:
    """Создает абсолютный путь к нужной директории, если директории не существует, создает её."""
    with lock:
        try:
            path_main = os.getcwd()
            data_dir = os.path.join(path_main, "data")

            if not os.path.exists(data_dir):
                os.mkdir(data_dir)
                return
            target_dir = os.path.join(data_dir, dir_name)
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
                return
            new_path = os.path.join(target_dir, "")
            return new_path
        except Exception:
            timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            save_txt(
                "Exceptions",
                f"[{timestamp}] - [create_path]\n{traceback.format_exc()}\n",
            )
            return None


def delete_file(dir_name: str) -> bool:
    """Удаляет все файлы в указанной директории."""
    with lock:
        try:
            if not os.path.exists(dir_name):
                return
            names = os.listdir(dir_name)
            for name in names:
                fullname = os.path.join(dir_name, name)
                if os.path.isfile(fullname):
                    os.remove(fullname)

        except Exception:
            timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            save_txt(
                "Exceptions",
                f"[{timestamp}] - [delete_file]\n{traceback.format_exc()}\n",
            )
