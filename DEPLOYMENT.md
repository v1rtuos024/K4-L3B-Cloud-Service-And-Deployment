# Thông Tin Deploy — Checkpoint 5

> `pytest tests/test_cp5.py` đọc Public URL dưới đây để kiểm tra service thật.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Nguyễn Thành Vinh |
| Mã học viên | 2A202602889 |
| Repo | https://github.com/v1rtuos024/K4-L3B-Cloud-Service-And-Deployment |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-agent-6lg4.onrender.com |
| Platform | Render |
| Ngày deploy | 2026-09-29; live lúc 11:02:33 giờ Việt Nam |
| Web service | `day12-agent` — `srv-datjg7vavr4c73dq0gv0` |
| Key Value | `day12-redis` — `red-datjg2navr4c73dpvri0` |
| Commit đã deploy | `b278e1486de4f3dff68049b8c9ef3d27876b4c71` |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | Render tự gán |
| `AGENT_API_KEY` | ✅ | Nhập trên Dashboard; Blueprint dùng `sync: false`; startup đã thành công |
| `REDIS_URL` | ✅ | Internal connection string của Render Key Value `day12-redis`; `/ready` xác nhận kết nối |
| `RATE_LIMIT_PER_MINUTE` | ✅ | Blueprint khai báo 10 |
| `MONTHLY_BUDGET_USD` | ✅ | Blueprint khai báo 10.0 |
| `LOG_LEVEL` | ✅ | Blueprint khai báo INFO |

## Lệnh Kiểm Tra

Các lệnh dưới đây chạy trong Bash/Git Bash. Các bước 4–5 là kiểm tra bổ sung,
cần nạp `DEPLOY_API_KEY` của service cloud từ `.env` cục bộ.

```bash
URL=https://day12-agent-6lg4.onrender.com

# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i "$URL/health"

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i "$URL/ready"

# 3. Không có API key — mong đợi 401
curl -i -X POST "$URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST "$URL/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DEPLOY_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy l\u00e0 g\u00ec?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST "$URL/ask" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $DEPLOY_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Kiểm tra trực tiếp Public URL lúc 11:06:47 ngày 2026-09-29 (UTC+7).
Dưới đây là status, các header chính và body từ output curl thực tế:

```
GET /health
HTTP/1.1 200 OK
Date: Tue, 29 Sep 2026 04:06:47 GMT
Content-Type: application/json
x-render-origin-server: uvicorn

{"status":"ok","service":"day12-agent","version":"1.0.0"}

GET /ready
HTTP/1.1 200 OK
Date: Tue, 29 Sep 2026 04:06:47 GMT
Content-Type: application/json
x-render-origin-server: uvicorn

{"status":"ready","redis":true}

POST /ask — body {"question":"Hello"}, không gửi API key
HTTP/1.1 401 Unauthorized
Date: Tue, 29 Sep 2026 04:06:47 GMT
Content-Type: application/json
x-render-origin-server: uvicorn

{"detail":"invalid or missing API key"}
```

## Ảnh Chụp Màn Hình

Ảnh minh chứng đã lưu trong thư mục `screenshots/`:

- [Dashboard Render](screenshots/dashboard.png) — service `day12-agent`, bản deploy Live.
- [Kết quả /health](screenshots/health.png) — Public URL trả JSON `status: ok`.

---

## Trạng Thái Triển Khai

`render.yaml` khai báo web service Docker `day12-agent` và Render Key Value
`day12-redis`, đều dùng gói Free tại Singapore. Key Value chỉ mở kết nối nội
bộ và dùng `noeviction` để không tự loại các key rate limit/ngân sách.

Blueprint đã được kiểm tra bằng JSON Schema chính thức của Render.
Render xác nhận deploy `dep-datjg87avr4c73dq0hv0` có trạng thái `live` và
Key Value có trạng thái `available`. Ba kiểm tra HTTP bắt buộc đều đạt.
Hai ảnh minh chứng Dashboard và `/health` đã được bổ sung và kiểm tra.

Key Value Free không có disk persistence (`persistenceMode: off`): history
và các bộ đếm sống qua restart của web service, nhưng có thể mất nếu chính
Key Value restart. Đây là giới hạn của gói Free, xem
[tài liệu Render Key Value](https://render.com/docs/key-value).

`DEPLOY_API_KEY` trong `.env` cục bộ là API key của chính service đã deploy,
không phải token quản trị Render. Không commit `.env` hoặc giá trị secret.

## Kết Quả Checkpoint

Chạy với `LOCAL_FALLBACK=false` để kiểm tra đúng URL cloud:

```text
pytest tests/test_cp5.py -v
9 passed, 4 skipped in 1.54s
```

Bốn test tài liệu và cả năm test Public URL đều pass, bao gồm `/ask` có
xác thực bằng `DEPLOY_API_KEY`: HTTP 200 và có câu trả lời. Bốn test
fallback cục bộ bị skip vì đang dùng Render thật. Chưa kiểm tra rate limit
trên cloud trong lần chạy này.
