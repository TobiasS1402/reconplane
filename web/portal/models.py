from django.core.exceptions import ValidationError
from django.db import models

from simple_history.models import HistoricalRecords
from djongo import models as dmodels
import tldextract

class DomainField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        super().__init__(*args, **kwargs)       

    def db_type(self, connection):
        return 'varchar'

    def _extract_domain_parts(self, value):
        return tldextract.extract(value)

    def _validate(self, value):
        if value:
            extracted = self._extract_domain_parts(value)
            if not extracted.registered_domain:
                raise ValidationError("Invalid domain name")
        else:
            raise ValidationError("Empty domain name")
        
    def to_python(self, value):
        extracted = self._extract_domain_parts(value)
        return extracted.registered_domain


class SubdomainField(models.Field):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 255
        super().__init__(*args, **kwargs)   

    def db_type(self, connection):
        return 'varchar'

    def _extract_domain_parts(self, value):
        return tldextract.extract(value)

    def _validate(self, value):
        if value:
            extracted = self._extract_domain_parts(value)
            if not extracted.subdomain:
                raise ValidationError("Invalid subdomain name")
        else:
            raise ValidationError("Empty subdomain name")
        
    def to_python(self, value):
        extracted = self._extract_domain_parts(value)
        return extracted.subdomain
    

class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ASN(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='asn')
    number = models.PositiveIntegerField()
    history = HistoricalRecords()

    def __str__(self):
        return self.number


class Domain(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='domain')
    name = DomainField()
    description = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name
 

class Subdomain(models.Model):
    name = SubdomainField()
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='subdomain')
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    def fqdn(self):
        return(self.domain + self.name)


class IPAddress(models.Model):
    ipaddress = models.GenericIPAddressField(protocol='both',unpack_ipv4=False)
    domain = models.ManyToManyField(Subdomain, related_name='ipaddress',  null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.ipaddress


class DNSRecord(models.Model):
    ARecord = models.ManyToManyField(IPAddress, blank=True, related_name='arecord')
    AAAARecord = models.ManyToManyField(IPAddress, blank=True, related_name='aaaarecord')
    CNAMERecord = models.CharField(max_length=255, blank=True)
    NSRecord = models.CharField(max_length=255, blank=True)
    PTRRecord = models.CharField(max_length=255, blank=True)
    SOARecord = models.CharField(max_length=255, blank=True)
    TXTRecord = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()
    
    def A(self):
        return self.ARecord
    
    def AAAA(self):
        return self.AAAARecord


class Netblock(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='netblock', null=True, blank=True)
    asn = models.ForeignKey(ASN, on_delete=models.CASCADE, null=True, blank=True)
    ipaddress = models.OneToOneField(IPAddress, on_delete=models.CASCADE) 
    name = models.CharField(max_length=100)
    cidr = models.PositiveSmallIntegerField()
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.ipaddress}/{self.cidr}"


class Port(models.Model):
    ipaddress = models.ManyToManyField(IPAddress, null=True, blank=True)
    subdomain = models.ManyToManyField(Subdomain, null=True, blank=True) 
    number = models.PositiveIntegerField()
    protocol = models.CharField(max_length=3)
    service = models.CharField(max_length=100, blank=True) # what's this service
    description = models.TextField(blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.number

    def proto(self):
        return f"{self.number}/{self.protocol}"


'''
Djongo MongoDB models:
'''
class ToolJson(dmodels.Model):
    asset = models.CharField(max_length=255)
    assettype = models.CharField(max_length=255)
    date = models.DateTimeField()
    toolname = models.CharField(max_length=255) 
    output = models.JSONField()