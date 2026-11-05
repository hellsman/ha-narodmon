*Please :star: this repo if you find it useful*

# NarodMon Cloud Integration Component for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE.md)

[![hacs][hacs-shield]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![Support me on Patreon][patreon-shield]][patreon]

[![Community Forum][forum-shield]][forum]

_Component to integrate with Narodmon cloud and automatic search for the nearest sensors of the required type._

![NarodMon Logo](narodmon-logo.png)

## Known Limitations and Issues

- The Narodmon service has limits on the amount of data returned per request and on the frequency of sending requests. Therefore, if you configure several sensors, at first some of them may be in the `Unavailable` state. As data is received from the server, all sensors will receive their values.
- Updates more than once a minute are prohibited by Narodmon and can lead to permanent blocking of your account.

## Breaking changes

- Since version 2.3.0, configuration via `configuration.yaml` has been removed. All configuration is now done through the Home Assistant UI by adding the "Narodmon" integration.
- Since version 2.3.0, the integration supports two servers: Global (narodmon.com) and RU (narodmon.ru). The default server is Global.
- Since version 2.0.0 the field `apikey` is no longer required and is not recommended. Fill it out only if you already have your own API key with special limits. Otherwise, remove this field from your configuration.
- Since version 2.1.0, the ability to specify the radius of the sensors search zone has been added. The default radius is set to 10 km.

## Installation

### Install via HACS (recommended)

1. Have [HACS][hacs] installed, this will allow you to easily manage and track updates.
1. Search for "Narodmon".
1. Click Install below the found integration.
1. Restart Home Assistant.
1. In the HA UI go to "Configuration" > "Integrations" click "+" and search for "Narodmon".

### Manual installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `narodmon`.
4. Download file `narodmon.zip` from the [latest release section][releases-latest] in this repository.
5. Extract _all_ files from this archive you downloaded in the directory (folder) you created.
6. Restart Home Assistant.
7. In the HA UI go to "Configuration" > "Integrations" click "+" and search for "Narodmon".

### Configuration

Configuration is done entirely through the Home Assistant UI:

1. Go to "Settings" > "Devices & services" > "Integrations" and click the "Add integration" button.
2. Search for "Narodmon".
3. Select the server you want to use:
   - **Global (narodmon.com)** - the main server for most regions.
   - **RU (narodmon.ru)** - the Russian server.
4. Enter your API key (obtained from [narodmon.com](https://narodmon.com/) -> `Profile` > `My applications` > `New key`).
5. Configure optional settings: SSL verification and connection timeout.
6. After adding the integration, you can configure sensor options in the integration settings:
   - **Use my home location** - use the location defined in Home Assistant as the center point for sensor search (default: enabled). Disable this option to enter custom latitude and longitude.
   - **Show entities on map** - enable showing sensor locations on the map.
   - **Scan interval** - how often the integration updates data (default: 3 minutes).
   - **Search area radius** - the maximum distance from your home to look for sensors (default: 10 km).

### Configuration Variables

The integration is configured through the UI. The following options are available:

**server**:\
  _(select) (**Required**)_\
  Choose the Narodmon server to use.\
  - `Global (narodmon.com)` - the main server for most regions.\
  - `RU (narodmon.ru)` - the Russian server.\
  _Default value: Global (narodmon.com)_

**apikey**:\
  _(string) (**Required**)_\
  The API key is a unique identifier that authenticates requests associated with your project. You can obtain it by registering on [narodmon.com](https://narodmon.com/), then opening `Profile` > `My applications` > `New key`. You can give the key any name at your discretion.

**center_home**:\
  _(boolean) (Optional) (Default value: True)_\
  Use the location defined in Home Assistant as the center point for sensor search. If disabled, you can enter custom latitude and longitude below.

**verify_ssl**:\
  _(boolean) (Optional) (Default value: True)_\
  Verify SSL/TLS certificate for HTTPS request.

**timeout**:\
  _(number) (Optional) (Default value: 10)_\
  Timeout for the connection in seconds.

**latitude** (manual):\
  _(number) (Optional)_\
  Latitude of the center point of the sensor search area. Used only when "Use my home location" is disabled.

**longitude** (manual):\
  _(number) (Optional)_\
  Longitude of the center point of the sensor search area. Used only when "Use my home location" is disabled.

After adding the integration, you can configure the following options:

**show_on_map**:\
  _(boolean) (Optional)_\
  Enables showing the location of the weather station on the map.\
  _Default value: false_

**search_area_radius**:\
  _(number) (Optional) (Default value: 10)_\
  Maximum allowed distance from described location to sensor location. Unit: kilometers (km).

**scan_interval**:\
  _(number) (Optional) (Default value: 180)_\
  Minimum time interval between updates, in seconds.

> **_Note_**:\
> Since the service has data update limits, if you configure several sensors, the actual data update period may be proportionally longer than the one specified in this field.
>
> Updates more than once a minute are prohibited by Narodmon and can lead to permanent blocking of your account.

The integration automatically discovers nearby sensors and creates sensor entities for all types:\n  `temperature`, `humidity`, `pressure`, `wind_speed`, `wind_bearing`, `precipitation`, `illuminance`, `radiation`, `uv`, `pm`.

## Track updates

You can automatically track new versions of this component and update it by [HACS][hacs].

## Troubleshooting

To enable debug logs use this configuration:
```yaml
# Example configuration.yaml entry
logger:
  default: info
  logs:
    custom_component.narodmon: debug
```
... then restart HA.

## Contributions are welcome!

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We have set up a separate document containing our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Authors & contributors

The original setup of this component is by [Andrey "Limych" Khrolenok](https://github.com/Limych).

For a full list of all authors and contributors,
check [the contributor's page][contributors].

This Home Assistant custom component was created and is updated using the [HA-Blueprint template](https://github.com/Limych/ha-blueprint). You can use this template to maintain your own Home Assistant custom components.

## License

creative commons Attribution-NonCommercial-ShareAlike 4.0 International License

See separate [license file](LICENSE.md) for full text.

***

[component]: https://github.com/Limych/ha-narodmon
[commits-shield]: https://img.shields.io/github/commit-activity/y/Limych/ha-narodmon.svg?style=popout
[commits]: https://github.com/Limych/ha-narodmon/commits/dev
[hacs-shield]: https://img.shields.io/badge/HACS-Default-orange.svg?style=popout
[hacs]: https://hacs.xyz
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=popout
[forum]: https://community.home-assistant.io/t/narodmon-cloud-integration/285737
[license]: https://github.com/Limych/ha-narodmon/blob/main/LICENSE.md
[license-shield]: https://img.shields.io/badge/license-Creative_Commons_BY--NC--SA_License-lightgray.svg?style=popout
[maintenance-shield]: https://img.shields.io/badge/maintainer-Andrey%20Khrolenok%20%40Limych-blue.svg?style=popout
[releases-shield]: https://github.com/Limych/ha-narodmon/releases
[releases]: https://github.com/Limych/ha-narodmon/releases
[releases-latest]: https://github.com/Limych/ha-narodmon/releases/latest
[user_profile]: https://github.com/Limych
[report_bug]: https://github.com/Limych/ha-narodmon/issues/new?template=bug_report.md
[suggest_idea]: https://github.com/Limych/ha-narodmon/issues/new?template=feature_request.md
[contributors]: https://github.com/Limych/ha-narodmon/graphs/contributors
[patreon-shield]: https://img.shields.io/endpoint.svg?url=https%3A%2F%2Fshieldsio-patreon.vercel.app%2Fapi%3Fusername%3DLimych%26type%3Dpatrons&style=popout
[patreon]: https://www.patreon.com/join/limych
