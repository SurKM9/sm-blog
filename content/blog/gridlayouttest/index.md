---
title: "Add or remove widgets in QGridLayout"
date: 2021-01-09T19:00:44.226Z
draft: false

# post thumb
image: "/images/post/gridlayouttest/grid.jpg"

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
Imagine we want to add multiple widgets in QGridLayout dynamically but also remove widgets on the fly.
<!--more-->

## Introduction

Imagine we want to add multiple widgets in `QGridLayout` dynamically but also remove widgets on the fly. Adding widgets to grid layout is pretty straight forward but removing widgets is the tricky part. In this tutorial we will see how to achieve the same.

## Goal

Our goal would be to design a simple UI with buttons which enable us to achieve adding and removing widgets on a grid layout dynamically. Our application would ultimately look like this:

![window](/images/post/gridlayouttest/window.gif)

## Adding widgets to layout

Adding widgets to `QGridLayout` is very easy using the `addWidget()` which can be used further to specify row or column spans also. In our example, we add 4 `QLabel`s to the layout when button `Add` is clicked.

```c++
void MainWindow::on_pushButton_clicked()
{
    // check if the grid layout is empty
    if(ui->gridLayout->count() == 0)
    {
        QLabel* label1 = new QLabel(this);
        QLabel* label2 = new QLabel(this);
        QLabel* label3 = new QLabel(this);
        QLabel* label4 = new QLabel(this);

        // set borders to labels for better visibility
        label1->setStyleSheet("border: 3px solid black;");
        label2->setStyleSheet("border: 3px solid black;");
        label3->setStyleSheet("border: 3px solid black;");
        label4->setStyleSheet("border: 3px solid black;");

        // add widget at (0,0) position inside the layout
        ui->gridLayout->addWidget(label1, 0,0);
        // add widget at (0,1) position inside the layout
        ui->gridLayout->addWidget(label2, 0,1);
        // add widget at (1,0) position inside the layout
        ui->gridLayout->addWidget(label3, 1,0);
        // add widget at (1,1) position inside the layout
        ui->gridLayout->addWidget(label4, 1,1);
    }
}

```

## Removing widgets from layout

Removing widgets from grid layout can be little tricky. In our tutorial, we perform removing widgets using button `Remove`. We use convenient function `removeWidget()` from Qt for the purpose. First, we get the item at index 0 in the grid using `itemAt(0)` then after we can remove it from the layout using `removeItem()`. Keep in mind this will only remove the item from the layout but it is the callers responsibility to delete in explicitly. To delete the widget itself, we need to call `widget()` on `QLayoutItem` returned by `itemAt(0)`. As it might be possible the widget at index 0 can be a nullptr, we add a check to see if its a valid widget and go on to delete the widget.

```c++
void MainWindow::on_pushButton_2_clicked()
{
    // get the item in the layout at index 0
    QLayoutItem* item = ui->gridLayout->itemAt(0);
    ui->gridLayout->removeItem(item);

    // get the widget
    QWidget* widget = item->widget();

    // check if a valid widget
    if(widget)
    {
        delete widget;
    }
}
```

## Conclusion

Adding and removing widgets from grid layout can be helpful specially when one wants to control the visibility of certain widgets inside the layout or moving widgets between layouts dynamically.

The whole project can be found on my [GitHub](https://github.com/SurKM9/GridLayoutTest) page. If this was helpful, please share this blog and also feel free to add your thoughts or comments below.


<span>Photo by <a href="https://unsplash.com/@lanceanderson?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Lance Anderson</a> on <a href="https://unsplash.com/s/photos/grid?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>
