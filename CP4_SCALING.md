# Thử scale CP4

`docker-compose.yml` dùng cổng `8000:8000` cho một agent. Khi scale, dùng thêm
`docker-compose.scale.yml` để mỗi replica có một cổng localhost được Docker
cấp riêng, tránh tranh cùng cổng 8000.

File scale dùng `!override`, yêu cầu Docker Compose 2.24.4 trở lên:
[tài liệu merge của Docker](https://docs.docker.com/reference/compose-file/merge/).

```bash
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --build --scale agent=3 --wait
docker compose -f docker-compose.yml -f docker-compose.scale.yml ps

# Xem địa chỉ từng replica để thử /health, /ready và /ask.
docker compose -f docker-compose.yml -f docker-compose.scale.yml port --index 1 agent 8000
docker compose -f docker-compose.yml -f docker-compose.scale.yml port --index 2 agent 8000
docker compose -f docker-compose.yml -f docker-compose.scale.yml port --index 3 agent 8000
```

Gửi request với cùng `X-User-Id` đến các địa chỉ trên: `history_length` lần
lượt là 0, 2, 4 với một user mới. Cả ba replica dùng Redis của cùng stack.
History giữ tối đa 20 message và hết hạn sau 7 ngày kể từ lần ghi cuối.

`/health` chỉ đọc trạng thái process. `/ready` gọi Redis và trả 503 nếu Redis
lỗi hoặc process đang shutdown. Readiness không yêu cầu API key.

Trở về một agent tại `http://localhost:8000`:

```bash
docker compose up -d --scale agent=1 --wait
```

Lệnh trên giữ volume Redis và history đã ghi. Nếu thêm Nginx để học load
balancing, đặt proxy trước các replica thay vì gán cùng một cổng host cho
từng replica.
