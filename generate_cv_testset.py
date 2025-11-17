from faker import Faker
import json
import random
import os

fake = Faker('vi_VN')  # Fake data tiếng Việt

# Danh sách ngành nghề đa dạng
industries = [
    "Sales nội thất", "Fresher IT", "Developer React", "Digital Marketing", "Kế toán",
    "HR Recruiter", "Chuyển ngành sales→IT", "CV ảo với Python/AWS", "CV tiếng Anh", "Sales B2B"
] * 5  # Lặp để đủ 50

def generate_cv(industry):
    cv = {
        "personal_info": {
            "name": fake.name(),
            "title": fake.job() if random.random() > 0.5 else f"Nhân viên {industry}",
            "email": fake.email(),
            "phone": fake.phone_number()
        },
        "education": [
            {
                "school": fake.company(),
                "major": fake.job(),
                "time": f"({random.randint(2015, 2022)} - {random.randint(2019, 2025)})"
            }
        ],
        "experience": [
            {
                "company": fake.company(),
                "role": f"Chuyên viên {industry}",
                "duration": f"({random.randint(2020, 2023)} - {random.randint(2024, 2025)})",
                "description": [fake.sentence() for _ in range(random.randint(3, 7))]
            }
        ],
        "certifications": [fake.word() if random.random() > 0.5 else "SCPS"],
        "skills": ["Python", "NextJs", "AWS"] if "ảo" in industry else ["Excel", "CRM"],
        "awards": [fake.sentence(nb_words=5)] if random.random() > 0.7 else [],
        "hobbies": [fake.sentence()],
        "activities": [fake.date_between(start_date='-5y', end_date='today').strftime('%Y')],
        "other_sections": {"DỰ ÁN": []}
    }
    # Thêm hallucination test: random nhét tech skills vào CV không liên quan
    if random.random() > 0.6:
        cv["skills"].extend(["GraphQL", "ML"])
    return cv

# Tạo folder và 50 file
os.makedirs("cv_testset", exist_ok=True)
for i in range(50):
    industry = industries[i % len(industries)]
    cv_data = generate_cv(industry)
    safe_industry = industry.replace(' ', '_').replace('/', '_')
    with open(f"cv_testset/cv_{i+1:02d}_{safe_industry}.json", "w", encoding="utf-8") as f:
        json.dump(cv_data, f, ensure_ascii=False, indent=4)

print("Đã tạo xong 50 file CV test trong folder 'cv_testset'! Mỗi file là JSON chuẩn như CV gốc của bạn.")
