# Kafka_License_Exporter

This is a python component that can query a list of provided Kafka brokers and extract license information and expose license expiry details to Prometheus as open-metrics standard.

This component implements the ideas presented in the approach-2 (Licnese Exporter to Prometheus) presented in https://confluence.dell.com/display/KAFKA/Kafka+License+Monitoring+and+Alerting



Initial Configuration
---
first install all the packages
~~~
> pip install -r requirements.txt -v
~~~

Broker configurations
---
Broker configurations are maintained in the _**config.yml**_ file.

Getting help
---
~~~
> python3 LicenseExporter.py --help
usage: LicenseExporter.py [-h] -p   -c   [-w ]
 
handles command line arguments for License Expiry monitoring
 
optional arguments:
  -h, --help            show this help message and exit
  -p  , --port          the port for prometheus endpoint: default=None
  -c  , --config-path
                        file path to yml file containing target kafka
                        clusters: default=None
  -w  , --workers       Number of workers to handle concurrent requests to
                        kafka clusters:default=8

~~~
Running the component
---
!!! Before running make sure the credentials entered in config.yml are correct!!!

To run the code Just execute the following
~~~
 >  python3 LicenseExporter.py -p 8000 -c ./config.yml
~~~

Testing
---
once the component sharts ruinning, it opens a http server at port nr 8000.
check in your browse http://<hostaddress>:8000/metrics

The following is a sample output
```
license_expiry_in_days{cluster="perf",exp_date="2024-05-30 07:00:00",host="CKFPLPC1PRFB01.amer.dell.com:9092"} 843.0
license_expiry_in_days{cluster="poc_upgrade",exp_date="2024-05-30 07:00:00",host="ckfnlr2cpocb001.us.dell.com:9092"} 843.0
license_expiry_in_days{cluster="dtc_stg",exp_date="2024-05-30 07:00:00",host="ckfplpc1sdtcb01.us.dell.com:9092"} 843.0
license_expiry_in_days{cluster="itp_apj_sit",exp_date="NA",host="ckfnlr2csipab01.amer.dell.com:9092"} -255.0    # -255 THE LICENSE INFOR COULDNOT BE RECEIVED FROM CLUSTER
license_expiry_in_days{cluster="itp_apj_prf",exp_date="NA",host="ckfnlr2cpipab01.amer.dell.com:9092"} -255.0    # -255 THE LICENSE INFOR COULDNOT BE RECEIVED FROM CLUSTER
license_expiry_in_days{cluster="itp_emea_sit",exp_date="2022-08-30 07:00:00",host="ckfnlr2csipeb01.amer.dell.com:9092"} 204.0
license_expiry_in_days{cluster="itp_emea_prf",exp_date="2022-08-30 07:00:00",host="ckfnlr2cpipeb01.amer.dell.com:9092"} 204.0
license_expiry_in_days{cluster="itp_dev",exp_date="2024-05-30 07:00:00",host="ckfnlr2citpb001.amer.dell.com:9092"} 843.0
license_expiry_in_days{cluster="srs_np",exp_date="2024-05-30 07:00:00",host="ckfpls3bssrsb01.amer.dell.com:9092"} 843.0
license_expiry_in_days{cluster="std_np",exp_date="2022-10-13 07:00:00",host="ckfnlstdb01.amer.dell.com:9092"} 248.0
license_expiry_in_days{cluster="dfs_np",exp_date="2022-10-13 07:00:00",host="ckfnlr2cdfsb01.amer.dell.com:9092"} 248.0
license_expiry_in_days{cluster="mlt_np",exp_date="2024-05-30 07:00:00",host="ckfnlr2cmltb001.us.dell.com:9092"} 843.0
license_expiry_in_days{cluster="cre_np",exp_date="2024-05-30 07:00:00",host="ckfnlr2ccreb001.amer.dell.com:9092"} 843.0
```
Notice -255 is used as values if the license expiry days value if it is not received from that cluster 

Trouble shooting
---
1. Errors.NoBrokersAvailable()
You will get the following error if the user credentials passed in the conf.yml files is incorrect.

\lib\site-packages\kafka\client_async.py", line 927, in check_version 
raise Errors.NoBrokersAvailable()
