---
title: "Set application icon using CMake on Windows"
date: 2021-06-25T23:00:00.226Z
draft: false

# post thumb
image: "//codeflaming-bucket.s3.eu-central-1.amazonaws.com/cmake-app-logo.jpg"

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
type: "featured"
---

Set application icon using CMake on Windows
<!--more-->

## Introduction

In the previous [tutorial](icon-qtapplication) we managed to simply set the application icon using QMake. In this tutorial, we will learn how to set the icon of an application using CMake scripts.

## Setup and Configuration

Before we can start writing CMake scripts we need to create a resource(.rc file). To create a .rc file, right-click in your current source directory where the CMakeLists.txt exists and choose a new document. Rename the new document to "appicon.rc". Open the .rc file in an editor and paste this line in it:

```
IDI_ICON1 ICON DISCARDABLE "appicon.ico"
```

Make sure **appicon.ico** exists in the current source directory as well. If you do not have a .ico file. You can create one [here](https://www.icoconverter.com/).

Now, we just need to add this .rc file in our CMake script like:

```
set(APP_ICON_RESOURCE_WINDOWS "${CMAKE_CURRENT_SOURCE_DIR}/appicon.rc")

add_executable(${PROJECT_NAME}
        WIN32
        main.cpp
        ${APP_ICON_RESOURCE_WINDOWS}
    )
```

When you build and run the application, you will see the icon on the top-left corner of the window, and also the icon is set on the executable(.exe) itself.

## Conclusion

If this was helpful, please share this blog, and also feel free to add your thoughts or comments below.

Photo by <a href="https://unsplash.com/@aquatium?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Harpal Singh</a> on <a href="https://unsplash.com/s/photos/icons?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
