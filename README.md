# 🤖 DXA Number Bot

<div align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" />
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" />
  <img src="https://img.shields.io/badge/telethon-1.34+-orange.svg" />
</div>

## 📝 বিবরণ
DXA Number Bot একটি শক্তিশালী টেলিগ্রাম বট যা OTP নাম্বার ফরওয়ার্ড করে এবং ইউজারদের ভার্চুয়াল নাম্বার প্রদান করে।

## ✨ বৈশিষ্ট্য
- 🔄 **অটো OTP ফরওয়ার্ডিং** - সোর্স গ্রুপ থেকে টার্গেট গ্রুপে OTP ফরওয়ার্ড
- 📱 **নাম্বার জেনারেশন** - ইউজাররা বিভিন্ন সার্ভিসের নাম্বার নিতে পারেন
- 👥 **ইউজার ম্যানেজমেন্ট** - অটোমেটিক ইউজার ট্র্যাকিং
- 🛠 **অ্যাডমিন প্যানেল** - সম্পূর্ণ কন্ট্রোল প্যানেল
- 📊 **স্ট্যাটাস মনিটরিং** - রিয়েল-টাইম স্টক স্ট্যাটাস
- 📢 **ব্রডকাস্ট সিস্টেম** - সকল ইউজারকে মেসেজ পাঠান

## 🚀 কুইক স্টার্ট

### প্রয়োজনীয় জিনিস
- Python 3.9 বা তার উপরে
- টেলিগ্রাম API ID ও Hash (https://my.telegram.org)
- দুইটি বট টোকেন ( @BotFather থেকে )

### ইনস্টলেশন
```bash
# রিপোজিটরি ক্লোন করুন
git clone https://github.com/আপনার-ইউজারনেম/dxa-number-bot.git
cd dxa-number-bot

# ডিপেন্ডেন্সি ইনস্টল করুন
pip install -r requirements.txt

# কনফিগারেশন সেট করুন
cp .env.example .env
# .env ফাইল এডিট করে আপনার তথ্য দিন

# বট চালু করুন
python bot.py
