---
title: "Systemtray icon with custom context menu on any modern OS"
date: 2021-09-21T12:26:00.226Z
draft: false

# post thumb
image: "//codeflaming-bucket.s3.eu-central-1.amazonaws.com/systray-logo.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
  - Tech
  - Programming
tags:
  - cplusplus
  - qt

# post type
type: "post"
---

Set custom system tray icon with custom context menu for your application
<!--more-->

## Introduction

Modern operating systems usually provide a special area on the desktop, called the *system tray* or *notification area*, where long-running applications can display icons and short messages. These icons can also be customized to show short context menus for additional functionality.

Qt framework has native support to add tray icons using the class *QSystemTray*. In this tutorial, we will see how can we implement system tray icon with custom context menu for our application with just couple of lines of code.

## Code

Before we use the *QSystemTray* class we need to make sure we have a *.ico* file which we need to set as an icon for our application. A *.ico* file is nothing but an icon file. You can convert your *.png or .jpg* image into *.ico* file using online converters like [this](https://icoconvert.com/). Once we have the *.ico* file ready, we can either add it to our *resource(.rc)* file of our application if available.

With a couple of lines of code as shown below, we can create a tray icon with a custom menu for our application ready.

```

    // create system tray icon
    // assuming you have added .ico file to your resource .rc file
    // otherwise, provide a relative path to it
    QSystemTrayIcon* trayIcon = new QSystemTrayIcon(QIcon(":/path/to/your/.ico file"), this);

    // add tray icon menu actions
    QMenu* trayMenu = new QMenu(this);
    trayMenu->addAction("Show");
    trayMenu->addAction("Exit");

    // set menu on the system tray icon
    trayIcon->setContextMenu(trayMenu);

    // show tray icon
    m_systemTrayIcon->show();

```
## Conclusion

The above piece of code will create a tray icon and when you right-click on it you would have your custom context menu displayed for you. If this was helpful, please share this blog, and also feel free to add your thoughts or comments below.

Photo by <a href="https://unsplash.com/@ben1?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Ben Schnell</a> on <a href="https://unsplash.com/s/photos/tray?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
