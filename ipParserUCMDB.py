#coding=utf-8
import re
import logger

from appilog.common.system.types import ObjectStateHolder
from appilog.common.system.types.vectors import ObjectStateHolderVector


def get_port_number(logString):
    '''
    На вход подаётся строка из логов, из которой через регулярное выражение парсятся айпишники и порты
    На выходе функции список портов
    '''
    pattern = r'((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,5})|(\*\:\d{1,5}))'
    results = re.finditer(pattern, logString)
    ports = []
    for result in results:
        ip_port = result.group(0).split(':')
        if ip_port[0] != '127.0.0.1':
            ports.append(ip_port[1])
    return ports


def create_ipOSH(ipAddress):
    ''' Создание OSH для входящей CI ip_address '''
    ipOsh = ObjectStateHolder("ip")
    ipAddressString = str(ipAddress)
    ipOsh.setStringAttribute("ip_address", ipAddressString)
    ipOsh.setStringAttribute("name", ipAddressString)
    return ipOsh


def DiscoveryMain(Framework):
    OSHVResult = ObjectStateHolderVector() # Итоговый вектор

    # Входные данные
    ip = Framework.getDestinationAttribute('ip_address')
    credentials = Framework.getAvailableProtocols('ssh')

    # Генерим OSH на основе Ip
    ipOSH = create_ipOSH(ip)

    for cred_id in credentials:
        try:
            client = Framework.createClient(cred_id)                # Создаём клиента на основе кредов
            result = client.executeCmd('ss -t4n state listening')   # Запускаем команду на скан портов
            result = result.split('\n')
            
            # Парсим логи
            ports = []
            for line in result:
                ports.extend(get_port_number(line))
            logger.debug('there is listening ports:', ports)

            # создаём OSHки, кидаем в вектор
            for port in ports:
                ipSerEndpointOSH = ObjectStateHolder('ip_service_endpoint')
                ipSerEndpointOSH.setAttribute('bound_to_ip_address', str(ip))
                ipSerEndpointOSH.setAttribute('network_port_number', port)
                ipSerEndpointOSH.setAttribute('port_type', 'tcp')
                portName = '%s:%s' %(ip, port)
                ipSerEndpointOSH.setStringAttribute("name", portName)
                ipSerEndpointOSH.setContainer(ipOSH) 
                OSHVResult.add(ipSerEndpointOSH)
                
        except Exception, e:
            logger.debug("smth was wrong", e)

    return OSHVResult
