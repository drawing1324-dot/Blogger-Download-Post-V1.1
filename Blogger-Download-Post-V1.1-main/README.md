ต่อครับ

เข้าสู่ **Milestone 13 : User Manual / Documentation**

รอบนี้เป็น **การสร้างไฟล์ใหม่**

เป้าหมาย:

สร้างคู่มือใช้งานระบบ เพื่อให้คุณสามารถ:

* เพิ่ม Blog เอง
* ลด/เพิ่มจำนวนโพสต์
* เปลี่ยนภาษา
* เปลี่ยนแนว AI
* เพิ่ม Account
* แก้ปัญหาเบื้องต้น

โดยไม่ต้องกลับมาแก้ Code

---

# [สร้างไฟล์]

**Version : V1.1**

**Milestone : 13**

ไฟล์:

```text
README.md
```

---

```markdown
# Blogger Download Auto Post V1.1

ระบบอัตโนมัติสำหรับสร้างและโพสต์บทความดาวน์โหลดไฟล์

รองรับ:

- 3D CAD Files
- Vector Graphics
- Drawing Files
- Engineering Resources
- Software / Knowledge Blog


---

# 1. แนวคิดระบบ


ระบบทำงานแบบ:


```

GitHub Actions

↓

Python Engine

↓

AI Topic Generator

↓

Queue System

↓

AI Article Writer

↓

Search Source

↓

Image Provider

↓

Blogger API

↓

Published Post

```


---

# 2. โครงสร้างโปรเจกต์


```

project/

│

├── main.py

├── test_system.py

├── requirements.txt

├── config/

│
├── blogs.json

├── settings.json

├── profiles.json

├── prompts.json

└── sources.json

├── modules/

│
├── ai/

├── blogger/

├── core/

├── image/

└── search/

├── storage/

│
├── queue/

├── backup/

├── logs/

└── posted/

└── .github/

```
└── workflows/

    └── auto-post.yml
```

```


---

# 3. การเพิ่ม Blog ใหม่


แก้ไฟล์:


```

config/blogs.json

````


ตัวอย่าง:


```json
{
"name":"New Blog",

"blog_id":"BLOG_ID",

"language":"en",

"type":"vector",

"enabled":true
}
````

ไม่ต้องแก้ Python

---

# 4. การเปิด / ปิด Blog

ปิด:

```json
"enabled":false
```

เปิด:

```json
"enabled":true
```

---

# 5. การเปลี่ยนจำนวนหัวข้อ

ไฟล์:

```
config/settings.json
```

ค่า:

```json
"generate_topics_amount":50
```

ตัวอย่าง:

สร้าง 100 หัวข้อ:

```json
"generate_topics_amount":100
```

---

# 6. การควบคุมจำนวนโพสต์

ไฟล์:

```
config/settings.json
```

ตัวอย่าง:

โพสต์วันละ 1:

```json
"posts_per_run":1
```

โพสต์วันละ 5:

```json
"posts_per_run":5
```

---

# 7. การเปลี่ยนแนวเขียน AI

แก้:

```
config/prompts.json
```

ตัวอย่าง:

เพิ่ม:

```
Explain technical details.
Include download information.
Use SEO keywords naturally.
```

---

# 8. การเพิ่มแหล่งค้นหา

แก้:

```
config/sources.json
```

ตัวอย่าง:

```json
"vector":

[
"SVG Repo",

"Openclipart",

"New Source"
]
```

---

# 9. GitHub Secrets

ไปที่:

```
Repository

↓

Settings

↓

Secrets and variables

↓

Actions
```

เพิ่ม:

```
GEMINI_API_KEY


MAIN_REFRESH_TOKEN


MAIN_CLIENT_ID


MAIN_CLIENT_SECRET
```

---

# 10. ทดสอบระบบ

ก่อนเปิด Auto Post:

```
python test_system.py
```

ตรวจสอบ:

* Config
* Queue
* Secret
* Module

---

# 11. การรันเอง

เข้า:

```
GitHub

↓

Actions

↓

Blogger Auto Post V1.1

↓

Run Workflow
```

---

# 12. ปัญหาที่พบบ่อย

## Blogger Token หมดอายุ

สร้าง OAuth Token ใหม่

แล้วเปลี่ยน:

```
MAIN_REFRESH_TOKEN
```

---

## AI ไม่สร้างบทความ

ตรวจ:

```
GEMINI_API_KEY
```

---

## ไม่โพสต์

ตรวจ:

```
settings.json

workflow.json
```

---

# 13. การ Backup

ระบบเก็บ Backup ที่:

```
storage/backup/
```

ก่อนประมวลผลทุกครั้ง

---

# 14. การพัฒนาต่อ Version 2

สามารถเพิ่ม:

* AI Image Generation
* Dashboard
* Web Admin
* Analytics
* Auto SEO
* Internal Link
* Multi Account Manager

โดยไม่กระทบระบบหลัก

---

# Version

Current:

```
Blogger Download Auto Post V1.1
```

Status:

```
Ready For Testing
```

