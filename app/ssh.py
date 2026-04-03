# -*- coding: utf-8 -*-
import paramiko
import traceback
from time import sleep
from datetime import datetime
from socket import error as SocketError, timeout as SocketTimeout
from ipaddress import IPv4Address, IPv4Interface

from file import save_txt, save_table
from cli import AlcatelTableCLI


class RunCommand:

    def __init__(self, format: "AlcatelTableCLI"):

        self.__ssh_ip = None
        self.__data = (
            b""  # инициализация объекта для храниня информации из stdout на узле
        )
        self.__format = format
        self.__client = paramiko.SSHClient()

    def connect(self, ssh_ip, ssh_user_name, ssh_user_pass, ssh_auth_timeout):

        try:
            self.__ssh_ip = ssh_ip
            # вносим ключ ssh сервера в перечень известных нам хостов
            self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Подключение
            self.__client.connect(
                hostname=self.__ssh_ip,
                username=ssh_user_name,
                password=ssh_user_pass,
                port=22,
                allow_agent=False,
                look_for_keys=False,
                auth_timeout=ssh_auth_timeout,
                timeout=60,  # timeout -> TCP
            )
            return True
        except paramiko.ssh_exception.SSHException as err:
            self._log_connection_error("connect", str(err))
        except EOFError:
            error_msg = (
                "Closed before all the bytes could be read / Stream has been closed"
            )
            save_txt(
                "Exceptions_Paramiko",
                f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] '
                f"{self.__ssh_ip} - [connect]\n{traceback.format_exc()}\n",
            )
            self._log_connection_error("connect", error_msg)
        except SocketTimeout:
            error_msg = "Connection didn't established by timed out"
            self._log_connection_error("connect", error_msg)
        except SocketError as err:
            self._log_connection_error("connect", str(err))
        except Exception:
            save_txt(
                "Exceptions_Paramiko",
                f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] '
                f"{self.__ssh_ip} - [connect]\n{traceback.format_exc()}\n",
            )
            self._close_connection()

    def execute(self, commands):

        try:
            with self.__client.invoke_shell() as self.__ssh:
                self.__ssh.settimeout(30)
                self.__receive_data()
                self.__ssh.send("environment no more\n")
                self.__receive_data()
                for type_request, command in commands.items():
                    self.__ssh.send(f"{command}\n")
                    sleep(1)
                    self.__receive_data()
                    self.__save_recived_data(type_request, command)
        except paramiko.ssh_exception.SSHException as err:
            self._log_execution_error("execute", str(err))
        except EOFError:
            error_msg = (
                "Closed before all the bytes could be read / Stream has been closed"
            )
            self._log_execution_error("execute", error_msg)
        except SocketTimeout:
            error_msg = "Connection didn't established by timed out"
            self._log_execution_error("execute", error_msg)
        except SocketError as err:
            self._log_execution_error("execute", str(err))
        except Exception:
            save_txt(
                "Exceptions_Paramiko",
                f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] '
                f"{self.__ssh_ip} - [execute]\n{traceback.format_exc()}\n",
            )

    def execute_arp(self, type_network_element):

        try:
            with self.__client.invoke_shell() as self.__ssh:
                self.__ssh.settimeout(30)
                self.__receive_data()
                self.__ssh.send("environment no more\n")
                self.__receive_data()
                # Информация по всем интерфейсам в vprn
                self.__ssh.send("admin display-config\n")
                sleep(1)
                self.__receive_data()

                sap_interface = self.__vprn_interface("sap")
                if type_network_element == "7750":
                    vpls_interface = self.__vprn_interface("vpls")
                    all_vprn_service_id = self.__vprn_service_id()
                    self.__vprn_arp_vpls(vpls_interface, all_vprn_service_id)
                    self.__vprn_arp_sap(sap_interface, all_vprn_service_id)
                else:
                    all_vprn_service_id = self.__vprn_service_id()
                    self.__vprn_arp_sap(sap_interface, all_vprn_service_id)
        except paramiko.ssh_exception.SSHException as err:
            self._log_execution_error("execute_arp", str(err))
        except EOFError:
            error_msg = (
                "Closed before all the bytes could be read / Stream has been closed"
            )
            self._log_execution_error("execute_arp", error_msg)
        except SocketTimeout:
            error_msg = "Connection didn't established by timed out"
            self._log_execution_error("execute_arp", error_msg)
        except SocketError as err:
            self._log_execution_error("execute_arp", str(err))
        except Exception:
            save_txt(
                "Exceptions_Paramiko",
                f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] '
                f"{self.__ssh_ip} - [execute_arp]\n{traceback.format_exc()}\n",
            )

    def __vprn_interface(self, type_interface: str) -> list:
        """Получает интерфейсы VPRN указанного типа."""
        all_vprn_interface = []
        if self.__data is not None and self.__data != b"":
            self.__format.table_formation(
                self.__ssh_ip,
                f"admin display-config vprn/{type_interface} interface",
                self.__data,
            )
            if self.__format.table:
                all_vprn_interface.extend(self.__format.table)
                save_table(
                    dir_name="arp",
                    table_name=f"vprn_interface_{type_interface}",
                    data=self.__format.table,
                    mode="a",
                    columns=None,
                    header=False,
                    create_backup=False,
                )
            del self.__format.table
        return all_vprn_interface

    def __vprn_service_id(self) -> list:
        """Получает список ID сервисов VPRN."""
        # Информация по всем сервисам vprn
        self.__ssh.send("show service service-using vprn\n")
        sleep(1)
        self.__receive_data()
        all_vprn_service_id = []
        if self.__data is not None and self.__data != b"":
            self.__format.table_formation(
                self.__ssh_ip, "show service service-using", self.__data
            )
            if self.__format.table:
                all_vprn_service_id.extend(self.__format.table)
            del self.__format.table
        return all_vprn_service_id

    def __vprn_arp_vpls(
        self, all_vprn_interface: list, all_vprn_service_id: list
    ) -> None:
        """Формирует ARP таблицу для VPLS интерфейсов."""
        # Формирование arp таблицы
        for i in range(len(all_vprn_service_id)):
            self.__ssh.send(f"show router {all_vprn_service_id[i][1]} arp\n")
            sleep(1)
            self.__receive_data()
            if self.__data is not None and self.__data != b"":
                self.__format.table_formation(
                    self.__ssh_ip, "show router id arp", self.__data
                )
                if self.__format.table:
                    for j in range(len(self.__format.table)):
                        for g in range(len(all_vprn_interface)):
                            if (
                                IPv4Address(self.__format.table[j][2])
                                in IPv4Interface(all_vprn_interface[g][4]).network
                                and self.__format.table[j][1]
                                == all_vprn_interface[g][1]
                            ):
                                self.__format.table[j].append(all_vprn_interface[g][6])
                                break
                        else:
                            self.__format.table[j].clear()
                    last_data = [data for data in self.__format.table if data]
                    save_table(
                        dir_name="arp",
                        table_name="vprn_arp_vpls",
                        data=last_data,
                        mode="a",
                        columns=None,
                        header=False,
                        create_backup=False,
                    )
                del self.__format.table

    def __vprn_arp_sap(
        self, all_vprn_interface: list, all_vprn_service_id: list
    ) -> None:
        """Формирует ARP таблицу для SAP интерфейсов."""
        # Формирование arp таблицы
        for i in range(len(all_vprn_service_id)):
            self.__ssh.send(f"show router {all_vprn_service_id[i][1]} arp\n")
            sleep(1)
            self.__receive_data()
            if self.__data is not None and self.__data != b"":
                self.__format.table_formation(
                    self.__ssh_ip, "show router id arp", self.__data
                )
                if self.__format.table:
                    for j in range(len(self.__format.table)):
                        for g in range(len(all_vprn_interface)):
                            if (
                                self.__format
                                and IPv4Address(self.__format.table[j][2])
                                in IPv4Interface(all_vprn_interface[g][4]).network
                                and self.__format.table[j][1]
                                == all_vprn_interface[g][1]
                            ):
                                self.__format.table[j].extend(
                                    [
                                        all_vprn_interface[g][-3],
                                        all_vprn_interface[g][-2],
                                        all_vprn_interface[g][-1],
                                    ]
                                )
                                break
                        else:
                            self.__format.table[j].clear()
                    last_data = [data for data in self.__format.table if data]
                    save_table(
                        dir_name="arp",
                        table_name="vprn_arp_sap",
                        data=last_data,
                        mode="a",
                        columns=None,
                        header=False,
                        create_backup=False,
                    )
                del self.__format.table

    def __save_recived_data(self, type_request: str, command: str) -> None:
        """Сохраняет полученные данные в таблицу."""
        if self.__data is not None and self.__data != b"":
            self.__format.table_formation(self.__ssh_ip, command, self.__data)
            if self.__format.table:
                save_table(
                    dir_name="all_command",
                    table_name=type_request,
                    data=self.__format.table,
                    mode="a",
                    columns=None,
                    header=False,
                    create_backup=False,
                )
            del self.__format.table
        else:
            raise Exception(f"Received data by {command} was empty")

    def _close_connection(self) -> None:
        """Закрывает SSH соединение."""
        try:
            self.__client.close()
        except Exception:
            pass  # Игнорируем ошибки при закрытии

    def _log_connection_error(self, method_name: str, error_msg: str) -> None:
        """Логирует ошибку подключения."""
        timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        save_table(
            dir_name="logs",
            table_name="Exceptions_Paramiko",
            data=[f"{timestamp},{self.__ssh_ip},{error_msg}".split(",")],
            mode="a",
            columns=None,
            header=False,
            create_backup=False,
        )
        self._close_connection()

    def _log_execution_error(self, method_name: str, error_msg: str) -> None:
        """Логирует ошибку выполнения команды."""
        timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
        save_table(
            dir_name="logs",
            table_name="Exceptions_Paramiko",
            data=[f"{timestamp},{self.__ssh_ip},{error_msg}".split(",")],
            mode="a",
            columns=None,
            header=False,
            create_backup=False,
        )

    def __receive_data(self) -> None:
        """Принимает данные из SSH сессии."""
        self.__data = b""
        while True:
            temp_data = self.__ssh.recv(8192)
            self.__data += temp_data
            if (
                len(temp_data) >= 2
                and temp_data.decode("utf-8", errors="backslashreplace")[-2] == "#"
            ):
                break
            if len(temp_data) == 0:
                raise Exception("Function __receive_data received zero payload")
