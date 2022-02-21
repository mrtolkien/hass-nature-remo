# Home Assistant integration for Nature Remo

A [Nature Remo](https://en.nature.global/en/) integration for [Home Assistant](https://www.home-assistant.io).

Only a custom component at the moment, but the goal is to merge it to the mainline repo at some point.

## Supported features

- [x] Air Conditioner
  - [x] Mode (e.g. cool, warm, blow etc.)
  - [x] Temperature
  - [x] Fan mode
  - [x] Swing mode
  - [x] Current temperature
  - [x] Remembers previous target temperatures when switching modes back and forth
- [x] Energy Sensor
  - [x] Fetch current power usage
- [x] Light
  - Only on/off at the moment
- [ ] TV
  - Work in progress @MrTolkien
- [ ] Sensors
  - Work in progress @MrTolkien
- [ ] Switch
  
## Installation

Add the contents of `custom_components/nature_remo` to the `/config/custom_components/nature_remo` folder of your 
Home Assistant installation. You can either copy the folder directly or set up a symbolic link/docker mount.

Files structure:
```
{/config}
├── configuration.yaml
└── custom_components
    └── nature_remo
        ├── __init__.py
        ├── climate.py
        ├── manifest.json
        ├── light.json
        └── sensor.py
              
```

## Configuration

1. Go to https://home.nature.global and sign in
1. Generate access token
1. Add the token to your `configuration.yaml` file:

```yaml
nature_remo:
  access_token: YOUR_ACCESS_TOKEN
```

4. Restart Home Assistant
5. All appliances should have been added to your `Configuration` -> `Entities` tab

## Special thanks

Special thanks to @yutoyazaki for doing the [first implementation](https://github.com/yutoyazaki/hass-nature-remo).

This implementation is basically a rewrite of Yuto Yazaki's, made with the goal of being more maintainable and complete.

### Notes

I do not own a Nature Remo E/E Lite, so I cannot verify or test the code for it. I'm relying fully on @yutoyazaki's 
code there. 