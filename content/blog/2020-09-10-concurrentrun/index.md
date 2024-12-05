---
title: "Run a function in separate thread using QtConcurrent"
date: 2020-09-11T9:35:31.137Z
draft: false

# post thumb
image: "/images/post/concurrentrun/concurrentrun-thumbnail.jpg"

# meta description
description: "this is meta description"

# taxonomies
categories:
  - "Tech"
  - "Programming"
tags:
  - "cplusplus"
  - "qt"

# post type
type: "featured"
---

Parallel programming using QtConcurrent.

<!--more-->
## Introduction

With computers getting more powerful, data computation is getting expensive. Many a times we need to perform heavy computations using multi threading to distribute this computing load. In C++ we use `std::thread` or `std::async` to achieve multi threading. In Qt5 we have `QThread` or `QtConcurrent` to achieve the same.

According to [QtConcurrent](https://doc.qt.io/qt-5/qtconcurrent-index.html) docs:

_The QtConcurrent namespace provides high-level APIs that make it possible to write multi-threaded programs without using low-level threading primitives such as mutexes, read-write locks, wait conditions, or semaphores._

In simpler words, `QtConcurrent` provides functionality to spawn threads without explicit interaction from the user. In addition to this, we also have possibility to use `signals` and `slots` across the threads.

In this tutorial we will see how to run a function asynchronously using `QtConcurrent` and also use `signals` and `slots` to update GUI from the thread created by `QtConcurrent`.

## Motivation

While performing computationally expensive tasks, GUI becomes unresponsive or laggy because of the reason that the GUI/Main thread is blocked by a heavy task but at the same time cannot keep the GUI responsive.

We need multi threading to keep our GUI responsive while performing computationally expensive tasks.

## Tutorial

Here we make a small application with `Start` and `Stop` buttons. `Start` button spawns a new thread and `Stop` button kills the thread.

In the layout we have a `QLCDNumber` and `QProgressBar` as a reference to see how the GUI is updated.

Lets have look at our **Dialog.cpp**:

``` 
#include <QtConcurrent/QtConcurrent>
#include <QFuture>

#include "dialog.h"
#include "ui_dialog.h"

Dialog::Dialog(QWidget* parent)
    : QDialog(parent)
    , ui(new Ui::Dialog)
{
    ui->setupUi(this);

    m_worker = new Worker(this);

    // connections
    connect(m_worker, &Worker::updateGUI, this, &Dialog::onUpdateGUI);
    connect(this, &Dialog::stop, m_worker, &Worker::stop);
    connect(ui->pushButton, &QPushButton::clicked, this, &Dialog::onStartClicked);
    connect(ui->pushButton_2, &QPushButton::clicked, this, &Dialog::onStopClicked);
}

Dialog::~Dialog()
{
    // stop the thread before closing the application
    // otherwise, the window will be destroyed but
    // the thread will continue running
    emit stop();
    delete ui;
}

void Dialog::onStartClicked()
{
    // prints current thread id
    // here it is the main thread
    qDebug() << "Main thread: " << this->thread()->currentThreadId();

    // create an concurrent thread
    QFuture<void> future = QtConcurrent::run(m_worker, &Worker::asyncFunction);

    ui->pushButton->setEnabled(false);
}

void Dialog::onStopClicked()
{
    emit stop();
    ui->pushButton->setEnabled(true);
}

void Dialog::onUpdateGUI(int value)
{
    // update lcd number and progress bar
    ui->lcdNumber->display(value);
    ui->progressBar->setValue(value);
}

```

We declare 3 slots `OnStartClicked()`, `OnStopClicked()`, `OnUpdateGUI()` and 1 signal `stop()`.

We have a `Worker` class which has a function `asyncFunction()` and this function in our tutorial will run on a different thread.

Implementation looks like this:

```
#include <QThread>
#include "worker.h"

Worker::Worker(QObject* parent) :
    QObject(parent)
    , m_stop(false)
{
}

void Worker::stop()
{
    m_stop = true;
}

void Worker::asyncFunction()
{
    // prints worker thread id
    qDebug() << "Worker thread: " << this->thread()->currentThreadId();

    m_stop = false;

    for(int i = 0; i <= 100; i++)
    {
        // if stop requested
        // break this loop
        if(m_stop)
        {
            return;
        }

        // signal dialog class to update GUI
        emit updateGUI(i);

        // thread sleep for 50 ms
        // otherwise this is too fast
        this->thread()->msleep(50);
    }
}
```

## Explanation

To make this work, we need proper connections like the ones we have defined in **Dialog.cpp**.

```
connect(m_worker, &Worker::updateGUI, this, &Dialog::onUpdateGUI);
connect(this, &Dialog::stop, m_worker, &Worker::stop);
```

First connection ensures that every time the worker class emits a signal `updateGUI`, the slot on `onUpdateGUI` is called in `Dialog` class.

By default, a connect statement in Qt looks something like this:

```
QObject::connect(const QObject *sender, const char *signal, const char *method, Qt::ConnectionType type = Qt::AutoConnection)
```

The last parameter `Qt::AutoConnection` is the key here. Qt automatically decides to use `Qt::QueuedConnection` while connecting `signals` and `slots` across the threads. We can also specify explicitly to use `Qt::QueuedConnection` inside our connect statements.

Our second connect statement is for stopping the thread. Notice we should always use signals and slots when working with multi threading since Qt handles most of the complications associated with it automatically.

Point of interest here is `QtConcurrent::run()`. It spawns a thread every time `Start` button is clicked and our function `asyncFunction()` runs asynchronously on a different thread.

To test it, we print the thread id:

```
Main thread:  0x4d48
Worker thread:  0x39cc

```

## Conclusion

Running complex and heavy tasks on different threads not only distributes the load and makes the program run faster but also keeps GUI/Main thread free, which helps in keeping our UI responsive.

Here is our demo project output in action:

![concurrentrun](/images/post/concurrentrun/concurrentrun.gif)

The whole project can be found on my [GitHub](https://github.com/SurKM9/ConcurrentRun) account. If this was helpful, please share this blog and also feel free to add your thoughts or comments below.

<span>Photo by <a href="https://unsplash.com/@drmakete?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">drmakete lab</a> on <a href="https://unsplash.com/s/photos/programming-thread?utm_source=unsplash&amp;utm_medium=referral&amp;utm_content=creditCopyText">Unsplash</a></span>
