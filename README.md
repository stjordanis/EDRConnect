# EDRConnect
A fully automated EDR alert to Intezer Analyze Analysis Scanner.

# Supported EDRs
* SentinelOne

# Coming Soon
* CrowdStrike support

# Description
![Screen Shot 2022-02-22 at 13 08 24](https://user-images.githubusercontent.com/63956508/155120445-ce29c53e-1353-4426-9871-c1e9ce418759.png)


This app was developed in order to provide a lightweight and simple way to automate EDR alert triage using Intezer Analyze.
* The app automatically detects new EDR alerts and creates Intezer Analyze analyses.
* The analysis information is then written on a **note** in the EDR's alert.

**The app doesn't affect anything on the alert other than written a note.**

The app is cautious about quota consumption and is configurable in that regard.([config](config.yaml#L38))

# Support
EDR Connect only supports Enterprise and trial users.
EDR Connect can be hosted by Intezer for our **Enterpise** users.
Please contact our [support](support@intezer.com). 

# Docker Support
```bash
docker pull intezer/edr-connect
```
* Copy the [config](config.yaml) file to your execution dir.
* Change the config settings 

```bash
docker run -it -v $(pwd)/config.yaml:/code/config/config.yaml  intezer/edr-connect 
```


https://user-images.githubusercontent.com/63956508/155152834-68725f47-0dd1-4db2-a759-54101cc12c56.mov


