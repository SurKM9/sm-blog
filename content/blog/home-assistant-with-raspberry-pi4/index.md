---
title: "Intro to Home Assistant with Raspberry Pi 4"
date: 2024-12-08T11:47:00.226Z
draft: true

# post thumb
image: "/images/post/home-assistant-with-raspberry-pi4/logo.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
  - Tech
tags:
  - raspberrypi
  - homeautomation

# post type
type: "post"
---

Installation of Home Assistant on Raspberry Pi 4
<!--more-->

## Introduction

[Home Assistant](https://www.home-assistant.io/) is an open-source home automation service that enables local control with security. It is managed and maintained by worldwide developers community. Since the launch home assistant has come a long way with support for more than 2900+ integrations available at the time of writing. It has a robust documentation and community support which makes it an ideal home automation choice for those who would like to move away from cloud based automation or the hobbyists who would like to play around with the advanced controls home assistant provides.

</br>

In this tutorial, we will discuss about how to install home assistant OS on Raspberry Pi 4 and what are the challenges in installation.

## Pre-requisites

* Raspberry Pi 4 Model B
* Good Micro SD card (at least 32 GB)
* SD card reader (for flashing the SD card with home assistant OS)
* Good internet connection (preferrably access to LAN connection for Raspberry Pi 4)
* PC/Laptop for writing/flashing SD card

</br>

## Challenges

Here I would like to mention the mistakes I made:

**Cheap 10€ micro SD card:**

In order to save some money (because it was a hobby project for me) I picked up a cheap micro SD card from the store. You guessed it right. While trying to write/flash the micro SD card, for some reason I managed to corrupt it. Rendering it useless. 
Even though micro SD is not recommended (SSD is preferred) I would suggest a good micro SD card from a reputed brand.

**Faulty SD card readers:**

Please make sure to use a good SD card reader for writing/flashing the cards. After the cheap SD card disaster, I realized I must check my SD card readers for their functionality. Guess what, my SD card reader was also faulty. I managed to buy a new one before I tried to flash my new SanDisk SD card. 

**Word of Caution:**

If you are planning to use your old SD card lying around somewhere in your drawers, flashing will **OVERWRITE/WIPE YOUR DATA** on the card. Make sure you have your data backed up.

## Setup and Installation

We will need the WNetAddConnection2A function from the Windows API to make the connection to a network resource as in our case samba server.

We need to set up 3 key components to achieving a successful connection:

 * Setup network resource
 * Samba server username
 * Samba server password

</br>

Network resource or *NETRESOURCE* needs attributes to be setup like:

 * local name - *Q:*
 * remote name - *////samba\_ip\_address//path//to//destination* (extra / are for escape characters in the path)
 * resource type - to any

</br>

You can read more about *NETRESOURCE* [here](https://docs.microsoft.com/en-us/windows/win32/api/winnetwk/ns-winnetwk-netresourcea).

After setting up our *NETRESOURCE* we need to call *WNetAddConnection2A* function to establish a connection to the samba server. *WNetAddConnection2A* takes in 4 arguments:

 * net resource - that we built above
 * password - samba password
 * username - samba username
 * type of connection you would like

</br>

*WNetAddConnection2A* returns with an error code which can be handled as you wish. Below is a sample function showing the creation of *NETRESOURCE* and add a new connection using *WNetAddConnection2A*.

 ```c++
#include <windows.h>
#include <Winnetwk.h>
#include <system_error>
#include <iostream>

// Need to link with Netapi32.lib and Mpr.lib

bool ServerConnection::create(const QString& remoteName, const QString& username, const QString& password)
{
    DWORD dwRetVal;

    NETRESOURCE nr;
    DWORD dwFlags;

    // assign a drive name
    // avoid using commonly used names like C:, D:
    LPSTR szLocalName = "Q:";

    LPSTR szRemoteName = new TCHAR[remoteName.toStdString().size() + 1]; //define
    std::strcpy(szRemoteName, remoteName.toStdString().c_str());

    // Zero out the NETRESOURCE struct
    memset(&nr, 0, sizeof (NETRESOURCE));

    // Assign our values to the NETRESOURCE structure.
    nr.dwType = RESOURCETYPE_ANY;
    nr.lpLocalName = szLocalName;
    nr.lpRemoteName = szRemoteName;
    nr.lpProvider = NULL;

    // Assign a value to the connection options
    // this flag makes sure windows doesn't remember previous connections
    dwFlags = CONNECT_TEMPORARY;

    // Call the WNetAddConnection2 function to assign
    // a drive letter to the share.
    dwRetVal = WNetAddConnection2A(&nr, password.toStdString().c_str(), username.toStdString().c_str(), dwFlags);

    // get the message string
    std::string message = std::system_category().message(dwRetVal);

    std::cout << message << std::endl;

    // handle error statements
    switch (dwRetVal)
    {
        case NO_ERROR:
        case ERROR_ALREADY_ASSIGNED:
        case ERROR_DEVICE_ALREADY_REMEMBERED:
            return true;
        default:
            return false;
    }
}
```

This implementation to communicate with samba server using Windows API has dependencies too. To make this work you will need to link your application to 2 different libraries:

 * Mpr.lib
 * NetAPI32.lib

</br>

These libs are usually found inside *C:\Program Files(x86)\Windows Kits\10\*

## Conclusion

To be able to communicate with the samba server beyond the authentication wall as a window client can be tricky. Using Windows API we learned how to mount the samba server locally as a network resource using *WNetAddConnection2A* function.

If this was helpful, please share this blog, and also feel free to add your thoughts or comments below.

Photo by <a href="https://unsplash.com/@flyd2069?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">FLY:D</a> on <a href="https://unsplash.com/s/photos/computer-security-lock?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
