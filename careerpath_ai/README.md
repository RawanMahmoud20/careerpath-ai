\# CareerPath AI 🚀

\### AI-Powered Career Transition Planner



A Django web application that helps users identify skill gaps and create personalized career transition roadmaps.



\---



\## 📸 Screenshots



\### Dashboard

!\[alt text](image.png)

\### Landing Page

!\[alt text](image-1.png)

\### Skill Gap Analysis

!\[alt text](image-2.png)

\### Career Roadmap

!\[alt text](image-3.png)

\---



\## 📁 Project Structure



```

careerpath-ai/

├── careerpath\_ai/          # Project settings \& main urls

├── apps/

│   ├── accounts/           # Auth + User Profile

│   ├── careers/            # Careers, Skills, CareerSkill mapping

│   ├── roadmap/            # Roadmap phases, tasks, user progress

│   ├── analysis/           # Skill gap logic + AI recommendations

│   └── dashboard/          # User dashboard

├── templates/

├── static/

├── .env                    # (not committed — copy from .env.example)

└── requirements.txt

```



\---



\## ⚙️ Setup Instructions



\### 1. Clone the repo

```bash

git clone https://github.com/YOUR\_USERNAME/careerpath-ai.git

cd careerpath-ai

```



\### 2. Create virtual environment

```bash

python -m venv venv

venv\\Scripts\\activate        # Windows

\# source venv/bin/activate   # Mac/Linux

```



\### 3. Install dependencies

```bash

pip install -r requirements.txt

```



\### 4. Create .env file

```bash

copy .env.example .env       # Windows

\# cp .env.example .env       # Mac/Linux

```

Then fill in your MySQL password and other values.



\### 5. Create MySQL database

```sql

CREATE DATABASE careerpath\_db CHARACTER SET utf8mb4 COLLATE utf8mb4\_unicode\_ci;

```



\### 6. Run migrations

```bash

python manage.py makemigrations

python manage.py migrate

```



\### 7. Create superuser

```bash

python manage.py createsuperuser

```



\### 8. Run server

```bash

python manage.py runserver

```



\---



\## 👥 Team Task Division



| Member | Responsibility |

|--------|---------------|

| Member 1 | `accounts` app — Auth, Profile, UserSkill form |

| Member 2 | `careers` + `analysis` apps — Models, skill gap logic, result page |

| Member 3 | `roadmap` + AI integration |

| Rawan Mahmoud | Dashboard, Links, Navigation, Testing, Documentation \& Presentation |



\---



\## 🤖 AI Integration



\- \*\*Phase A\*\*: Pure Django skill gap logic (works without API key)

\- \*\*Phase B\*\*: OpenAI GPT-3.5 for personalized career summaries



Set `OPENAI\_API\_KEY` in `.env` to enable Phase B.

