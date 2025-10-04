[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/FrankSommer-64/restix">
    <img src="restix-icon.png" alt="Logo" width="128" height="128">
  </a>

<h3 align="center">Restix</h3>
  <p align="center">
    Wrapper around open source backup application restic.
    <br />
    <a href="https://github.com/FrankSommer-64/restix"><strong>Documentation</strong></a>
    <br />
    <br />
    <a href="https://github.com/FrankSommer-64/restix/issues">Report Bug</a>
    ·
    <a href="https://github.com/FrankSommer-64/restix/issues">Request Feature</a>
  </p>
</div>


## About The Project

Restix mainly addresses users doing manual backups for multiple computers and
favoring restic for this purpose.  
Restix works on backup targets, i.e. directories containing restic repositories
for every user, host and year. This concept shall minimize data inconsistencies
compared to a single restic repository.  
A backup target may exist either locally (e.g. on a USB stick or drive),
or on a remote machine.  
Restix provides both a graphical and a command line interface.


## Getting Started

### Prerequisites

Restix needs Python, version 3.10 or higher and restic, version 0.10 or higher.  
At least restic version 0.17 is required to enjoy full restix functionality.  
The GUI is based on PySide 6.  
Restix has been tested on Linux Mint 22, Fedora 42 and Windows 11.


### Installation

Binary installation (Linux deb):

1. Download restix-0.9.6.deb for full functionality, restix-core-0.9.6.deb lacks the GUI
1. Verify package integrity
1. Install the package using apt with administrator privileges

Binary installation (Linux rpm):

1. Download restix-0.9.6-1.fc42.noarch.rpm for full functionality, restix_core-0.9.6-1.fc42.noarch.rpm lacks the GUI
1. Verify package integrity
1. Install the package using dnf with administrator privileges

Binary installation (Windows):

1. Download install_restix_0.9.6.exe for system-wide installation, install_restix_0.9.6_local.exe for installation per user
1. Verify package integrity
1. Run the installer, administrator privileges needed for system-wide installation

Manual installation (Linux only):

1. Download restix package restix-0.9.6-custom.zip for manual installation
1. Verify package integrity
1. Extract package into temporary directory
1. Open installation script in an editor an adjust path variables according to your needs
1. Save installation script
1. Run installation script (root permissions required for a system-wide installation)


## Usage

Restix offers a GUI for backup, restore and configuration.  
Run the GUI from start menu or with **grestix** from console.

Command line interface for automated tasks is also available. Examples:

- Create a backup: ```restix backup --auto-create usbstick-a```
- Restore: ```restix restore --snapshot latest --restore-path /tmp usbstick-a```
- Initialize repository: ```restix init usbstick-a```
- Unlock repository: ```restix unlock usbstick-a```
- List snapshots: ```restix snapshots usbstick-a```
- Show snapshot contents: ```restix ls --snapshot latest usbstick-a```
- Search element: ```restix find --pattern *.conf usbstick-a```


## Roadmap

- v0.9.7 GUI usability improvements
- v0.9.8 system tested GUI
- v1.0 system tested command line interface

See [open issues](https://github.com/FrankSommer-64/restix/issues) for a full list of proposed features (and known issues).


## Contributing

Any contributions you make are **greatly appreciated**.



## License

Distributed under the MIT License. See [LICENSE][license-url] for more information.



## Contact

Frank Sommer - Frank.Sommer@sherpa-software.de

Project Link: [https://github.com/FrankSommer-64/restix](https://github.com/FrankSommer-64/restix)

[contributors-shield]: https://img.shields.io/github/contributors/FrankSommer-64/restix.svg?style=for-the-badge
[contributors-url]: https://github.com/FrankSommer-64/restix/graphs/contributors
[issues-shield]: https://img.shields.io/github/issues/FrankSommer-64/restix.svg?style=for-the-badge
[issues-url]: https://github.com/FrankSommer-64/restix/issues
[license-shield]: https://img.shields.io/github/license/FrankSommer-64/restix.svg?style=for-the-badge
[license-url]: https://github.com/FrankSommer-64/restix/blob/master/LICENSE
