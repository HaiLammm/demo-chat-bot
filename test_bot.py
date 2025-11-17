import json
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

# Model Ollama của bạn
llm = ChatOllama(model="cv-analyzer", temperature=0.3)

# Prompt chuẩn từ trước (thay {context} bằng knowledge.txt nếu có)
prompt_template = """
Bạn là chuyên gia CV Việt Nam. Phân tích CV sau cho ngành {industry}:
CV JSON: {cv_json}

Output ngắn gọn: Điểm mạnh | Điểm yếu | Top 3 kỹ năng bổ sung (không bịa tech nếu không có).
"""

chain = PromptTemplate.from_template(prompt_template) | llm

# Test tất cả 50 file
test_folder = "cv_testset"
results = []
for filename in os.listdir(test_folder):
    if filename.endswith('.json'):
        with open(os.path.join(test_folder, filename), 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
        industry = filename.split('_')[-1].replace('.json', '').replace('_', ' ')
        result = chain.invoke({
            "cv_json": json.dumps(cv_data, ensure_ascii=False),
            "industry": industry
        })
        results.append(f"File {filename}: {result.content[:200]}...")  # Log ngắn
        print(f"Tested {filename} - Output: {result.content[:100]}...")

with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

danger_words = ["AWS", "Python", "NextJs", "SaaS", "Tech Sales", "Microsoft", "Google Cloud", "AI", "ML", "Docker"]
danger_count = sum(1 for line in open("test_results.txt", encoding="utf-8") 
                   if any(word.lower() in line.lower() for word in danger_words))

print(f"\n🎯 KẾT QUẢ TEST 50 CV")
print(f"   Hallucination rate: {danger_count}/50 → {(danger_count/50)*100}%")
if danger_count == 0:
    print("   🚀 BOT SẠCH 100% – THẢ RA DISCORD NGAY VÀ LUÔN!")
else:
    print(f"   ⚠️  Còn {danger_count} trường hợp ảo → mở test_results.txt sửa prompt tiếp!")
