# POWERSTALLY - Tally Light for OBS Studio (fully Plug-and-Play)
by Andrew B. Powers (www.andrewbpowers.com // https://github.com/andrewbpowers/POWERSTALLY)

## Use

### Hardware & Setup

Please see https://www.andrewbpowers.com/stories/2020/9/11/powerstally

### Configuration

Set the port in [line 37](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL37).
Set the websocket password in [line 38](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL38).

Set the character that triggers the light in [line 41](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL41).

Set the GPIO pins in [line 44] (https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL44) and in [line 45] (https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL45).

Set the value for high active or low aktive LEDs/Relays GPIO in [line 49] (https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL49).

By default, the script will create a new logfile every day. If you wish to have only one logfile, comment out [line 60](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L60) and uncomment [line 57](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.pyL57).

## License

Documentation is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)

Software is licensed under a [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt)
