# Serenify 

## Your Mental Health Companion

Serenify is a **full-stack mental health companion web application** designed to help users reflect, track emotions, and seek support in a secure and structured way. It brings together journaling, mood analytics, symbolic emotional release, and conversational support into a single, cohesive platform.

The project was developed with two core goals:

1. To create a **meaningful, user-focused mental health tool**
2. To strengthen full-stack development skills using Python, Flask, and modern web technologies

---

## Problem Statement

People struggling with mental health often rely on scattered tools—notebooks, apps, self-help articles, or external assistance. This fragmentation makes it difficult to:

* Track emotional patterns consistently
* Express feelings safely
* Access timely guidance in moments of distress

Serenify addresses this gap by providing a **centralized, private, and interactive mental health platform**.

---

## Solution Overview

Serenify enables users to:

* Maintain private digital diaries
* Track and visualize mood trends over time
* Release negative emotions symbolically without data storage
* Interact with a supportive chatbot for immediate guidance
* Access professional mental health resources when needed

The platform is designed with **privacy, emotional sensitivity, and usability** as top priorities.

---

## ✨ Key Features

### Authentication

* User registration and login with hashed passwords
* Secure session management using Flask-Login

### CRUD Diary Module

* Create, read, update, and delete private diary entries
* Automatic timestamps and user-defined tags
* Mood indicators (emojis) attached to entries

### Symbolic Void Release (Unique Feature)

* A dedicated space to type out frustrations or worries
* Content is **never stored**—only the action is logged
* Symbolic release reinforced with positive visual feedback

### Mood Tracking & Analytics

* Quick mood logging with timestamps
* Optional linking of mood logs to diary entries
* Interactive charts (Chart.js) to visualize trends and patterns
* Weekly summaries and emotional correlations

### Intelligent Chatbot Support

* Integrated chatbot using Gemini API
* Provides supportive, non-clinical responses from a curated knowledge base
* Emergency keyword detection with redirection to professional help

### Professional Support Module

* Browse and search verified professionals
* Appointment booking and status tracking
* Secure chat for confirmed sessions

---

## 🛠️ Technology Stack

### Frontend

* HTML, CSS, Bootstrap
* Jinja2 Templates
* JavaScript (used where required for client-side interactivity and dynamic behavior)

### Backend

* Python 3.x
* Flask (Monolithic MVC Architecture)
* Flask-Login & Flask-Session

### Data Handling / ORM

* SQLAlchemy ORM (for structured data modeling and abstraction)

### AI / Logic

* Gemini (API Key)


##  System Architecture

Serenify follows a **Monolithic MVC architecture**:

* **Model Layer**: SQLAlchemy models for Users, Diary Entries, Mood Logs, Appointments
* **View Layer**: Jinja2 templates with responsive UI
* **Controller Layer**: Flask routes handling business logic and chatbot processing

Special care is taken to ensure:

* User-specific data isolation
* No persistence of Void content
* Secure client–server communication

---


## Target Users

* Individuals seeking daily emotional reflection tools
* Users who want visual insight into their mental health patterns
* People needing immediate, discreet conversational support
* Users looking for guided access to mental health professionals

---

## Future Enhancements

* AI-driven mood sentiment analysis
* Personalized coping strategies
* Real-time chat with certified therapists
* Wearable device integration for stress tracking
* Mobile application support

---

## Why Serenify Matters

Serenify is not just a course project—it represents a shift toward **emotionally intelligent software**.

It combines:

* Technical depth (full-stack architecture)
* Ethical design (privacy-first mental health features)
* Real-world impact (user-focused emotional support)

---

*Serenify aims to make mental health reflection structured, private, and empowering.*
