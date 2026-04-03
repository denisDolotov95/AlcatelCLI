# -*- coding: utf-8 -*-
import traceback
from datetime import datetime
from typing import List, Optional
from file import save_txt

# Константы для разделителей в выводе команд
SEPARATOR_LINE = "=" * 73
DASH_SEPARATOR = "-" * 73
EMPTY_STRING = ""
DEFAULT_VLAN = "4095"


class AlcatelTableCLI:
    """
    'show port' - Display physical port information
    'show service fdb-mac' - Display FDB entry for a given MAC address
    'show service sap-using' - Display SAP information
    'show service service-using' - Display services using certain options
    'show service sdp' - Display SDP information
    'show router id interface' - Display IP interface information
    'show router id arp' - Display ARP entries
    'show router interface' - Display IP interface information
    'show router mpls lsp path detail' - Display MPLS lsp information with path detail
    'show router mpls lsp' - Display MPLS lsp information
    'admin display-config | match post-lines 30 expression "^        sdp"' - Display existing configuration with matching "^        sdp" and post-lines 30
    'admin display-config' - Display existing configuration
    """

    def __init__(self):
        self.__host: Optional[str] = None
        self.__command: List[str] = []
        self.__temp_list: List[str] = []
        self.__data_list: List[List[str]] = []
        self.__alcatel_commands = {
            "show port": self.__table_formation_info_port,
            "show service fdb-mac": self.__table_formation_service_fdb_mac,
            "show service sap-using": self.__table_formation_service_sap_using,
            "show service service-using": self.__table_formation_service_service_using,
            "show service sdp": self.__table_formation_service_sdp,
            "show router id arp": self.__table_formation_router_id_arp,
            "show router id interface": self.__table_formation_router_id_interface,
            "show router interface": self.__table_formation_router_interface,
            "show router mpls lsp": self.__table_formation_router_mpls_lsp,
            "show router mpls lsp path detail": self.__table_formation_router_mpls_lsp_path_detail,
            "admin display-config vprn/vpls interface": self.__table_formation_admin_display_config_vprn_vpls_interface,
            "admin display-config vprn/sap interface": self.__table_formation_admin_display_config_vprn_sap_interface,
            'admin display-config | match post-lines 30 expression "^        sdp"': self.__table_formation_admin_display_config_sdp_mpls,
        }

    def _get_objects(self) -> List[List[str]]:
        return self.__data_list

    def _del_objects(self) -> None:
        self.__host = None
        self.__command.clear()
        self.__temp_list.clear()
        self.__data_list.clear()

    # атрибут, который содержит в себе свойства get, set, del, doc
    table = property(_get_objects, None, _del_objects, "Doc")

    def table_formation(self, ip_address: str, command: str, data: bytes) -> None:
        """
        Формирует таблицу данных на основе вывода команды.
        
        Args:
            ip_address: IP адрес хоста, на котором была введена команда
            command: Команда, выполненная на удаленной стороне
            data: Байтовые данные вывода команды
        """
        self.__host = str(ip_address)
        self.__command = command.split()
        self.__temp_list = list(
            data.decode("utf-8", errors="backslashreplace").split("\r\n")
        )

        for key in self.__alcatel_commands.keys():
            if key.split() == self.__command:
                self.__alcatel_commands[key]()
                break

    def __table_formation_info_port(self) -> None:
        """Формирует таблицу информации о портах."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, port, admin_state, oper_state, config_mtu, oper_mtu, port_mode, port_encp, port_type <- таблица
                if (SEPARATOR_LINE in self.__temp_list[i]) and (
                    "Ports on Slot" in self.__temp_list[i + 1]
                ):
                    i += 6
                    count = 0
                    for j in range(i, len(self.__temp_list)):
                        count += 1
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if (SEPARATOR_LINE in self.__temp_list[j]) or (
                            "tdm" in self.__temp_list[j]
                        ):
                            i += count - 1
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 8:
                            continue
                        self.__data_list.append(
                            (
                                f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                f"{new_temp_list[3].replace('Link', '')} {new_temp_list[4]} "
                                f"{new_temp_list[5]} {new_temp_list[7]} {new_temp_list[8]} "
                                f"{new_temp_list[9]}"
                            ).split()
                        )
        except Exception:
            self._log_exception("table_formation_info_port")

    def _log_exception(self, method_name: str) -> None:
        """Логирует исключение с указанием метода."""
        save_txt(
            "Exceptions",
            f'[{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}] {self.__host} '
            + f"- [{method_name}]\n{traceback.format_exc()}\n",
        )

    def __table_formation_router_interface(self) -> None:
        """Формирует таблицу интерфейсов роутера."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, interface_name, admin_state, oper_state_v4, mode, port, ip_address, ip_address_mask <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list), 2):
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if (len(new_temp_list) < 5) or (
                            "Down/Down" in new_temp_list[2]
                        ):
                            continue
                        if len(new_temp_list) > 5:
                            new_temp_list.insert(
                                0, new_temp_list.pop(0) + new_temp_list[0]
                            )
                            del new_temp_list[1]
                        ip_line = self.__temp_list[j + 1].split()[0]
                        self.__data_list.append(
                            (
                                f"{self.__host} "
                                f"{new_temp_list[0].replace(',', '.').replace(' ', '')} "
                                f"{new_temp_list[1]} {new_temp_list[2].split('/')[0]} "
                                f"{new_temp_list[3]} {new_temp_list[4].split(':')[0]} "
                                f"{ip_line.split('/')[0]} {ip_line}"
                            ).split()
                        )
                    break
        except Exception:
            self._log_exception("table_formation_router_interface")

    def __table_formation_service_fdb_mac(self) -> None:
        """Формирует таблицу FDB MAC адресов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, service_id, mac_address, source_type, source, source_vlan_vc_id, pevlan <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if (DASH_SEPARATOR in self.__temp_list[j]) or (
                            "No Matching Entries" in self.__temp_list[j]
                        ):
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 6:
                            continue
                        # 1/1/11:111. * <- формат интерфейса. * - 4095, vlan 0-4095, выделим его из этого диапазона, для представления * в виде целого - уникального значения.
                        if "." in new_temp_list[2]:
                            source_vlan_vc_id = (
                                new_temp_list[2]
                                .replace(":", " ")
                                .replace(".", " ")
                                .replace("*", DEFAULT_VLAN)
                                .split()
                            )
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                    f"{source_vlan_vc_id[0]} {source_vlan_vc_id[1]} "
                                    f"{source_vlan_vc_id[3]} {source_vlan_vc_id[2]}"
                                ).split()
                            )
                        else:
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                    f"{new_temp_list[2].replace(':', ' ').replace('*', DEFAULT_VLAN)} -"
                                ).split()
                            )
                    break
        except Exception:
            self._log_exception("table_formation_service_fdb_mac")

    def __table_formation_service_sap_using(self) -> None:
        """Формирует таблицу SAP интерфейсов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, interface,port, vlan, pevlan, service_id, qos, admin_state, oper_state <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if (DASH_SEPARATOR in self.__temp_list[j]) or (
                            "No Matching Entries" in self.__temp_list[j]
                        ):
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 7:
                            continue
                        if ":" in new_temp_list[0]:
                            port_vlan = (
                                new_temp_list[0].replace(":", " ").replace("*", DEFAULT_VLAN)
                            )
                            if "." in port_vlan:
                                self.__data_list.append(
                                    (
                                        f"{self.__host} {new_temp_list[0]} "
                                        f"{str(port_vlan).replace('.', ' ')} {new_temp_list[1]} "
                                        f"{new_temp_list[2].replace('none', ' - ')} "
                                        f"{new_temp_list[5]} {new_temp_list[6]}"
                                    ).split()
                                )
                            else:
                                port_parts = port_vlan.split()
                                self.__data_list.append(
                                    (
                                        f"{self.__host} {new_temp_list[0]} "
                                        f"{port_parts[0]} {port_parts[1]} - {new_temp_list[1]} "
                                        f"{new_temp_list[2].replace('none', ' - ')} "
                                        f"{new_temp_list[5]} {new_temp_list[6]}"
                                    ).split()
                                )
                        else:
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} - - - {new_temp_list[1]} "
                                    f"{new_temp_list[2].replace('none', ' - ')} "
                                    f"{new_temp_list[5]} {new_temp_list[6]}"
                                ).split()
                            )
                    break
        except Exception:
            self._log_exception("table_formation_service_sap_using")

    def __table_formation_service_service_using(self) -> None:
        """Формирует таблицу сервисов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, service_id, service_type, admin_state, oper_state, service_name <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 5:
                            continue
                        if new_temp_list[4] == new_temp_list[-1]:
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                    f"{new_temp_list[2]} {new_temp_list[3]} -"
                                ).split()
                            )
                        elif ("VPLS" == new_temp_list[5]) or (
                            "epipe" == new_temp_list[5]
                        ):
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                    f"{new_temp_list[2]} {new_temp_list[3]} "
                                    f"{new_temp_list[-3]}_{new_temp_list[-2]}_{new_temp_list[-1]}"
                                ).split()
                            )
                        else:
                            self.__data_list.append(
                                (
                                    f"{self.__host} {new_temp_list[0]} {new_temp_list[1]} "
                                    f"{new_temp_list[2]} {new_temp_list[3]} {new_temp_list[-1]}"
                                ).split()
                            )
                    break
        except Exception:
            self._log_exception("table_formation_service_service_using")

    def __table_formation_router_id_interface(self) -> None:
        """Формирует таблицу интерфейсов роутера по ID."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, interface_name, ip_address <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            i += j
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 4:
                            continue
                        self.__data_list.append(
                            (
                                f"{self.__host} {new_temp_list[0]} "
                                f"{self.__temp_list[j + 1].split()[0]}"
                            ).split()
                        )
        except Exception:
            self._log_exception("table_formation_router_id_interface")

    def __table_formation_router_id_arp(self) -> None:
        """Формирует таблицу ARP записей роутера по ID."""
        try:
            service_id_vprn = ""
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                if "ARP Table (Service:" in self.__temp_list[i]:
                    service_id_vprn = self.__temp_list[i].split()[3][:-1]
                # host, service_id_vprn, ip_address, mac_address
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 5:
                            continue
                        self.__data_list.append(
                            (
                                f"{self.__host} {service_id_vprn} {new_temp_list[0]} "
                                f"{new_temp_list[1]}"
                            ).split()
                        )
                    break
        except Exception:
            self._log_exception("table_formation_router_id_arp")

    def __table_formation_admin_display_config_vprn_vpls_interface(self) -> None:
        """Формирует таблицу конфигурации VPRN/VPLS интерфейсов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, service_id_vprn, service_name_vprn, interface_vprn, range_ip_address, service_name_vpls, service_id_vpls ('-')  <- таблица vprn со всеми interface и vpls в данных interface
                if 'echo "Service Configuration"' in self.__temp_list[i]:
                    i += 2
                    # проходим по всем записям в теле "Service Configuration"
                    for j in range(i, len(self.__temp_list), 1):
                        if self.__temp_list[j] == "":
                            continue
                        if ("#" + "-" * 50) in self.__temp_list[j]:
                            break
                        if (
                            "vprn" in self.__temp_list[j]
                            and "description" in self.__temp_list[j + 1]
                        ):  # находим конфигурацию vprn
                            service_id_vprn = self.__temp_list[j].split()[1]
                            service_name_vprn = self.__temp_list[j + 1].split('"')[1]
                            j += 2
                            # проходим по всем записям в теле конфигурации vprn
                            for k in range(j, len(self.__temp_list), 1):
                                if "customer" in self.__temp_list[k]:
                                    break
                                if (
                                    "interface" in self.__temp_list[k]
                                    and "create" in self.__temp_list[k]
                                    and "shutdown" not in self.__temp_list[k + 1]
                                ):
                                    interface_vprn = self.__temp_list[k].split('"')[1]
                                    k += 1
                                    # проходим по всем интерфейсам, в данном vprn
                                    for g in range(k, len(self.__temp_list), 1):
                                        if (
                                            "interface" in self.__temp_list[g]
                                            and "create" in self.__temp_list[g]
                                            or "customer" in self.__temp_list[g]
                                        ):
                                            break
                                        if "address" in self.__temp_list[g]:
                                            range_ip_address = self.__temp_list[
                                                g
                                            ].split()[1]
                                        if "vpls" in self.__temp_list[g]:
                                            service_name_vpls = self.__temp_list[
                                                g
                                            ].split('"')[1]
                                            self.__data_list.append(
                                                (
                                                    f"{self.__host} {service_id_vprn} {service_name_vprn.replace(' ','_')} "
                                                    + f"{interface_vprn.replace(' ','_')} {range_ip_address} "
                                                    + f"{service_name_vpls.replace(' ','_')} -"
                                                ).split()
                                            )
            if self.__data_list:
                service_id_vpls = ""
                temp_service_name_vpls = ""
                for i in range(len(self.__temp_list)):
                    if self.__temp_list[i] == EMPTY_STRING:
                        continue
                    if self.__temp_list[i] == self.__temp_list[-1]:
                        break
                    # дополняем список новыми значениями service_id_vpls  <- таблица vprn со всеми interface и vpls в данных interface
                    if (
                        "vpls" in self.__temp_list[i]
                        and "create" in self.__temp_list[i]
                        and "name" in self.__temp_list[i]
                        and "pbb" not in self.__temp_list[i + 1]
                    ):
                        service_id_vpls = self.__temp_list[i].split()[1]
                        temp_service_name_vpls = (
                            self.__temp_list[i].split('"')[1].replace(" ", "_")
                        )
                        i += 1
                        for j in range(i, len(self.__temp_list), 1):
                            if (
                                "vpls" in self.__temp_list[i + 1]
                                and "create" in self.__temp_list[i + 1]
                            ):
                                i += j
                                break
                            if "sap" in self.__temp_list[j]:
                                for k in range(0, len(self.__data_list), 1):
                                    if self.__data_list[k][5] == temp_service_name_vpls:
                                        self.__data_list[k][6] = service_id_vpls
                                        break
                                break
                    elif (
                        "vpls" in self.__temp_list[i]
                        and "create" in self.__temp_list[i]
                        and "pbb" not in self.__temp_list[i + 1]
                    ):
                        service_id_vpls = self.__temp_list[i].split()[1]
                        i += 1
                        for j in range(i, len(self.__temp_list), 1):
                            if (
                                "vpls" in self.__temp_list[i + 1]
                                and "create" in self.__temp_list[i + 1]
                            ):
                                i += j
                                break
                            if (
                                "service-name" in self.__temp_list[j]
                                and "sap" in self.__temp_list[j + 1]
                            ):
                                temp_service_name_vpls = (
                                    self.__temp_list[j].split('"')[1].replace(" ", "_")
                                )
                                for k in range(0, len(self.__data_list), 1):
                                    if self.__data_list[k][5] == temp_service_name_vpls:
                                        self.__data_list[k][6] = service_id_vpls
                                        break
                                break
        except Exception:
            self._log_exception("table_formation_admin_display_config_vprn_vpls_interface")

    def __table_formation_admin_display_config_vprn_sap_interface(self) -> None:
        """Формирует таблицу конфигурации VPRN/SAP интерфейсов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, service_id_vprn, service_name_vprn, interface_vprn, range_ip_address, service_name_vpls, service_id_vpls ('-')  <- таблица vprn со всеми interface и vpls в данных interface
                if 'echo "Service Configuration"' in self.__temp_list[i]:
                    i += 2
                    # проходим по всем записям в теле "Service Configuration"
                    for j in range(i, len(self.__temp_list), 1):
                        if self.__temp_list[j] == "":
                            continue
                        if ("#" + "-" * 50) in self.__temp_list[j]:
                            break
                        if (
                            "vprn" in self.__temp_list[j]
                            and "description" in self.__temp_list[j + 1]
                        ):  # находим конфигурацию vprn
                            service_id_vprn = self.__temp_list[j].split()[1]
                            service_name_vprn = self.__temp_list[j + 1].split('"')[1]
                            j += 2
                            # проходим по всем записям в теле конфигурации vprn
                            for k in range(j, len(self.__temp_list), 1):
                                if "customer" in self.__temp_list[k]:
                                    break
                                if (
                                    "interface" in self.__temp_list[k]
                                    and "create" in self.__temp_list[k]
                                    and "shutdown" not in self.__temp_list[k + 1]
                                ):
                                    interface_vprn = self.__temp_list[k].split('"')[1]
                                    k += 1
                                    # проходим по всем интерфейсам, в данном vprn
                                    for g in range(k, len(self.__temp_list), 1):
                                        if (
                                            "interface" in self.__temp_list[g]
                                            and "create" in self.__temp_list[g]
                                            or "customer" in self.__temp_list[g]
                                        ):
                                            break
                                        if (
                                            "address" in self.__temp_list[g]
                                            and "/" in self.__temp_list[g]
                                        ):
                                            range_ip_address = self.__temp_list[
                                                g
                                            ].split()[1]
                                        if "sap" in self.__temp_list[g]:
                                            sap_interface = self.__temp_list[g].split()[
                                                1
                                            ]
                                            if ":" in sap_interface:
                                                port, vlan = sap_interface.split(":")
                                            else:
                                                port, vlan = sap_interface, "-"
                                            self.__data_list.append(
                                                (
                                                    f"{self.__host} {service_id_vprn} {service_name_vprn.replace(' ','_')} "
                                                    + f"{interface_vprn.replace(' ','_')} {range_ip_address} "
                                                    + f"{sap_interface} {port} {vlan}"
                                                ).split()
                                            )
        except Exception:
            self._log_exception("table_formation_admin_display_config_vprn_sap_interface")

    def __table_formation_service_sdp(self) -> None:
        """Формирует таблицу SDP сервисов."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, sdp_id, oper_mtu, far_end, admin_state, oper_state <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 8:
                            continue
                        self.__data_list.append(
                            (
                                f"{self.__host} {new_temp_list[0]} {new_temp_list[2]} "
                                f"{new_temp_list[3]} {new_temp_list[4]} {new_temp_list[5]}"
                            ).split()
                        )
                    break
        except Exception:
            self._log_exception("table_formation_service_sdp")

    def __table_formation_router_mpls_lsp(self) -> None:
        """Формирует таблицу MPLS LSP."""
        try:
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, lsp_name, to_far_end, admin_state, oper_state <- таблица
                if DASH_SEPARATOR in self.__temp_list[i]:
                    i += 1
                    for j in range(i, len(self.__temp_list)):
                        if self.__temp_list[j] == EMPTY_STRING:
                            continue
                        if DASH_SEPARATOR in self.__temp_list[j]:
                            break
                        new_temp_list = self.__temp_list[j].split()
                        if len(new_temp_list) < 6:
                            continue
                        self.__data_list.append(
                            (
                                f"{self.__host} {new_temp_list[0].replace(' ', '')} "
                                f"{new_temp_list[1]} {new_temp_list[4]} {new_temp_list[5]}"
                            ).split()
                        )
                    break
        except Exception:
            self._log_exception("table_formation_router_mpls_lsp")

    def __table_formation_router_mpls_lsp_path_detail(self) -> None:
        """Формирует таблицу детальной информации о пути MPLS LSP."""
        try:
            name_mpls_lsp = ""
            ip_address_to_far_end = ""
            out_interface = ""
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, name_lsp, out_interface, to_far_end, number_hops, interface_ip_address, system_ip_address <- таблица
                if (DASH_SEPARATOR in self.__temp_list[i]) and (
                    "LSP Name" in self.__temp_list[i + 1]
                ):
                    i += 1
                    for j in range(i, len(self.__temp_list), 1):
                        if self.__temp_list[j] == "":
                            continue
                        if "LSP Name" in self.__temp_list[j]:
                            name_mpls_lsp = (
                                self.__temp_list[j]
                                .split(":")[1]
                                .split("  ")[0]
                                .replace(" ", "")
                            )
                            if not name_mpls_lsp:
                                name_mpls_lsp = " - "

                        if (
                            "From" in self.__temp_list[j]
                            and "To" in self.__temp_list[j]
                        ):
                            ip_address_to_far_end = self.__temp_list[j].split()[5]
                        elif (
                            "From" in self.__temp_list[j]
                            and "To" in self.__temp_list[j + 1]
                        ):
                            ip_address_to_far_end = self.__temp_list[j + 1].split()[2]

                        if (
                            "Out" in self.__temp_list[j]
                            and "Interface" in self.__temp_list[j]
                        ):
                            out_interface = (
                                self.__temp_list[j].split(":")[1].split("  ")[0]
                            )
                        # не должно быть No Hops Specified
                        if ("Actual" in self.__temp_list[j]) and (
                            "No Hops Specified" not in self.__temp_list[j + 1]
                        ):
                            j += 1
                            number_hops = 0  # порядковый номер хопа, для определения узла в path
                            for g in range(j, len(self.__temp_list)):
                                number_hops += 1
                                if ("Computed" in self.__temp_list[g]) or (
                                    "Record Label" not in self.__temp_list[g]
                                ):
                                    break
                                new_temp_list = (
                                    self.__temp_list[g].replace("->", "").split(")")
                                )
                                lsp_name_clean = name_mpls_lsp.replace(",", ".").replace(" ", "")
                                if "(" in new_temp_list[0]:
                                    hop_parts = new_temp_list[0].split("(")
                                    self.__data_list.append(
                                        (
                                            f"{self.__host} {lsp_name_clean} {out_interface} "
                                            f"{ip_address_to_far_end} {number_hops} "
                                            f"{hop_parts[0]} {hop_parts[1]}"
                                        ).split()
                                    )
                                else:
                                    self.__data_list.append(
                                        (
                                            f"{self.__host} {lsp_name_clean} {out_interface} "
                                            f"{ip_address_to_far_end} {number_hops} "
                                            f"{new_temp_list[0].split()[0]} {ip_address_to_far_end}"
                                        ).split()
                                    )
                            i += j
                            break
        except Exception:
            self._log_exception("table_formation_router_mpls_lsp_path_detail")

    def __table_formation_admin_display_config_sdp_mpls(self) -> None:
        """Формирует таблицу конфигурации SDP MPLS."""
        try:
            sdp_id = ""
            far_end = ""
            name_lsp = ""
            for i in range(len(self.__temp_list)):
                if self.__temp_list[i] == EMPTY_STRING:
                    continue
                if self.__temp_list[i] == self.__temp_list[-1]:
                    break
                # host, sdp_id, far_end, name_lsp <- таблица
                if (
                    ("sdp" in self.__temp_list[i])
                    and ("create" in self.__temp_list[i])
                    and ("spoke" not in self.__temp_list[i])
                ):
                    sdp_id = self.__temp_list[i].split()[1]
                    i += 1
                    for j in range(i, len(self.__temp_list), 1):
                        if "exit" in self.__temp_list[j]:
                            if not far_end or not name_lsp:
                                i += j
                                break
                            self.__data_list.append(
                                (
                                    f"{self.__host} {sdp_id} {far_end} {name_lsp}"
                                ).split()
                            )
                            i += j
                            break
                        if "far-end" in self.__temp_list[j]:
                            far_end = self.__temp_list[j].split()[1]
                        if "lsp" in self.__temp_list[j]:
                            name_lsp = (
                                self.__temp_list[j]
                                .split('"')[1]
                                .replace(",", ".")
                                .replace(" ", "")
                            )
        except Exception:
            self._log_exception("table_formation_admin_display_config_sdp_mpls")
