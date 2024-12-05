---
title: "Resizing QLabel while maintaining the aspect ratio"
date: 2021-01-31
draft: false

# post thumb
image: "/images/post/aspectratio-qpixmap/eye.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
    - tech
    - programming
tags:
    - cplusplus 
    - qt

# post type
type: "post"
---

Let's talk about aspect ratio handling in QLabel.

<!--more-->
## Introduction

Displaying a big image on a `QLabel` is not always straight forward. For instance, we have an image of size 1920 x 1080 pixels, the label size may or may not be sufficient to show the whole image in the size of `QLabel` itself.

In this tutorial, we will address 2 issues:

- How to keep aspect ratio of the image while resizing a `QLabel`?
- How to make `QLabel` follow the aspect ratio of the image it is showing?

## Formula

This is where, aspect ratio comes into the picture. Aspect ratio helps us to keep the entire image inside the size we have available with us.

To preserve aspect ratio, we need to calculate new dimensions for the original height and width of the image.
Lets we have an image of 1920 x 1080 pixels and our width of our `QLabel` is only 400 pixels. New height of our image, preserving the aspect ratio would be:

```
(original height of the image) / (original width of the image) x width of QLabel

(1080 / 1920) x 400 = 225
```

Usually, i use this awesome and simple aspect ratio [calculator](https://eikhart.com/blog/aspect-ratio-calculator).

## Tutorial

For this tutorial, we will create a `QLabel` and load a `QPixmap` on `QPushButton` clicked. We will use `QDialog` as the container and QtDesigner to setup the UI. This is how our simple UI looks like:

![layout](/images/post/aspectratio-qpixmap/layout.png)

We have a button `Swap` and a `QLabel`. I have added a stylesheet to our `QLabel` to make it more obvious. Otherwise, a `QLabel` without its default text is plain transparent. We will load a `QPixmap` whenever the button `Swap` is clicked.

Lets dig into code.

Our **main.cpp** doesn't look any special. Plain file created by QtCreator for us.

```

#include "Dialog.h"
#include <QApplication>

int main(int argc, char* argv[])
{
    QApplication a(argc, argv);
    Dialog w;
    w.show();
    return a.exec();
}

```

To achieve our objective, we need to subclass `QLabel` and we call it **PixmapLabel**.

Lets see our **PixmapLabel.h**

```
#ifndef PIXMAPLABEL_H
#define PIXMAPLABEL_H

#include <QLabel>
#include <QPixmap>


class PixmapLabel : public QLabel
{
    public:

        PixmapLabel(QWidget* parent = nullptr);
        virtual QSize sizeHint() const override;

        void setImage(const QPixmap& image);
        int heightForWidth(int width) const override;

    protected:

        void paintEvent(QPaintEvent* event) override;

    private:

        QPixmap m_pixmap;
        int m_cols;
        int m_rows;
};
#endif // PIXMAPLABEL_H

```

Here we are going to re-implement 3 functions `sizeHint()`, `heightForWidth()` and `paintEvent()`.

Here is the implementation file **PixmapLabel.cpp**:

```

#include "PixmapLabel.h"
#include <QPainter>
#include <QPaintEvent>



PixmapLabel::PixmapLabel(QWidget* parent) :
    QLabel(parent),
    m_cols(0),
    m_rows(0)
{
    QSizePolicy sizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    sizePolicy.setHeightForWidth(true);
    setSizePolicy(sizePolicy);

    setMinimumSize(sizeHint());

    // set borders on the QLabel
    setStyleSheet("QLabel{border: 1px solid black; background: gray;}");
}



void PixmapLabel::setImage(const QPixmap& image)
{
    m_pixmap = image;

    m_cols = m_pixmap.width();
    m_rows = m_pixmap.height();

    update();
}



/* virtual */ QSize PixmapLabel::sizeHint() const
{
    if (m_cols != 0)
    {
        int width = this->width();
        return QSize(width, heightForWidth(width));
    }
    else
    {
        return QSize(200, 200);
    }
}



/* virtual */ int PixmapLabel::heightForWidth(int width) const
{
    return (m_cols != 0) ? width * m_rows / m_cols : this->height();
}



/* virtual */ void PixmapLabel::paintEvent(QPaintEvent* event)
{
    QLabel::paintEvent(event);

    // if there is no pixmap loaded yet
    if(m_pixmap.isNull())
    {
        return;
    }

    // Create painter
    QPainter painter(this);

    // Get current pixmap size
    QSize pixmapSize = m_pixmap.size();

    // Scale size to painted rect
    pixmapSize.scale(event->rect().size(), Qt::KeepAspectRatio);

    // Scale the pixmap
    QPixmap pixmapScaled = m_pixmap.scaled(pixmapSize, Qt::KeepAspectRatio, Qt::SmoothTransformation);

    // Draw the pixmap
    painter.drawPixmap(QPoint(), pixmapScaled);
}

```

Notice we are not using `setPixmap()` available in `QLabel` class but rather we are using `paintEvent()`. This allows us to resize `QLabel` and also scale its contents.

`paintEvent()` is automatically called whenever `QLabel` is resized or Qt feels like it needs to repaint the contents of the `QLabel` as in our case a `QPixmap`. This solves our first issue as to how do we keep the aspect ratio while resizing and we do it without the need to explicitly implementing `resizeEvent()`.

To fix our second issue, we need to manage the `width()` and `height()` of the `QLabel` explicitly in the container of our label i.e. `QDialog`.

Lets have a look at our **Dialog.h**

```
#ifndef DIALOG_H
#define DIALOG_H

#include <QDialog>

QT_BEGIN_NAMESPACE
namespace Ui
{
    class Dialog;
}
QT_END_NAMESPACE

class Dialog : public QDialog
{
        Q_OBJECT

    public:

        Dialog(QWidget* parent = nullptr);
        ~Dialog();

    private slots:

        void on_pushButton_clicked();

    protected:

        virtual void resizeEvent(QResizeEvent* event) override;

    private:

        Ui::Dialog* ui;
        bool m_swap;
        QImage m_image1;
        QImage m_image2;
};
#endif // DIALOG_H

```

Here is our implementation **Dialog.cpp**

```
#include "Dialog.h"
#include "ui_Dialog.h"

Dialog::Dialog(QWidget* parent)
    : QDialog(parent)
    , ui(new Ui::Dialog)
    , m_swap(true)
{
    ui->setupUi(this);
    m_image1 = QImage(":/images/images/1.png");
    m_image2 = QImage(":/images/images/2.jpg");
}



Dialog::~Dialog()
{
    delete ui;
}



void Dialog::on_pushButton_clicked()
{
    if(m_swap)
    {
        ui->label->setImage(QPixmap::fromImage(m_image1));

        m_swap = false;
    }
    else
    {
        ui->label->setImage(QPixmap::fromImage(m_image2));

        m_swap = true;
    }

    // force QLabel to follow fixed dimensions
    // based on the loaded QPixmap aspect ratio
    int w = ui->label->width();
    int h = ui->label->heightForWidth(w);

    ui->label->setFixedHeight(h);
}



void Dialog::resizeEvent(QResizeEvent* event)
{
    Q_UNUSED(event);

    // force QLabel to follow fixed dimensions
    // based on the loaded QPixmap aspect ratio
    int w = ui->label->width();
    int h = ui->label->heightForWidth(w);

    ui->label->setFixedHeight(h);
}

```

We force the `QLabel` to follow fixed dimensions.

Here we have used it on 2 occasions, first when we set an image and second is in `resizeEvent()` of our `QDialog`. Whenever our `QDialog` is resized we resize our `QLabel` based on the formula we derived above. This not only allows us to preserve the aspect ratio of the image but also forces the `QLabel` to follow along.

This whole project can be found on my [GitHub](https://github.com/SurKM9/AspectRatioPixmap) account.

## Conclusion

Feel free to share this blog, if you feel it helped you. If you have any comments or suggestions, post it in the comments section below.

<span>Photo by <a href="https://unsplash.com/@kuzelevdaniil?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Daniil Kuželev</a> on <a href="https://unsplash.com/s/photos/eye?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>
