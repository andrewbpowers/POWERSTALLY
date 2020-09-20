# POWERSTALLY - Tally Light for OBS Studio (fully Plug-and-Play)
by Andrew B. Powers (www.andrewbpowers.com // https://github.com/andrewbpowers/POWERSTALLY)

## Use

### Hardware & Setup

Please see https://www.andrewbpowers.com/stories/2020/9/11/powerstally

### Configuration

Set the port in [line 37](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L37). 
Set the websocket password in [line 38](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L38).

Set the character that triggers the light in [line 41](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L41).

Set the GPIO pins in [line 44](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L44) and in [line 45](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L45).

Set the GPIO pin value for high active or low active LEDs/Relays in [line 51](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L51) for the OFF value and in [line 55](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L55) for the ON value.

By default, the script will create a new logfile every day. If you wish to have only one logfile, comment out [line 66](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L66) and uncomment [line 63](https://github.com/andrewbpowers/POWERSTALLY/blob/master/powerstally.py#L63).

## License

Documentation is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)

Software is licensed under a [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt)
