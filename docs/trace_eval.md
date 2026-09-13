# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Phạm Xuân Quý
> **Mã Sinh Viên / Mã Học viên:** 2A202602745
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Tra cứu Lịch thi VinUni

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Một số yêu cầu cần được chia thành nhiều bước nối tiếp, chẳng hạn xác định mã sinh viên, tra cứu hồ sơ và cố vấn học tập, sau đó dùng thông tin thu được để đặt lịch tư vấn. Các câu hỏi học vụ chung vẫn có thể được trả lời trực tiếp nên tiêu chí này chưa ở mức tuyệt đối. |
| **2. Tool Interaction** | 5 / 5 | Agent bắt buộc tương tác với MCP Server để gọi công cụ `academic_query` khi tra cứu dữ liệu sinh viên và `schedule_appointment` khi thực hiện hành động đặt lịch; LLM không thể tự tạo ra dữ liệu thời gian thực một cách đáng tin cậy. |
| **3. Dynamic Decision** | 5 / 5 | Agent phải tự quyết định có cần gọi công cụ hay không, chọn đúng công cụ theo ý định người dùng và lựa chọn bước kế tiếp dựa trên Observation, ví dụ chỉ đặt lịch sau khi đã tìm thấy sinh viên và xác định đúng cố vấn. |
| **4. Long Horizon Goal** | 4 / 5 | Với yêu cầu đa bước, Agent phải duy trì mục tiêu ban đầu và các dữ kiện như mã sinh viên, thời gian hẹn và tên cố vấn qua nhiều lượt Thought–Action–Observation cho đến khi trả lời cuối cùng. Phạm vi bài lab còn ngắn và chưa yêu cầu bộ nhớ dài hạn. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | Tổng điểm lớn hơn 12/20, vì vậy bài toán phù hợp để triển khai dưới dạng ReAct Agent kết nối MCP Server. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dưới đây là trace tiêu biểu của TC04 được sinh từ OpenAI API thật. Agent đã tra cứu cố vấn, kiểm tra lịch trống, đặt lịch và tổng hợp câu trả lời cuối cùng:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu cố vấn học tập của sinh viên SV2026002, sau đó đặt lịch tư vấn với cố vấn đó vào lúc 09:00 ngày 16/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "thought": "OpenAI quyết định gọi công cụ 'academic_query' với tham số: {\"student_id\": \"SV2026002\"}",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "data": {
        "full_name": "Trần Thị Bình",
        "advisor": "TS. Lê Thị B"
      }
    },
    "latency_ms": 807.73
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "thought": "OpenAI quyết định gọi công cụ 'advisor_availability' với tham số ngày 16/09/2026.",
    "tool_name": "advisor_availability",
    "arguments": {
      "advisor_name": "TS. Lê Thị B",
      "date": "16/09/2026"
    },
    "observation": {
      "status": "SUCCESS",
      "available_slots": ["09:00", "14:30", "16:30"]
    },
    "latency_ms": 999.92
  },
  {
    "step": 3,
    "action_type": "TOOL_EXECUTION",
    "thought": "OpenAI quyết định gọi công cụ 'schedule_appointment' với khung giờ đã được xác nhận còn trống.",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "SV2026002",
      "datetime_str": "09:00 16/09/2026",
      "advisor_name": "TS. Lê Thị B"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026002-16092026-0900"
    },
    "latency_ms": 951.81
  },
  {
    "step": 4,
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Cố vấn học tập của sinh viên SV2026002 là TS. Lê Thị B. Đã đặt lịch tư vấn thành công vào lúc 09:00 ngày 16/09/2026.",
    "latency_ms": 1666.9
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy thành công trên OpenAI API thật với model `gpt-4o-mini`, không fallback sang Mock.
- **Tổng số Test Cases đã chạy thành công:** 7 / 7 test cases *(5 test bắt buộc + 2 test mở rộng)*.
- **Số lượt gọi Tool qua MCP Server chính xác:** 9 lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
