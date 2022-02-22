# EDRConnect
A fully automated EDR alert to Intezer Analyze Analysis Scanner.

# Supported EDRs
* SentinelOne

# Coming Soon
* CrowdStike support

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


![Screen Shot 2022-02-22 at 12 25 41](https://user-images.githubusercontent.com/63956508/155113278-fc57a9bc-b91f-4833-bf5b-6c2c807b5bc2.png)

