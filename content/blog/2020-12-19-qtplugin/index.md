---
title: "Custom qtplugin part I"
date: 2020-12-19T10:45:31.137Z
draft: false

# post thumb
image: "//codeflamingo.s3.eu-central-1.amazonaws.com/images/plugin.jpg"

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

Let's learn how to create a custom qt plugin.
<!--more-->

## Introduction

Plugins are software components that adds a specific feature to an existing Qt application. This enables customization without actually disturbing the core structure of the application. In otherwords, these can be called as add-in, add-ons etc.

An existing Qt application functionality can be greatly extended without having to build the functionality into the application but load the plugin at run time whenever needed. Qt provides a powerful low level API to extend current Qt applications using plugins. 

This would be a 2 part tutorial about how to create plugins using QtPlugin and how do we load/use QPluginLoader to load the plugins.

## Motivation

Lets have a look at an instance, where, we have different cameras which depend on various libraries like OpenCV, Boost or any proprietary libraries. We do not want to build/compile our main application with so many dependencies. Building a camera device along with its dependencies as a plugin would enable us to keep our main application free of all unnecessary dependencies.

## Tutorial

In this short tutorial, we will learn how to create a Qt plugin interface and implement the interface to create a plugin.

```
// plugin_interface

#include <QString>
#include <QStringList>
#include <QtPlugin>

class Device
{
    public:

        virtual ~Device() = default;
        virtual void start() = 0;
        virtual void stop() = 0;
};

// declare an interface to use
#define iInterface_IID "com.company.Device/1.0"
Q_DECLARE_INTERFACE(Device, iInterface_IID)

``` 
<br />

Notice the declaration at the bottom. **Q_DECLARE _INTERFACE** needs to be declared using the unique **iInterface_IID** and also **QtPlugin** include.
This allows Qt to assign this as an interface class with an unique ID.

Now, we have an interface that needs to be implemented to create necessary plugins. This is how we implement plugins using the above interface:

```
// pluginA class implemented using Device class
#include <QObject>
#include "Device.h"

class PluginA : public QObject, public Device
{
        Q_OBJECT
        
        // QtPlugin macros needs to be defined
        Q_PLUGIN_METADATA(IID "com.company.PluginA")
        Q_INTERFACES(Device)

    public:

        explicit PluginA(QObject* parent = nullptr);

        // Device interface
        virtual void start() override;
        virtual void stop() override;
};

``` 
<br />

In order to be considered as [QtPlugin](https://doc.qt.io/qt-5/qtplugin.html), we need to define macros **Q_PLUGIN _METADATA** and **Q_INTERFACES**. [Q_PLUGIN _METADATA](https://doc.qt.io/qt-5/qtplugin.html#Q_PLUGIN_METADATA) macro also takes in an optional parameter as json file with plugin metadata which looks something like this:

```
{
    "id" :            "com.company.PluginA",
    "name" :          "pluginA",
    "apiversion" :    "1.0",
    "version" :       "1.0.0",
    "author" :        "user"
}

```
<br />

As per Qt docs *"The json file must reside in one of the include directories specified by the build-system. moc exits with an error when it could not find the specified file"*. To keep it simple for this tutorial we are not using metadata. 

Building this plugin app will create pluginA.[dll/.so] file which we can later use in our main Qt application. In the second part of this tutorial we will see how to load/use this plugin using QPluginLoader class.

## Conclusion

This sample project can be found on my [GitHub](https://github.com/SurKM9/PluginLoaderApp) page.

Feel free to share this blog, if you feel it helped you. If you have any comments or suggestions, post it in the comments section below.

<span>Photo by <a href="https://unsplash.com/@thomasjsn?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Thomas Jensen</a> on <a href="https://unsplash.com/s/photos/plugin?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>