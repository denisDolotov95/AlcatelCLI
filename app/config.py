# -*- coding: utf-8 -*-
import os
import json

"""
    SAS-M 7210, SAR 7705, SR 7750, IXR-e 7250
"""
# ----------------------------------------------------------------------------------------
SCHEDULE_TIME = os.environ.get("SCHEDULE_TIME", "00:30")
# ----------------------------------------------------------------------------------------
NUMBER_THREADS = os.environ.get("NUMBER_THREADS", 3)
# ----------------------------------------------------------------------------------------
PATH_ALCATEL_NETWORK_ELEMENTS = (
    "./data/ne_alcatel/all_alcatel_network_elements_on_men.csv"
)
# ----------------------------------------------------------------------------------------
SSH_CONNECTION = {
    "login": os.environ.get("SSH_LOGIN", ""),
    "password": os.environ.get("SSH_PASS", ""),
    "auth_timeout": 30,
}
# ----------------------------------------------------------------------------------------
SSH_COMMANDS = json.loads(
    os.environ.get("SSH_COMMANDS", "[]")
)  # команды для каждого сетевого устройства
# ----------------------------------------------------------------------------------------
NAME_AND_COLUMNS_FOR_CSV_TABLE = {
    "all_command": {
        "info_port": "host port admin_state oper_state config_mtu oper_mtu port_mode port_encp port_type",
        "service_sap_using": "host interface port vlan pevlan service_id qos admin_state oper_state",
        "service_fdb_mac": "host service_id mac_address source_type source source_vlan_vc_id pevlan",
        "service_service_using": "host service_id service_type admin_state oper_state service_name",
        # 'all_service_sdp': 'host sdp_id oper_mtu far_end admin_state oper_state',
        # 'all_router_mpls_lsp': 'host lsp_name to_far_end admin_state oper_state',
        "router_mpls_lsp_path_detail": "host name_lsp out_interface ip_address_to_far_end number_hop interface_ip_address system_ip_address",
        "admin_display_config_mpls_sdp": "host sdp_id ip_address_far_end name_lsp",
        "router_interface": "host interface_name admin_state oper_state_v4 mode port ip_address ip_address_mask",
    },
    "arp": {
        "vprn_arp_vpls": "host service_id_vprn ip_address mac_address service_id_vpls",
        "vprn_arp_sap": "host service_id_vprn ip_address mac_address interface port vlan",
        "vprn_interface_vpls": "host service_id_vprn service_name_vprn interface_vprn ip_address_mask service_name_vpls service_id_vpls",
        "vprn_interface_sap": "host service_id_vprn service_name_vprn interface_vprn ip_address_mask interface port vlan",
    },
}  # для формирования столбцов (columns) pandas имеет формат dict ['1','2'...], формирование таблицы с определенным форматом колонок
# ----------------------------------------------------------------------------------------
