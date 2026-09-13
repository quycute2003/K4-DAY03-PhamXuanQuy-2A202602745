"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError


def build_contextual_prompt(prompt: str, tool_history: List[Dict[str, Any]] = None) -> str:
    """Bổ sung Observation từ các bước trước để LLM quyết định bước ReAct kế tiếp."""
    if not tool_history:
        return prompt

    history_json = json.dumps(tool_history, ensure_ascii=False, indent=2)
    return (
        f"Yêu cầu ban đầu của người dùng:\n{prompt}\n\n"
        f"Các Tool Call và Observation đã thực hiện:\n{history_json}\n\n"
        "Hãy tiếp tục xử lý mục tiêu ban đầu. Không gọi lại một tool với cùng tham số nếu đã có "
        "Observation tương ứng. Nếu cần thêm dữ liệu, hãy gọi tool kế tiếp; nếu đã đủ dữ liệu, "
        "hãy trả lời cuối cùng bằng văn bản."
    )


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        student_match = re.search(r"\bsv\d+\b", prompt, re.IGNORECASE)
        date_match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", prompt)
        time_match = re.search(r"\b(?:[01]\d|2[0-3]):[0-5]\d\b", prompt)
        student_id = student_match.group(0).upper() if student_match else "SV2026001"
        requested_date = date_match.group(0) if date_match else "15/09/2026"
        requested_time = time_match.group(0) if time_match else "14:00"
        history = tool_history or []
        completed_tools = [item.get("tool_name") for item in history]
        last_observation = history[-1].get("observation", {}) if history else {}
        booking_requested = "đặt lịch" in prompt_lower
        multi_step_booking = "tra cứu" in prompt_lower and booking_requested

        if history and last_observation.get("status") != "SUCCESS":
            return {
                "type": "text",
                "content": last_observation.get(
                    "message",
                    f"Không thể hoàn tất yêu cầu vì công cụ trả về trạng thái {last_observation.get('status', 'UNKNOWN')}."
                ),
                "thought": "Observation báo thao tác không thành công nên Agent dừng và phản hồi lỗi cho người dùng."
            }

        if history and completed_tools[-1] == "schedule_appointment":
            return {
                "type": "text",
                "content": last_observation.get("message", "Đã đặt lịch tư vấn thành công."),
                "thought": "Đã nhận xác nhận đặt lịch từ MCP Server nên có thể trả lời cuối cùng."
            }

        if history and completed_tools[-1] == "exam_schedule_query":
            exams = last_observation.get("exams", [])
            exam_lines = [
                f"{exam['course_code']} - {exam['course_name']}: {exam['start_time']}-{exam['end_time']} "
                f"ngày {exam['exam_date']}, phòng {exam['room']}"
                for exam in exams
            ]
            return {
                "type": "text",
                "content": f"Lịch thi của {student_id}: " + "; ".join(exam_lines),
                "thought": "Đã nhận đủ lịch thi từ MCP Server nên có thể tổng hợp câu trả lời."
            }

        if history and completed_tools[-1] == "advisor_availability":
            available_slots = last_observation.get("available_slots", [])
            if booking_requested and requested_time in available_slots:
                academic_observation = next(
                    (
                        item.get("observation", {})
                        for item in history
                        if item.get("tool_name") == "academic_query"
                    ),
                    {}
                )
                advisor_name = academic_observation.get("data", {}).get(
                    "advisor",
                    last_observation.get("advisor_name", "PGS.TS Nguyễn Văn A")
                )
                return {
                    "type": "tool_call",
                    "tool_name": "schedule_appointment",
                    "arguments": {
                        "student_id": student_id,
                        "datetime_str": f"{requested_time} {requested_date}",
                        "advisor_name": advisor_name
                    },
                    "thought": "Khung giờ yêu cầu còn trống. Tôi sẽ gọi tool schedule_appointment để hoàn tất đặt lịch."
                }

            if booking_requested:
                return {
                    "type": "text",
                    "content": (
                        f"Cố vấn không còn trống lúc {requested_time} ngày {requested_date}. "
                        f"Các giờ còn trống: {', '.join(available_slots) if available_slots else 'không có'}."
                    ),
                    "thought": "Khung giờ người dùng yêu cầu không khả dụng nên không thực hiện đặt lịch."
                }

            return {
                "type": "text",
                "content": last_observation.get("message", "Đã kiểm tra lịch trống của cố vấn."),
                "thought": "Đã nhận đủ thông tin lịch trống nên có thể trả lời cuối cùng."
            }

        if history and completed_tools[-1] == "academic_query":
            if multi_step_booking:
                advisor_name = last_observation.get("data", {}).get("advisor", "")
                return {
                    "type": "tool_call",
                    "tool_name": "advisor_availability",
                    "arguments": {"advisor_name": advisor_name, "date": requested_date},
                    "thought": "Đã xác định được cố vấn của sinh viên. Tôi sẽ kiểm tra lịch trống trước khi đặt hẹn."
                }

            data = last_observation.get("data", {})
            return {
                "type": "text",
                "content": (
                    f"Sinh viên {last_observation.get('student_id', student_id)} - {data.get('full_name', '')}, "
                    f"lớp {data.get('class', '')}, GPA {data.get('gpa', '')}, cố vấn {data.get('advisor', '')}."
                ),
                "thought": "Đã nhận đủ dữ liệu học vụ từ MCP Server nên có thể trả lời cuối cùng."
            }

        # Mô phỏng quyết định Tool Call đầu tiên
        if "lịch thi" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "exam_schedule_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu lịch thi của {student_id}. Tôi sẽ gọi tool exam_schedule_query."
            }
        elif "lịch trống" in prompt_lower or "khung giờ" in prompt_lower:
            advisor_name = "TS. Lê Thị B" if "lê thị b" in prompt_lower else "PGS.TS Nguyễn Văn A"
            return {
                "type": "tool_call",
                "tool_name": "advisor_availability",
                "arguments": {"advisor_name": advisor_name, "date": requested_date},
                "thought": f"Người dùng muốn kiểm tra lịch trống của {advisor_name} ngày {requested_date}. Tôi sẽ gọi tool advisor_availability."
            }
        elif multi_step_booking:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": "Yêu cầu cần tra cứu cố vấn trước khi đặt lịch. Tôi sẽ bắt đầu bằng tool academic_query."
            }
        elif booking_requested:
            advisor_name = "TS. Lê Thị B" if "lê thị b" in prompt_lower else "PGS.TS Nguyễn Văn A"
            return {
                "type": "tool_call",
                "tool_name": "advisor_availability",
                "arguments": {"advisor_name": advisor_name, "date": requested_date},
                "thought": "Người dùng yêu cầu đặt lịch. Tôi sẽ kiểm tra khung giờ của cố vấn trước khi xác nhận."
            }
        elif student_match or "tra cứu" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Người dùng muốn tra cứu thông tin học vụ của {student_id}. Tôi sẽ gọi tool academic_query."
            }
        else:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Quy chế học vụ VinUni yêu cầu sinh viên tích lũy tối thiểu 120 tín chỉ và duy trì GPA trên 2.0 để tốt nghiệp.",
                "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        self.request_interval_seconds = float(os.getenv("GEMINI_REQUEST_INTERVAL_SECONDS", "13"))
        self.max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "5"))
        self.allow_mock_fallback = os.getenv("GEMINI_ALLOW_MOCK_FALLBACK", "false").lower() == "true"
        self._last_request_at = 0.0

    def _generate_content_with_rate_limit(self, client, **request_kwargs):
        """Giới hạn tốc độ gọi Gemini và tự retry khi Free Tier trả về HTTP 429."""
        for attempt in range(self.max_retries + 1):
            elapsed = time.monotonic() - self._last_request_at
            wait_seconds = max(0.0, self.request_interval_seconds - elapsed)
            if wait_seconds > 0:
                print(f"⏳ [GEMINI RATE LIMIT]: Chờ {wait_seconds:.1f}s trước request tiếp theo...")
                time.sleep(wait_seconds)

            self._last_request_at = time.monotonic()
            try:
                return client.models.generate_content(**request_kwargs)
            except Exception as exc:
                error_text = str(exc)
                is_rate_limit_error = "429" in error_text or "RESOURCE_EXHAUSTED" in error_text
                if not is_rate_limit_error or attempt >= self.max_retries:
                    raise

                retry_match = re.search(
                    r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s",
                    error_text
                )
                server_retry_seconds = float(retry_match.group(1)) if retry_match else 0.0
                retry_seconds = max(self.request_interval_seconds, server_retry_seconds)
                print(
                    f"⏳ [GEMINI 429 RETRY]: Hết quota tạm thời, chờ {retry_seconds:.1f}s "
                    f"rồi thử lại ({attempt + 1}/{self.max_retries})..."
                )
                time.sleep(retry_seconds)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = self._generate_content_with_rate_limit(
                client,
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = self._generate_content_with_rate_limit(
                client,
                model=self.model_name,
                contents=build_contextual_prompt(prompt, tool_history),
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            if self.allow_mock_fallback:
                print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
                return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)
            raise RuntimeError(
                f"Gemini API thất bại sau khi retry; dừng nghiệm thu để tránh tạo trace trộn với Mock: {e}"
            ) from e


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.allow_mock_fallback = os.getenv("OPENAI_ALLOW_MOCK_FALLBACK", "false").lower() == "true"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
        tool_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": build_contextual_prompt(prompt, tool_history)})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            if self.allow_mock_fallback:
                print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
                return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt, tool_history)
            raise RuntimeError(
                f"OpenAI API thất bại; dừng nghiệm thu để tránh tạo trace trộn với Mock: {e}"
            ) from e


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
