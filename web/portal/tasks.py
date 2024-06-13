from celery import shared_task
from .models import *

import docker
import json


'''
Subdomain and DNS checks
'''
'''
Run Subfinder to find related subdomains.
'''
@shared_task()
def subdomainSubfinder(domain):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/subfinder:v2.6.6",
        ["-silent", "-nW", "-oI", "-d", domain, "-oJ"],
        remove=True,
    )
    return output


'''
Run tlsx to find domains based on certificate.
'''
@shared_task()
def subdomainTlsx(domain):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/tlsx:v1.1.6",
        ["-silent", "-san", "-cn", "-host", domain, "-json"],
        remove=True,
    )
    return output


'''
Run Oneforall to find related subdomains.
'''
@shared_task()
def subdomainOneforall(domain):
    client = docker.from_env()

    output = client.containers.run(
        "shmilylty/oneforall:latest",
        ["--target", domain, "--fmt", "json", "--path", "/dev/stdout", "run"],
        remove=True,
    )
    return output


'''
Run Shuffledns to bruteforce related subdomains with mounted wordlists.
'''
@shared_task()
def subdomainShuffledns(domain):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/shuffledns:v1.0.8",
        ["-silent", "-d", domain, "-w", "/mnt/wordlists/dns/best-dns-wordlist.txt", ""],
        volumes={'/reconplane/wordlists': {'bind': '/mnt/wordlists', 'mode': 'ro'}, 
                 '/reconplane/configfiles': {'bind': '/mnt/configfiles', 'mode':'ro'}}, #hardcoded values
        remove=True,
    )
    return output


@shared_task(serializer='json')
def subdomains_processing(input, domain):
    lines = input.decode().splitlines()
    ToolJson.objects.db_manager("tools").create(asset="test",toolname="test",assettype="test",date="2024-06-13",output=[json.loads(line) for line in lines if line.strip()])
    domain_instance = Domain.objects.get(name=domain)
    for x in lines:
        line = json.loads(x)
        if line["host"] != line["input"]:
            subdomain, created = Subdomain.objects.get_or_create(domain=domain_instance, name=line["host"])
            ipaddress, created = IPAddress.objects.get_or_create(ipaddress=line["ip"])
            ipaddress.domain.add(subdomain)
        else:
            pass
    return 



'''
Portscans, tech-detect and waf/cloud checks
'''

'''
Run Cdncheck to find cloud-hosted and waf protected hosts.
'''
@shared_task()
def cdnWafCheck(subdomainOrIpAddress):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/cdncheck:v1.0.9",
        ["-i", subdomainOrIpAddress, "-cloud", "-waf", "-silent", "-j"],
        remove=True,
    )
    return output


'''
Run Naabu to find open ports on ip-addresses, as well as subdomains (that are not cloud/CDN).
'''
@shared_task()
def portscanNaabu(subdomainOrIpAddress):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/naabu:v2.3.0",
        ["-p", "-", "-host", subdomainOrIpAddress, "-silent", "-j"],
        remove=True,
    )
    return output


'''
Run Nuclei to detect technologies and running applications.
'''
@shared_task()
def technologyNuclei(subdomainOrIpAddressWithPort):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/nuclei:v3.2.2",
        ["-u", f"https://{subdomainOrIpAddressWithPort}", "-t", "http/technologies", "-silent", "-j"],
        volumes={'/reconplane/templates/nuclei': {'bind': '/mnt/templates', 'mode': 'ro'}}, #hardcoded values
        remove=True,
    )
    return output


'''
Run httpx to detect technologies and running applications.
'''
@shared_task()
def technologyHttpx(subdomainOrIpAddressWithPort):
    client = docker.from_env()

    output = client.containers.run(
        "projectdiscovery/httpx:v1.6.0",
        ["-u", f"https://{subdomainOrIpAddressWithPort}", "-td", "-bp", "-title", "-sc", "-server", "-fr", "-include-chain", "-favicon", "-j"],
        remove=True,
    )
    return output


'''
Javascript/file download
'''