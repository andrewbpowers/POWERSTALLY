# POWERSTALLY - Tally Light for OBS Studio (fully Plug-and-Play)

## Use

### Hardware & Setup

Please see https://www.andrewbpowers.com/stories/2020/6/26/studio-rack-powersrack

### Configuration

By default, the script will create a new logfile every day.  If you wish to have only one logfile, comment out [line 30](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L30) and uncomment [line 29](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L29).

Set the character that triggers the LED in [line 37](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L37).

Set the websocket password in [line 49](https://github.com/td0g/OBS_TallyLight/blob/76f0a91a4130b9426cd6d66720c012547c89aded/tallylight.py#L49).

## License

Documentation is licensed under a [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)

Software is licensed under a [GNU GPL v3 License](https://www.gnu.org/licenses/gpl-3.0.txt)
