# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Các câu trả lời dưới đây dựa trên code và các lần chạy kiểm chứng của bài.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Thành Vinh — Mã học viên: 2A202602889

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi tạo service từ Blueprint trên Render, mình có thể quên nhập
`AGENT_API_KEY`. Nếu khóa mặc định là `changeme`, service vẫn lên và người
biết khóa này có thể gọi `/ask`. Fail fast giúp phát hiện thiếu cấu hình ngay
trong startup, trước khi nhận traffic và phát sinh chi phí.

Mình đã chạy image production mà không truyền secret. Log báo
`ValidationError: 1 validation error for Settings`, trường `agent_api_key`
có lỗi `Field required`, rồi `Application startup failed. Exiting.`.
Image không chứa `.env`, nên không có khóa cục bộ để vô tình che lỗi này.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng dưới đây lấy từ `docker compose logs --no-color agent`, sau khi gọi
`/ask` thành công trên máy ngày 29/09/2026. Phần tiền tố `agent-1 |` là do
Compose thêm khi hiển thị; nội dung event là đúng một dòng JSON:

```json
{"user_id": "exercises-de1e2379", "tokens_in": 3, "tokens_out": 37, "cost_usd": 2.265e-05, "event": "ask_completed", "level": "info", "timestamp": "2026-09-29T04:49:57.201753+00:00"}
```

Mình có thể lọc `event=ask_completed` theo `user_id` và thời gian UTC để
đếm các lượt gọi của một người. Mình cũng có thể cộng `cost_usd` và số
token theo ngày để theo dõi chi phí, thay vì phải đoán từ một câu thông
báo chung. JSON được in không có indent và dùng `ensure_ascii=False`; nếu
field có tiếng Việt thì chữ vẫn được giữ nguyên, còn xuống dòng trong
nội dung được escape để không tách event thành nhiều dòng.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu), `agent:single` | 1.73 GB, khoảng 1730 MB |
| Multi-stage, `agent:multi` | 309 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Mình đo ngày 29/09/2026 trên Docker Desktop. Dockerfile một stage được
lấy lại từ commit gốc `1bf8ea5`, nhưng cả hai bản đều dùng source,
`requirements.txt` và `.dockerignore` hiện tại để so sánh. Output thật:

```text
agent:single 1.73GB
agent:multi 309MB
```

Đây là dung lượng hiển thị bởi cùng lệnh `docker images --format`, đã
được Docker làm tròn, không phải dung lượng tải qua mạng. Theo số hiển
thị, bản mới giảm khoảng 1421 MB và nằm dưới yêu cầu 500 MB.

Phần giảm chủ yếu đến từ việc đổi `python:3.11` đầy đủ sang
`python:3.11-slim`: bỏ các công cụ build và thư viện hệ thống không cần
cho việc chạy app. Kiểm tra thật thấy bản gốc có `/usr/bin/gcc` và pip
cache 15.2 MB; bản runtime không có gcc. Bản gốc còn giữ pip cache sau
cài đặt; bản mới dùng `--no-cache-dir`. Runtime chỉ nhận venv đã cài và
source `app/`, `utils/`.
Mức giảm này là kết quả của cả lựa chọn base image lẫn cách build, không
thể coi là tác dụng riêng của việc thêm stage. Hai stage hiện đều dùng
slim và dependency trong venv vẫn được copy sang runtime; multi-stage
không tự loại các thư viện đã cài vào venv.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Mình thêm một chữ `s` vào docstring đầu `app/main.py`, build với
`--progress=plain`, rồi khôi phục file về đúng nội dung ban đầu. Output
hiện `CACHED` cho `WORKDIR`, `COPY requirements.txt`, bước tạo venv/cài pip,
bước tạo user và `COPY --from=builder /opt/venv /opt/venv`.
`COPY app/ ./app/` và bước tiếp theo `COPY utils/ ./utils/` chạy lại;
Docker cũng xuất lại image. Lần thử này không tải hay cài lại thư viện.

Nếu đưa `COPY . .` lên trước `RUN pip install`, chỉ một ký tự source thay
đổi cũng làm layer COPY đổi. Layer pip đứng sau sẽ mất cache và phải chạy
lại, dù `requirements.txt` không đổi. Đây là lý do mình tách dependency
khỏi source trong Dockerfile. Tham khảo
[quy tắc cache của Docker](https://docs.docker.com/build/cache/invalidation/).

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Một lỗi cho phép thực thi mã trong app có thể giúp kẻ tấn công chạy lệnh
với quyền của process Python. Nếu process là root trong container, họ có
quyền cao hơn để sửa file và tìm đường vượt lớp cách ly. Nếu còn có cấu
hình nguy hiểm như cho truy cập Docker socket, mount thư mục host với
quyền ghi, hoặc một lỗ hổng kernel/runtime, họ có thể tiến tới quyền cao
trên host. Root trong container không tự động đồng nghĩa với root trên host;
còn phải vượt cách ly hoặc tận dụng quyền đã được cấp.

`USER appuser` chặn bước được thừa hưởng root ngay khi chiếm process app.
Mình kiểm tra bằng `docker compose exec -T agent id` và nhận
`uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)`. Nó giảm quyền
và thiệt hại có thể gây ra, nhưng không thay thế việc giữ cấu hình mount,
socket và quyền container an toàn. Đối chiếu
[Docker Engine security](https://docs.docker.com/engine/security/).

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Với bộ đếm reset theo phút đồng hồ, có thể gửi 20 request trong hai giây:
10 request ngay trước mốc phút, ví dụ 10:00:59, rồi 10 request ngay sau
mốc đó, ví dụ 10:01:00. Hai nhóm thuộc hai phút khác nhau nên mỗi phút
đều chưa vượt 10, dù tải dồn lại rất lớn trong khoảng ngắn.

Sliding window của mình đếm 60 giây gần nhất nên nhóm thứ hai vẫn nhìn
thấy 10 request trước đó và bị 429. Redis ZSET lưu timestamp làm score;
request hết cửa sổ được xóa trước khi đếm. Member thêm UUID nên hai
request trùng timestamp không ghi đè nhau. Test đã xác nhận hết cửa sổ
thì gọi lại được, và các request đồng thời vẫn tôn trọng quota.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit quản lý tốc độ theo user trong 60 giây, còn cost guard quản lý
tổng USD của user theo tháng UTC. Mình thấy hai cơ chế trả lỗi khác nhau:
429 kèm `Retry-After` khi gọi quá nhanh, và 402 khi vượt ngân sách tháng.

Ví dụ một user chỉ gọi một lần mỗi phút nhưng đã tiêu 10.01 USD trong
tháng với ngân sách 10 USD: rate limit cho qua, cost guard chặn. Ngược
lại, user mới chỉ tiêu 0.001 USD nhưng gửi request thứ 11 trong 60 giây:
vẫn còn tiền nhưng rate limit chặn trước khi đến cost guard.

Với chi phí ước tính, `guard.check(estimated_cost=0.02)` cũng chặn nếu
đã tiêu 9.99 USD. Trong `/ask` hiện tại, mình gọi `guard.check(user_id)`
với ước tính mặc định 0, nên nó kiểm tra chi phí đã ghi; chưa đặt trước
ngân sách cho lượt sắp gọi. Vì vậy đây chưa phải giới hạn tiền tuyệt đối
cho request lớn hoặc nhiều request đồng thời. Cả hai bước kiểm tra vẫn
chạy trước LLM; test xác nhận các lỗi 401, 429 và 402 không gọi LLM.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Đầu tiên Redis mất kết nối, trong khi ba process agent vẫn còn chạy.
Nếu endpoint gộp kiểm tra Redis, cả ba probe sẽ trả lỗi. Load balancer
dùng kết quả này làm readiness sẽ ngừng gửi traffic tới các instance.
Nếu orchestrator cũng dùng nó làm liveness và lỗi kéo dài đủ số lần
probe đã cấu hình, nó sẽ restart các container. Container mới vẫn không
kết nối được Redis nên có thể tiếp tục bị restart; việc restart agent
không sửa được Redis. Sau 30 giây Redis hồi phục, các agent còn phải
khởi động lại và vượt probe trước khi nhận traffic.

Với hai endpoint riêng, `/health` vẫn 200 còn `/ready` trả 503 khi Redis
lỗi. Load balancer có thể rút traffic mà không restart process đang sống;
khi Redis hồi phục, `/ready` trở lại 200. Test CP4 đã kiểm chứng cặp trạng
thái này. Việc có restart thật hay không phụ thuộc orchestrator và ngưỡng
probe; riêng Docker Compose healthcheck chỉ đánh dấu unhealthy, không
tự restart container chỉ vì probe lỗi.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Ở lần thử CP4, mình chạy ba agent bằng file override trong
`CP4_SCALING.md`, rồi gọi lần lượt từng replica với cùng một user mới.
`history_length` nhận được là 0, 2, 4. Trường này đếm message trước lượt
gọi hiện tại, và mỗi lượt thêm hai message user/assistant vào Redis.
History có TTL 604800 giây và chỉ giữ 20 message gần nhất.

Nếu mỗi process dùng dict riêng, vòng đầu qua ba replica có thể là
0, 0, 0; vòng tiếp theo là 2, 2, 2. Nếu phân phối traffic không đều, số
message có thể giảm khi chuyển sang replica ít nhận request hơn. Restart
một process cũng làm mất dict của riêng nó. Redis dùng chung giúp lịch
sử nhất quán qua các replica khi mình gọi tuần tự, và giữ dữ liệu qua
restart của agent.

Mình cần override vì map cố định `8000:8000` không thể dùng đồng thời cho
ba container. Mỗi replica được cấp một cổng host riêng; sau khi thử mình
trả stack về một agent ở cổng 8000. Render Key Value Free không có disk
persistence, nên restart chính Redis vẫn có thể mất state.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Sau khi CI deploy lên Render ngày 29/09/2026, lần kiểm tra URL thật bằng
`pytest tests/test_cp5.py -v` có lỗi
`httpx.ConnectError: [Errno 11001] getaddrinfo failed` ở `/health`,
`/ready` và `/ask`. Đây là lỗi gặp khi xác minh bản cloud, không phải
một lỗi build của Render.

Mình đối chiếu Render: deploy `dep-datjtc893c1s73atofag` đã `live` và đúng
commit `c56d4fd`. Sau đó dùng `Resolve-DnsName` để kiểm tra tên miền và
`curl -i https://day12-agent-6lg4.onrender.com/health` để gọi trực tiếp.
DNS phân giải được và curl trả 200 với `status: ok`, nên lỗi quan sát
được nằm ở bước phân giải tên miền/kết nối từ máy kiểm tra, chưa có bằng
chứng Redis hay startup của service bị lỗi.

Mình kiểm tra lại kết nối rồi chạy lại test, không sửa `REDIS_URL` hay
secret khi chưa có bằng chứng chúng sai. Kết quả là 9 passed, 4 skipped:
health/readiness đều 200, thiếu key trả 401 và có `DEPLOY_API_KEY` trả 200.
Lần chạy toàn bộ test sau đó đạt 97 passed, 4 skipped. Bài học của mình
là phân biệt lỗi build/runtime trên cloud với lỗi DNS của máy gọi trước
khi thay cấu hình service.
