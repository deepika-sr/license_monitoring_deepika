# Kafka_License_Exporter

This is a python component that can query a list of provided Kafka brokers and extract license information and expose license expiry details to Prometheus as open-metrics standard.

This component implements that ideas presented in the approach-2 (Licnese Exporter to Prometheus) presented in https://confluence.dell.com/display/KAFKA/Kafka+License+Monitoring+and+Alerting



Initial Configurtation
---
first install all the packages
~~~
> pip install -r requirements.txt -v
~~~

Broker configurations
---
Broker configurations are maintained in the config.yml file.


How to run the component 
---
!!! Before running make sure the credentials entered in  _**config.yml**_  are correct!!!

To run the code Just execute the following 
~~~
 > python3 LicenseExporter.py 
~~~
Testing
---
once the component sharts ruinning, it opens a http server at port nr 8000.
check in your browse http://<hostaddress>:8000/metrics


Trouble shooting
---
1. Errors.NoBrokersAvailable()
You will get the following error if the user credentials passed in the conf.yml files is incorrect.

\lib\site-packages\kafka\client_async.py", line 927, in check_version 
raise Errors.NoBrokersAvailable()
