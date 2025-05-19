[![Contributors][contributors-shield]][contributors-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/FrankSommer-64/restix">
    <img src="images/restix.png" alt="Logo" width="128" height="128">
  </a>

<h3 align="center">Restix</h3>
  <p align="center">
    Graphical user interface for backup and restore with restic.
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

Restix mainly provides a GUI for the open source backup application restic.<br/>


## Getting Started

### Prerequisites

Restix needs Python, version 3.10 and above and restic. Restic version 0.17 or above is required if you like
restix to create repositories automatically if needed.
The GUI is based on PySide 6.
Restix has been tested on Linux Mint 22, Fedora 42, FreeBSD 14 and Windows 11.


### Installation

Binary installation:
1. Download appropriate installation package for your system
2. Install the package with administrator privileges

Manual installation:
1. Download restix Python wheel and start scripts
2. Create root directory for restix application (may require administrator privileges)
3. Copy restix wheel and start scripts to restix root directory
4. Change to restix root directory
5. Create virtual Python environment (python3 -m venv .venv)
6. Activate virtual Python environment (source .venv/bin/activate)
7. Install restix wheel (pip3 install <restix wheel filename>)
8. Deactivate virtual Python environment (deactivate)
9. Create links to start scripts in a directory in your path (/usr/local/bin or $HOME/bin)


## Usage

Restix offers a GUI for backup, restore and configuration.
Start the GUI with <pre>grestix</pre>.

Command line interface for automated tasks is also available:
<ul>
  <li>Create a backup: <pre>restix backup --batch --auto-create usbstick-a</pre></li>
  <li>Restore: <pre>restix restore --batch --snapshot latest --restore-path /tmp usbstick-a</pre></li>
  <li>List snapshots: <pre>restix --batch snapshots usbstick-a</pre></li>
</ul>


## Roadmap

- [ ] v0.9.5 system tests
- [ ] v0.9.6 Windows support
- [ ] v0.9.7 full documentation and manuals

See the [open issues](https://github.com/FrankSommer-64/restix/issues) for a full list of proposed features (and known issues).


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
