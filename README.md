# Blogger Download Auto Post V1.1

## Overview

Blogger Download Auto Post V1.1 is a lightweight automatic posting system for Blogger websites focused on downloadable resources such as:

* 3D Models
* CAD Files
* Vector Graphics
* SVG
* PSD
* STL
* SketchUp Models
* SolidWorks Resources
* Autodesk Resources

The primary goal of this project is simplicity, stability, and continuous automatic publishing.

Version 1.1 intentionally avoids unnecessary complexity. Advanced features are reserved for Version 2.

---

# Design Goals

* Easy to install
* Easy to configure
* Easy to maintain
* Easy to expand
* Configuration driven
* Minimal dependencies

---

# Main Features

* Automatic Topic Generation
* AI Article Writing
* SEO Metadata
* Automatic Labels
* Download Source Collection
* Image Collection
* Blogger Auto Publish
* Queue Management
* GitHub Actions Support

---

# Project Structure

```text
blogger-download-autopost-v1.1/

config/
data/
modules/
docs/

main.py
requirements.txt
README.md
```

---

# Supported Blogs

Current Version supports:

* Drawing and Graphics
* Engineering 3DCad Application
* Vector Graphic Free Downloads
* SolidWorks Share
* Autodesk Knowledge

Additional blogs can be added later using configuration files.

---

# Configuration Philosophy

The project is designed so that almost every setting can be modified without editing Python source code.

Users should normally edit files inside:

```text
config/
```

instead of changing program logic.

---

# AI Provider

Current Version

* Google Gemini

Future Versions may support additional providers.

---

# Image Strategy

Priority order

1. Download source preview image
2. Free image source
3. No image

AI image generation is intentionally excluded from Version 1.1.

---

# Queue System

Each blog maintains its own posting queue.

Workflow

Generate Topics

↓

Store Queue

↓

Write Article

↓

Publish

↓

Remove From Queue

↓

Continue

---

# Documentation

Detailed documentation is available in the docs folder.

---

# Version Policy

Version 1.1 focuses only on production-ready features.

Features intentionally excluded:

* Dashboard
* Database
* Docker
* Local AI
* Stable Diffusion
* AI Image Generation
* Analytics
* Plugin System

These features are planned for Version 2.

---

# Development Principle

If a feature does not directly help the system publish blog posts, it should not be included in Version 1.1.

---

# License

Private Project
