---
title: "Custom qtplugin part II"
date: 2020-12-21T11:25:31.137Z
draft: false

# post thumb
image: "/images/post/qpluginloader/qpluginloader.jpg"

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

Let's learn to use QPluginLoader class to load custom plugins.
<!--more-->

## Introduction

In our [part I](/blog/qtplugin) of this tutorial we learnt how to create a qt plugin using Qt low level API to extend our application. In this tutorial, we will learn how to load/use the plugin we created using [QPluginLoader](https://doc.qt.io/qt-5/qpluginloader.html) class.

Qt docs also states that *"QPluginLoader cannot be used if your application is statically linked against Qt. In this case, you will also have to link to plugins statically. You can use QLibrary if you need to load dynamic libraries in a statically linked application."*

## Motivation

As we have used Qt's low level API to create our plugin, we have an option to use QPluginLoader class to load/use the plugin we created. Benefits? QPluginLoader provides convenient functions to access Qt plugin. Also, eliminates the use of platform specific loading e.g. to load a .dll file in windows we need to use **"[LoadLibraryA()](https://docs.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibrarya)"** and in case of Linux we use 
**"[dlopen()](https://linux.die.net/man/3/dlopen)"** and so on. Although, we can use another Qt convenient class **[QLibrary](https://doc.qt.io/qt-5/qlibrary.html)** but that would be a completely another tutorial.

## Tutorial

In this short tutorial, we will learn how to load/use a Qt plugin using QPluginLoader class.

```
// plugin_loader

#include <QObject>
#include <QPluginLoader>

#include "interfaces/Device.h"

class PluginLoader : public QObject
{
        Q_OBJECT

    public:

        explicit PluginLoader(QObject* parent = nullptr);

        Device* load(const QString& path);

    private:

        QPluginLoader* m_pluginLoader;
};

``` 
<br />

We create a **PluginLoader** class as a wrapper to load our plugins. Our implementation looks like this:

```

#include <QDebug>
#include "pluginloader.h"

PluginLoader::PluginLoader(QObject* parent) :
    QObject(parent),
    m_pluginLoader(nullptr)
{
}

Device* PluginLoader::load(const QString& path)
{
    m_pluginLoader = new QPluginLoader(path, this);

    qInfo() << "Loading plugin...";

    if(m_pluginLoader->load())
    {
        qInfo() << "Plugin loaded successfully...";

        Device* device = dynamic_cast<Device*>(m_pluginLoader->instance());
        return device;
    }

    qWarning() << "Plugin " << path << "failed to load..." << m_pluginLoader->errorString();
    return nullptr;
}

``` 
<br />

Our **load(const QString& path)** function takes in an argument as a path to a plugin (.so/.dll). To be loadable, the file's suffix must be a valid suffix for a loadable library in accordance with the platform, e.g. .so on Unix, - .dylib on macOS and iOS, and .dll on Windows. 

Qt docs also states that
*"We recommend omitting the file's suffix in the file name, since QPluginLoader will automatically look for the file with the appropriate suffix."*

Before loading, we check to see if **m_pluginLoader** is already loaded. If not, we try to load the plugin using **load()** and the get the instance of the plugin. In our case: 

```
Device* device = dynamic_cast<Device*>(m_pluginLoader->instance());
```
<br />

would evaluate to look something like this (check [part I](/blog/qtplugin) for PluginA):

```
Device* device = new PluginA();
```

<br />

On successful return of an instance, we can call the functions available in the plugin on the fly. 

**Note: If the plugin has additional dependencies on other third party libraries, *errorString()* might throw an error as *“Cannot load library: The specified module could not be found”* unless the plugin is in the same folder as in .exe.**
 
## Conclusion

This sample project can be found on my [GitHub](https://github.com/SurKM9/PluginLoaderApp) page.

Feel free to share this blog, if you feel it helped you. If you have any comments or suggestions, post it in the comments section below.

<span>Photo by <a href="https://unsplash.com/@markusspiske?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Markus Spiske</a> on <a href="https://unsplash.com/s/photos/loader?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>