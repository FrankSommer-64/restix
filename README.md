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

Restix needs Python 3 and restic Version 0.17 or above.
The GUI is based on PySide 6, 
Restix has been tested on Linux Mint 22, Fedora xx, FreeBSD 14 and Windows 11.


### Installation
Fully featured installation:
1. pip install restix
2. Enter URL and credentials in file .tcms.conf in your home directory to access Kiwi TCMS using XML-RPC
3. Configure restix according to your needs in directory .config/restix under your home directory.
Core features without GUI:
Binary install


## Usage

Restix offers a GUI for local configuration and development on test automation. Start the GUI with <pre>grestix</pre>.

Command line interface for automated tasks is also available:
<ul>
  <li>Run a test plan: <pre>restix --plan mytestplan --product-version "v0.8" --product-build "240120"</pre></li>
  <li>Export a product: <pre>restix --product myproduct /tmp/issai-export</pre></li>
  <li>Import a test result: <pre>restix /tmp/myproduct/plan_24_result.toml</pre></li>
</ul>



## Roadmap

- [ ] v0.7 full functionality to run tests
- [ ] v0.8 full functionality for import and export, CI integration
- [ ] v0.9 Windows support, localization, complete system test

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
