# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
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
| Public URL | Chưa có — chờ Apply Blueprint và deploy thành công |
| Platform | Render |
| Ngày deploy | Chưa xác nhận — đang chuẩn bị Blueprint |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | Chờ deploy | Render tự gán |
| `AGENT_API_KEY` | Chờ nhập trên Dashboard | Blueprint dùng `sync: false`; không nằm trong repo |
| `REDIS_URL` | Chờ deploy | Internal connection string của Render Key Value `day12-redis` |
| `RATE_LIMIT_PER_MINUTE` | Đã khai báo trong Blueprint | 10 |
| `MONTHLY_BUDGET_USD` | Đã khai báo trong Blueprint | 10.0 |
| `LOG_LEVEL` | Đã khai báo trong Blueprint | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $DEPLOY_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy l\u00e0 g\u00ec?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $DEPLOY_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Dán output của các lệnh trên vào đây:

```
Chưa có kết quả HTTP trên cloud. Chỉ cập nhật sau khi deploy thành công
và chạy các lệnh kiểm tra trên Public URL thật.
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên platform
- `screenshots/health.png` — kết quả gọi `/health` từ trình duyệt hoặc curl

---

## Trạng Thái Triển Khai

`render.yaml` khai báo web service Docker `day12-agent` và Render Key Value
`day12-redis`, đều dùng gói Free tại Singapore. Key Value chỉ mở kết nối nội
bộ và dùng `noeviction` để không tự loại các key rate limit/ngân sách.

Blueprint đã được kiểm tra bằng JSON Schema chính thức của Render.
Chưa xác nhận deploy live, Public URL hoặc ảnh Dashboard. CP5 chỉ được coi
là hoàn tất sau khi có các bằng chứng chạy thật ở trên.

`DEPLOY_API_KEY` trong `.env` cục bộ là API key của chính service đã deploy,
không phải token quản trị Render. Không commit `.env` hoặc giá trị secret.
