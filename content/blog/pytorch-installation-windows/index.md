---
title: "Pytorch Installation on Windows 11"
date: 2024-12-26T22:43:24+01:00
draft: false

# post thumb
image: "/images/post/pytorch-installation-windows/logo.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
  - Machine Learning
tags:
  - python
  - pytorch

# post type
type: "post"
---

Installation of Pytorch using Miniforge3 on Windows 11
<!--more-->

## Introduction

PyTorch is a widely-used open-source machine learning library originally developed by Meta AI. Over time, it has gained significant traction and emerged as one of the leading frameworks in the machine learning ecosystem. Today, PyTorch operates under the governance of the Linux Foundation, further solidifying its role in the open-source community.

<br/>
In this tutorial, we will guide you through the process of installing PyTorch on a Windows 11 machine using the Miniforge package manager.

### Prerequisites
To follow this tutorial, ensure you have the following:

* A laptop or PC (preferably equipped with an NVIDIA GPU and CUDA support)
* Python version 3.9 or later (bundled with Miniforge during installation)

## Installation

PyTorch can typically be installed via Anaconda or Pip, but in this tutorial, we’ll use Miniforge. Miniforge is a free, community-driven, lightweight installer that includes useful packages like Conda and Python with minimal overhead. By default, Miniforge uses the conda-forge channel for package installations.

### Step 1: Download and Install Miniforge

To get started, download the 64-bit version of Miniforge for Windows 11. At the time of writing, we are using:

**Miniforge3-24.11.0-0-Windows-x86_64.exe**

You can find the latest release on the [Miniforge GitHub repository](https://github.com/conda-forge/miniforge/releases). Miniforge comes bundled with Python, so there’s no need for a separate Python installation. Once installed, open the Miniforge Prompt from the Windows Start Menu *(Miniforge Prompt)*.

### Step 2: Verify Python Version

Ensure your Python version is 3.9 or later. Check the installed version by running:

`python --version`

If your Python version is outdated, you may need to update or reinstall Miniforge.

### Step 3: Install PyTorch with CUDA Support

PyTorch can be installed in two modes: with or without CUDA. In this tutorial, we’ll install it with CUDA enabled for better performance, as CUDA accelerates computation on compatible NVIDIA GPUs.

#### Create a Conda Environment

To keep your setup organized, create a new Conda environment for PyTorch. Replace <your-installed-python-version> with the version you verified earlier:

`conda create -n pytorch-env python=<your-installed-python-version>`

`conda activate pytorch-env`

#### Check CUDA Installation

Before proceeding, confirm that CUDA is installed and check its version. On Windows 11, open Command Prompt and run:

`nvidia-smi`

This command should display information about your GPU and the installed CUDA version. If CUDA is not installed, follow NVIDIA’s [official guide](https://developer.nvidia.com/cuda-downloads).

#### Install PyTorch

With the Conda environment activated, install PyTorch and its dependencies:

`conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia`

During installation, you’ll be prompted to confirm the addition of multiple packages. After a successful installation, PyTorch will be ready to use.

### Step 4: Test Your Installation

To verify that PyTorch is working correctly, run the following in the Miniforge Prompt:

`python`

Then, in the Python interpreter, execute:

```
import torch

x = torch.rand(5,3)
print(x)
```
You should see an output similar to:

```
tensor([[0.2024, 0.3091, 0.9639],
        [0.3450, 0.1904, 0.8550],
        [0.6629, 0.4928, 0.6141],
        [0.7480, 0.6815, 0.2906],
        [0.3157, 0.1456, 0.3400]])
```

#### Verify CUDA Availability

To ensure PyTorch can utilize your GPU, check for CUDA availability:

```
import torch
torch.cuda.is_available()
```

If `True` is returned, PyTorch is ready to leverage CUDA for accelerated computations.

