---
title: "Samba authentication in Qt app using Windows API"
date: 2021-06-27T12:00:00.226Z
draft: false

# post thumb
image: "//codeflaming-bucket.s3.eu-central-1.amazonaws.com/samba-logo.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
  - Tech
  - Programming
tags:
  - cplusplus
  - cmake

# post type
type: "post"
---

Authenticate samba server using Windows API
<!--more-->

## Introduction

Samba is an open-source service that runs on Linux/Unix based platforms while having the capability to communicate with Windows OS clients. Samba server offers services like:

 * Sharing of directories
 * Sharing printers
 * Windows clients authentication
 * Name-server resolution and so on

</br>

In this tutorial, we will discuss about how to implement communication between Qt application and samba server using authentication. We do not go into the depth of setting up or configuring samba servers as it will be beyond the scope of our discussion.

## Problem

A samba server without authentication is open to communicate with as many clients as possible if set up correctly. But communicating with a samba server with authentication can be challenging. Qt doesn't have native support to mount network resources and deal with file protocols. So, we will use Windows APIs to get around the authentication issue. Of course, this would violate Qt's cross-platform ability but this would be useful for anyone developing applications only for Windows platforms.

## Setup and Configuration

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

 ```
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
