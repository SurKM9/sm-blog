---
title: "Set icon on Qt application"
date: 2021-05-13T10:00:44.226Z
draft: false

# post thumb
image: "/images/post/icon-on-application/app-icon-logo.jpg"

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

Set icon on Qt application window and on executable
<!--more-->

## Introduction

Sometimes, simple tasks like setting an icon for application or executable can be very confusing and complicated. In this tutorial, we will see how easy it is to set an icon for Qt applications.

## What do we need?

A .ico file in the source directory. Icon can be any image of choice but it must be a .ico file for this to work.

## Setup

Setup is very simple. The .ico file must in the source directory and one single line inside .pro file of the project:

**RC\_ICONS = my\_icon.ico**

After this `run qmake, build the project, and run`. Now, the icon is set on the top left corner of the Qt application and also on our executable file.

## Conclusion

If this was helpful, please share this blog and also feel free to add your thoughts or comments below.

Photo by <a href="https://unsplash.com/@aquatium?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Harpal Singh</a> on <a href="https://unsplash.com/s/photos/icons?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
