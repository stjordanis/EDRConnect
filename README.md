# EDRConnect
A Fully automated EDR alert to Intezer Analyze Analysis Scanner.

# Supported EDRs
* SentinelOne

# Features
* Regonize new EDR Alerts -> Analyze in Intezer Analyze -> Write a note on EDR alert with Intezer's analysis information.

# Description


# Docker Support
```bash
docker pull intezer/edr-connect
```
* Download the [config](config.yaml) file to do execution dir.
* Change the config settings 

```bash
docker run -it -v $(pwd)/config.yaml:/code/config/config.yaml  intezer/edr-connect 
```

