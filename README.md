# EDRConnect
A fully automated EDR alert to Intezer Analyze Analysis Scanner.

# Supported EDRs
* SentinelOne

# Coming Soon
* CrowdStike support

# Flow
* Pull new EDR Alerts -> Analyze in Intezer Analyze -> Write a note on EDR alert with Intezer's analysis information

# Description
This app was developed in order to support a lightweight and simple way to automate EDR alert triage using Intezer Analyze.

* The app automatically detects new EDR alerts and creates Intezer Analyze analyses.
* The analysis information is then written on a note in the EDR's alert.

The app is cautious about quota consumption and is configurable in that regard.([config](config.yaml#L7))



# Docker Support
```bash
docker pull intezer/edr-connect
```
* Download the [config](config.yaml) file to do execution dir.
* Change the config settings 

```bash
docker run -it -v $(pwd)/config.yaml:/code/config/config.yaml  intezer/edr-connect 
```

