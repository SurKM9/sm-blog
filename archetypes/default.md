---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
description: "" 
summary: ""     
featureAsset: "background.png" # Default flamingo background
tags: []
categories: []
# We don't need to add showDate or showReadingTime here 
# because your Global Config (params.toml) already handles them!
---