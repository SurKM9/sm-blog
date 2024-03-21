---
title: "Loading custom qtplugin with dependencies on windows"
date: 2020-12-25T18:45:31.137Z
draft: false

# post thumb
image: "//codeflaming-bucket.s3.eu-central-1.amazonaws.com/error.jpg"

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

Solution to cannot load library error.
<!--more-->

## Introduction

In [QPluginLoader](/qpluginloader) tutorial we learnt how to load plugins using Qt. This only works when the plugin has no dependencies to other third party plugins like OpenCV, Boost and proprietary plugins. Although, loading plugins which has other third party dependencies is not straight forward.

## The Problem

I personally encountered a problem where i built a custom plugin like we did in [part I](/qtplugin) tutorial but with additional dependencies to OpenCV, Boost and some other proprietary libraries. Problem?

- Plugins (.so/.dll) and its dependencies were located in their respective folders 

  - the path to the plugins looks something like this: /path/to/exe-folder/plugins/plugins[.so/.dll]                                                         

- The plugin won't load error - *"QPluginloader error: “Cannot load library: The specified module could not be found”*

Notice, none of the plugins or its dependencies are located inside the exe directory. Important!

At first, i thought this is some kind of error in the path we are passing to QPluginLoader constructor. No! It goes deeper.

Turns out, windows has a predefined [Dynamic-Link Library Search Order](https://docs.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order).
When loading a plugin using QPluginLoader **load()** as described in [part II](/qpluginloader), by default, windows searches for plugin dependencies in the exe directory but cannot find the necessary dlls to load the plugin, hence the error.

## Solution

 Simplest workaround for this would be to put plugin and all its dependencies in the exe folder of the application where windows can find the necessary dlls to load. 
 
 This is not the case when we have lots of plugins and its dependencies. We do not want all the dlls inside exe directory. 

 Other workaround would be to actually handle it through the code itself. We need to somehow inform windows to search inside our *plugins* directory for dependencies. 

 With reference to our [part II](/qpluginloader) tutorial, our new code looks like this:

 ```

#include <QDebug>
#include <QtGlobal>
#include "pluginloader.h"

#define Q_OS_WIN
#include <windows.h>
#include <winbase.h>
#endif

PluginLoader::PluginLoader(QObject* parent) :
    QObject(parent),
    m_pluginLoader(nullptr)
{
}

Device* PluginLoader::load(const QString& path)
{
    m_pluginLoader = new QPluginLoader(path, this);

    qInfo() << "Loading plugin...";

#define Q_OS_WIN
    // set the directory to "plugins" folder
    // windows will search for dlls in this folder
    SetDllDirectoryA((LPCSTR) "/path/to/exe-folder/plugins");
#endif

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
</br>

[SetDllDirectoryA()](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setdlldirectorya) adds plugin directory path to windows search order.

## Conclusion

This sample project can be found on my [GitHub](https://github.com/SurKM9/PluginLoaderApp) page.

Feel free to share this blog, if you feel it helped you. If you have any comments or suggestions, post it in the comments section below.

<span>Photo by <a href="https://unsplash.com/@jackson_893?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Michael Geiger</a> on <a href="https://unsplash.com/s/photos/computer-error?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>