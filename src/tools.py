"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # Tool 2: Đặt lịch hẹn tư vấn học vụ
    # 🎯 YÊU CẦU THIẾT KẾ SCHEMA (JSON SCHEMA STANDARD):
    # 1. Tool dùng để đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.
    # 2. Thiết kế các tham số (properties) để LLM trích xuất:
    #    - student_id (string): Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')
    #    - datetime_str (string): Thời gian hẹn (ví dụ: '14:00 15/09/2026')
    #    - advisor_name (string): Tên cố vấn học tập
    # 3. Khai báo danh sách các trường bắt buộc (required).
    # --------------------------------------------------------------------------
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch tư vấn (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Ngày và giờ hẹn tư vấn theo định dạng HH:MM DD/MM/YYYY (ví dụ: '14:00 15/09/2026')"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Họ tên cố vấn học tập sẽ tham gia buổi tư vấn"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },

    # Tool 3: Tra cứu lịch thi của sinh viên
    {
        "name": "exam_schedule_query",
        "description": "Tra cứu lịch thi của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu lịch thi (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },

    # Tool 4: Kiểm tra lịch trống của cố vấn trước khi đặt hẹn
    {
        "name": "advisor_availability",
        "description": "Kiểm tra các khung giờ còn trống của cố vấn học tập VinUni trong một ngày cụ thể.",
        "parameters": {
            "type": "object",
            "properties": {
                "advisor_name": {
                    "type": "string",
                    "description": "Họ tên cố vấn học tập cần kiểm tra lịch trống"
                },
                "date": {
                    "type": "string",
                    "description": "Ngày cần kiểm tra lịch trống theo định dạng DD/MM/YYYY (ví dụ: '15/09/2026')"
                }
            },
            "required": ["advisor_name", "date"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}

# Lịch thi giả lập theo mã sinh viên
EXAM_SCHEDULE_DATABASE = {
    "SV2026001": [
        {
            "course_code": "AI101",
            "course_name": "Nhập môn Trí tuệ Nhân tạo",
            "exam_date": "20/09/2026",
            "start_time": "08:00",
            "end_time": "10:00",
            "room": "C201"
        },
        {
            "course_code": "CS102",
            "course_name": "Cấu trúc Dữ liệu và Giải thuật",
            "exam_date": "23/09/2026",
            "start_time": "13:30",
            "end_time": "15:30",
            "room": "C305"
        }
    ],
    "SV2026002": [
        {
            "course_code": "AI101",
            "course_name": "Nhập môn Trí tuệ Nhân tạo",
            "exam_date": "20/09/2026",
            "start_time": "08:00",
            "end_time": "10:00",
            "room": "C201"
        },
        {
            "course_code": "MATH201",
            "course_name": "Xác suất và Thống kê",
            "exam_date": "25/09/2026",
            "start_time": "09:00",
            "end_time": "11:00",
            "room": "B102"
        }
    ]
}

# Các khung giờ tư vấn còn trống của từng cố vấn theo ngày
ADVISOR_AVAILABILITY_DATABASE = {
    "PGS.TS Nguyễn Văn A": {
        "15/09/2026": ["09:00", "14:00", "16:00"],
        "16/09/2026": ["10:00", "15:30"]
    },
    "TS. Lê Thị B": {
        "15/09/2026": ["08:30", "13:30"],
        "16/09/2026": ["09:00", "14:30", "16:30"]
    }
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn sau khi xác thực sinh viên, cố vấn và khung giờ trống."""
    normalized_student_id = student_id.strip().upper()
    normalized_advisor_name = advisor_name.strip()

    if normalized_student_id not in MOCK_DATABASE:
        return json.dumps({
            "status": "NOT_FOUND",
            "student_id": normalized_student_id,
            "message": f"Không tìm thấy sinh viên có mã '{normalized_student_id}' để đặt lịch."
        }, ensure_ascii=False)

    matched_advisor_name = next(
        (
            stored_name
            for stored_name in ADVISOR_AVAILABILITY_DATABASE
            if stored_name.casefold() == normalized_advisor_name.casefold()
        ),
        None
    )
    if matched_advisor_name is None:
        return json.dumps({
            "status": "NOT_FOUND",
            "advisor_name": normalized_advisor_name,
            "message": f"Không tìm thấy cố vấn có tên '{normalized_advisor_name}' để đặt lịch."
        }, ensure_ascii=False)

    datetime_parts = datetime_str.strip().split(maxsplit=1)
    if len(datetime_parts) != 2:
        return json.dumps({
            "status": "VALIDATION_ERROR",
            "message": "Thời gian hẹn phải có định dạng HH:MM DD/MM/YYYY."
        }, ensure_ascii=False)

    requested_time, requested_date = datetime_parts
    available_slots = ADVISOR_AVAILABILITY_DATABASE[matched_advisor_name].get(requested_date, [])
    if requested_time not in available_slots:
        return json.dumps({
            "status": "SLOT_UNAVAILABLE",
            "advisor_name": matched_advisor_name,
            "date": requested_date,
            "requested_time": requested_time,
            "available_slots": available_slots,
            "message": (
                f"Cố vấn {matched_advisor_name} không còn trống lúc {requested_time} ngày {requested_date}."
            )
        }, ensure_ascii=False)

    booking_id = (
        f"BK-{normalized_student_id}-{requested_date.replace('/', '')}-{requested_time.replace(':', '')}"
    )
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": booking_id,
        "student_id": normalized_student_id,
        "datetime": f"{requested_time} {requested_date}",
        "advisor": matched_advisor_name,
        "message": (
            f"Đặt lịch thành công cho sinh viên {normalized_student_id} với "
            f"{matched_advisor_name} vào lúc {requested_time} {requested_date}."
        )
    }, ensure_ascii=False)


def execute_exam_schedule_query(student_id: str) -> str:
    """Thực thi tra cứu lịch thi theo mã sinh viên"""
    normalized_student_id = student_id.strip().upper()
    exams = EXAM_SCHEDULE_DATABASE.get(normalized_student_id)

    if exams is not None:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": normalized_student_id,
            "exam_count": len(exams),
            "exams": exams
        }, ensure_ascii=False)

    return json.dumps({
        "status": "NOT_FOUND",
        "student_id": normalized_student_id,
        "message": f"Không tìm thấy lịch thi của sinh viên có mã '{normalized_student_id}'"
    }, ensure_ascii=False)


def execute_advisor_availability(advisor_name: str, date: str) -> str:
    """Thực thi kiểm tra các khung giờ trống của cố vấn trong một ngày"""
    normalized_name = advisor_name.strip()
    normalized_date = date.strip()
    matched_name = next(
        (
            stored_name
            for stored_name in ADVISOR_AVAILABILITY_DATABASE
            if stored_name.casefold() == normalized_name.casefold()
        ),
        None
    )

    if matched_name is None:
        return json.dumps({
            "status": "NOT_FOUND",
            "advisor_name": normalized_name,
            "message": f"Không tìm thấy cố vấn có tên '{normalized_name}'"
        }, ensure_ascii=False)

    available_slots = ADVISOR_AVAILABILITY_DATABASE[matched_name].get(normalized_date, [])
    if not available_slots:
        return json.dumps({
            "status": "NO_AVAILABILITY",
            "advisor_name": matched_name,
            "date": normalized_date,
            "available_slots": [],
            "message": f"Cố vấn {matched_name} không có khung giờ trống vào ngày {normalized_date}."
        }, ensure_ascii=False)

    return json.dumps({
        "status": "SUCCESS",
        "advisor_name": matched_name,
        "date": normalized_date,
        "available_slots": available_slots,
        "message": f"Cố vấn {matched_name} còn {len(available_slots)} khung giờ trống vào ngày {normalized_date}."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "exam_schedule_query": execute_exam_schedule_query,
    "advisor_availability": execute_advisor_availability
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
